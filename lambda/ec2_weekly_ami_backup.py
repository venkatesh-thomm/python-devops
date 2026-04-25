import boto3
import datetime
import logging
import os
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2 = boto3.client('ec2')

# Config (move to env vars in Lambda ideally)
INSTANCE_TAG_NAME = os.getenv('INSTANCE_TAG_NAME', 'dev-mysql')
RETENTION_DAYS = int(os.getenv('RETENTION_DAYS', '7'))
RETENTION_HOURS = int(os.getenv('RETENTION_HOURS', '0'))


def get_instance_ids():
    """Fetch instances with pagination"""
    instance_ids = []
    paginator = ec2.get_paginator('describe_instances')

    try:
        for page in paginator.paginate(
            Filters=[
                {'Name': 'tag:Name', 'Values': [INSTANCE_TAG_NAME]},
                {'Name': 'instance-state-name', 'Values': ['running']}
            ]
        ):
            for res in page['Reservations']:
                for inst in res['Instances']:
                    instance_ids.append(inst['InstanceId'])

        return instance_ids

    except ClientError as e:
        logger.error(f"AWS error fetching instances: {e}")
        return []


def create_backup(instance_id):
    """Create AMI"""
    try:
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d-%H%M%S')
        ami_name = f'backup-{instance_id}-{timestamp}'

        response = ec2.create_image(
            InstanceId=instance_id,
            Name=ami_name,
            NoReboot=True
        )

        ami_id = response['ImageId']

        ec2.create_tags(
            Resources=[ami_id],
            Tags=[
                {'Key': 'CreatedBy', 'Value': 'LambdaBackup'},
                {'Key': 'InstanceId', 'Value': instance_id},
                {'Key': 'CreatedAt', 'Value': timestamp}
            ]
        )

        logger.info(f"Created AMI: {ami_id}")
        return ami_id

    except ClientError as e:
        logger.error(f"Error creating AMI for {instance_id}: {e}")
        return None


def get_cutoff_time():
    """Dynamic retention logic"""
    delta = datetime.timedelta(days=RETENTION_DAYS, hours=RETENTION_HOURS)
    return datetime.datetime.utcnow() - delta


def cleanup_old_amis():
    """Delete only relevant AMIs safely"""
    cutoff = get_cutoff_time()
    paginator = ec2.get_paginator('describe_images')

    try:
        for page in paginator.paginate(
            Owners=['self'],
            Filters=[
                {'Name': 'tag:CreatedBy', 'Values': ['LambdaBackup']},
                {'Name': 'tag:InstanceId', 'Values': ['*']}  # ensures controlled scope
            ]
        ):
            for image in page['Images']:
                creation_date = datetime.datetime.strptime(
                    image['CreationDate'], "%Y-%m-%dT%H:%M:%S.%fZ"
                )

                if creation_date >= cutoff:
                    continue

                ami_id = image['ImageId']
                logger.info(f"Deleting AMI: {ami_id}")

                try:
                    ec2.deregister_image(ImageId=ami_id)

                    for mapping in image.get('BlockDeviceMappings', []):
                        if 'Ebs' in mapping:
                            snapshot_id = mapping['Ebs']['SnapshotId']
                            try:
                                ec2.delete_snapshot(SnapshotId=snapshot_id)
                                logger.info(f"Deleted snapshot: {snapshot_id}")
                            except ClientError as e:
                                logger.warning(f"Snapshot delete failed {snapshot_id}: {e}")

                except ClientError as e:
                    logger.error(f"AMI delete failed {ami_id}: {e}")

    except ClientError as e:
        logger.error(f"Cleanup error: {e}")


def lambda_handler(event, context):
    logger.info("Starting backup job")

    instance_ids = get_instance_ids()

    if not instance_ids:
        logger.warning("No instances found")
        return {"status": "no instances"}

    created = []

    for instance_id in instance_ids:
        ami_id = create_backup(instance_id)
        if ami_id:
            created.append(ami_id)

    cleanup_old_amis()

    return {
        "status": "success",
        "created_amis": created
    }