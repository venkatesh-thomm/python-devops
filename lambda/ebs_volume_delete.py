import boto3
from datetime import datetime, timezone

REGION = "us-east-1"
DRY_RUN = False   # Set True to test without deleting
MIN_AGE_HOURS = 24  # Delete only if older than 24 hours

def lambda_handler(event, context):
    ec2_client = boto3.client("ec2", region_name=REGION)
    ec2_resource = boto3.resource("ec2", region_name=REGION)

    unattached_volumes = []

    paginator = ec2_client.get_paginator('describe_volumes')

    for page in paginator.paginate():
        for vol in page.get("Volumes", []):

            vol_id = vol["VolumeId"]
            state = vol["State"]
            vol_type = vol["VolumeType"]
            create_time = vol["CreateTime"]

            # ✅ Condition 1: Only gp3 volumes
            if vol_type != "gp3":
                continue

            # ✅ Condition 2: Only unattached volumes
            if state != "available":
                continue

            # ✅ Condition 3: Age check
            age_hours = (datetime.now(timezone.utc) - create_time).total_seconds() / 3600
            if age_hours < MIN_AGE_HOURS:
                print(f"Skipping {vol_id} (too new: {age_hours:.2f} hrs)")
                continue

            # ✅ Condition 4: Tag protection
            tags = {tag['Key']: tag['Value'] for tag in vol.get('Tags', [])}
            if tags.get("Keep", "").lower() == "true":
                print(f"Skipping protected volume {vol_id}")
                continue

            print(f"Volume {vol_id} (gp3) is eligible for deletion")
            unattached_volumes.append(vol_id)

    print(f"Final volumes to delete: {unattached_volumes}")

    # 🔥 Deletion step
    for vol_id in unattached_volumes:
        try:
            if DRY_RUN:
                print(f"[DRY RUN] Would delete {vol_id}")
            else:
                volume = ec2_resource.Volume(vol_id)
                volume.delete()
                print(f"Deleted volume {vol_id}")
        except Exception as e:
            print(f"Error deleting {vol_id}: {str(e)}")