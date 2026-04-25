import boto3
import logging
from botocore.exceptions import ClientError

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2 = boto3.client('ec2')


def get_all_snapshots():
    """Fetch all EBS snapshots owned by the account (with pagination)."""
    snapshots = []
    paginator = ec2.get_paginator('describe_snapshots')

    for page in paginator.paginate(OwnerIds=['self']):
        snapshots.extend(page['Snapshots'])

    return snapshots


def get_active_volume_ids():
    """
    Get volume IDs that are attached to any EC2 instance
    (running, stopped, etc.)
    """
    volume_ids = set()
    paginator = ec2.get_paginator('describe_volumes')

    for page in paginator.paginate():
        for volume in page['Volumes']:
            if volume['Attachments']:
                volume_ids.add(volume['VolumeId'])

    return volume_ids


def delete_snapshot(snapshot_id):
    """Delete snapshot safely with logging."""
    try:
        ec2.delete_snapshot(SnapshotId=snapshot_id)
        logger.info(f"Deleted snapshot: {snapshot_id}")
    except ClientError as e:
        logger.error(f"Error deleting snapshot {snapshot_id}: {str(e)}")


def lambda_handler(event, context):
    logger.info("Starting EBS snapshot cleanup process")

    snapshots = get_all_snapshots()
    active_volumes = get_active_volume_ids()

    deleted_count = 0
    skipped_count = 0

    for snapshot in snapshots:
        snapshot_id = snapshot['SnapshotId']
        volume_id = snapshot.get('VolumeId')

        # Skip snapshots with specific tag (safety)
        tags = {tag['Key']: tag['Value'] for tag in snapshot.get('Tags', [])}
        if tags.get('Keep', 'false').lower() == 'true':
            logger.info(f"Skipping snapshot {snapshot_id} (Keep=true)")
            skipped_count += 1
            continue

        if not volume_id:
            logger.info(f"Deleting snapshot {snapshot_id} (no volume)")
            delete_snapshot(snapshot_id)
            deleted_count += 1
            continue

        if volume_id not in active_volumes:
            logger.info(f"Deleting snapshot {snapshot_id} (volume not in use)")
            delete_snapshot(snapshot_id)
            deleted_count += 1
        else:
            logger.info(f"Skipping snapshot {snapshot_id} (volume still in use)")
            skipped_count += 1

    logger.info(f"Cleanup completed. Deleted: {deleted_count}, Skipped: {skipped_count}")

    return {
        "status": "completed",
        "deleted": deleted_count,
        "skipped": skipped_count
    }