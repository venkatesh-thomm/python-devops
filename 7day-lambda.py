import boto3
import datetime
import logging

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2_client = boto3.client('ec2')

# Configuration
INSTANCE_TAG_NAME = 'dev-mysql'
RETENTION_DAYS = 7
RETENTION_HOURS = 1  


def get_instance_ids():
    """Fetch EC2 instances based on Name tag"""
    try:
        response = ec2_client.describe_instances(
            Filters=[
                {'Name': 'tag:Name', 'Values': [INSTANCE_TAG_NAME]},
                {'Name': 'instance-state-name', 'Values': ['running']}
            ]
        )

        instance_ids = [
            instance['InstanceId']
            for reservation in response['Reservations']
            for instance in reservation['Instances']
        ]

        return instance_ids

    except Exception as e:
        logger.error(f"Error fetching instances: {str(e)}")
        return []


def create_backup(instance_id):
    """Create AMI backup"""
    try:
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d-%H%M%S')
        ami_name = f'backup-{instance_id}-{timestamp}'

        response = ec2_client.create_image(
            InstanceId=instance_id,
            Name=ami_name,
            Description=f'Automated backup created on {timestamp}',
            NoReboot=True
        )

        ami_id = response['ImageId']

        # Tag AMI
        ec2_client.create_tags(
            Resources=[ami_id],
            Tags=[
                {'Key': 'CreatedBy', 'Value': 'LambdaBackup'},
                {'Key': 'Retention', 'Value': str(RETENTION_DAYS)}
            ]
        )

        logger.info(f"Created AMI: {ami_id}")
        return ami_id

    except Exception as e:
        logger.error(f"Error creating AMI: {str(e)}")
        return None


def cleanup_old_amis():
    """Delete AMIs older than retention period"""
    try:
        cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=RETENTION_DAYS)
        #cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(hours=RETENTION_HOURS)

        images = ec2_client.describe_images(
            Owners=['self'],
            Filters=[{'Name': 'tag:CreatedBy', 'Values': ['LambdaBackup']}]
        )['Images']

        for image in images:
            creation_date = datetime.datetime.strptime(
                image['CreationDate'], "%Y-%m-%dT%H:%M:%S.%fZ"
            )

            if creation_date < cutoff_date:
                ami_id = image['ImageId']
                logger.info(f"Deregistering AMI: {ami_id}")

                # Deregister AMI
                ec2_client.deregister_image(ImageId=ami_id)

                # Delete associated snapshots
                for mapping in image.get('BlockDeviceMappings', []):
                    if 'Ebs' in mapping:
                        snapshot_id = mapping['Ebs']['SnapshotId']
                        logger.info(f"Deleting snapshot: {snapshot_id}")
                        ec2_client.delete_snapshot(SnapshotId=snapshot_id)

    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")


def lambda_handler(event, context):
    """Lambda entry point"""
    instance_ids = get_instance_ids()

    if not instance_ids:
        logger.warning("No matching instances found.")
        return {"statusCode": 404, "body": "No matching instances found."}

    created_amis = []

    for instance_id in instance_ids:
        ami_id = create_backup(instance_id)
        if ami_id:
            created_amis.append(ami_id)

    cleanup_old_amis()

    return {
        "statusCode": 200,
        "body": f"Created AMIs: {', '.join(created_amis)}"
    }
