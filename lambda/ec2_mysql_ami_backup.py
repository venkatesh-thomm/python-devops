import boto3
import datetime
import logging
import os
from botocore.exceptions import ClientError

# Logging setup
logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2 = boto3.client('ec2')

# Environment variables (configure in Lambda)
TAG_NAME = os.getenv('INSTANCE_TAG_NAME', 'dev-mysql')
RETENTION_DAYS = int(os.getenv('RETENTION_DAYS', '7'))
TEAM_TAG = os.getenv('TEAM_TAG', 'DevOps')


def get_instance_ids():
    """Fetch EC2 instance IDs based on Name tag (with pagination)"""
    instance_ids = []
    paginator = ec2.get_paginator('describe_instances')

    try:
        for page in paginator.paginate(
            Filters=[{'Name': 'tag:Name', 'Values': [TAG_NAME]}]
        ):
            for reservation in page['Reservations']:
                for instance in reservation['Instances']:
                    instance_ids.append(instance['InstanceId'])

        return instance_ids

    except ClientError as e:
        logger.error(f"Error fetching instances: {str(e)}")
        return []


def get_instance_name(instance_id):
    """Fetch Name tag of instance"""
    try:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        tags = response['Reservations'][0]['Instances'][0].get('Tags', [])

        return next((t['Value'] for t in tags if t['Key'] == 'Name'), instance_id)

    except Exception:
        return instance_id


def create_ami(instance_id):
    """Create AMI backup"""
    try:
        name = get_instance_name(instance_id)
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d-%H%M%S')

        ami_name = f'backup-{name}-{timestamp}'

        response = ec2.create_image(
            InstanceId=instance_id,
            Name=ami_name,
            Description=f'Backup of {name} ({instance_id})',
            NoReboot=True
        )

        ami_id = response['ImageId']

        # Tag AMI
        ec2.create_tags(
            Resources=[ami_id],
            Tags=[
                {'Key': 'Name', 'Value': ami_name},
                {'Key': 'CreatedBy', 'Value': 'Lambda'},
                {'Key': 'Team', 'Value': TEAM_TAG},
                {'Key': 'Retention', 'Value': str(RETENTION_DAYS)}
            ]
        )

        logger.info(f"AMI created: {ami_id}")
        return ami_id

    except ClientError as e:
        logger.error(f"Error creating AMI for {instance_id}: {str(e)}")
        return None


def cleanup_old_amis():
    """Delete AMIs older than retention period"""
    cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=RETENTION_DAYS)

    try:
        images = ec2.describe_images(Owners=['self'])['Images']

        for image in images:
            creation_date = datetime.datetime.strptime(
                image['CreationDate'], "%Y-%m-%dT%H:%M:%S.%fZ"
            )

            if creation_date < cutoff_date:
                ami_id = image['ImageId']

                # Deregister AMI
                ec2.deregister_image(ImageId=ami_id)
                logger.info(f"Deregistered AMI: {ami_id}")

                # Delete associated snapshots
                for block in image.get('BlockDeviceMappings', []):
                    if 'Ebs' in block:
                        snapshot_id = block['Ebs']['SnapshotId']
                        ec2.delete_snapshot(SnapshotId=snapshot_id)
                        logger.info(f"Deleted snapshot: {snapshot_id}")

    except ClientError as e:
        logger.error(f"Error during cleanup: {str(e)}")


def lambda_handler(event, context):
    logger.info("Starting EC2 backup process")

    instance_ids = get_instance_ids()

    if not instance_ids:
        logger.warning("No instances found")
        return {"status": "No instances"}

    ami_list = []

    for instance_id in instance_ids:
        logger.info(f"Backing up: {instance_id}")
        ami_id = create_ami(instance_id)
        if ami_id:
            ami_list.append(ami_id)

    # Cleanup old AMIs
    cleanup_old_amis()

    logger.info(f"Backup completed: {ami_list}")

    return {
        "status": "success",
        "amis": ami_list
    }