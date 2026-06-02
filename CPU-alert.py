import os
import logging
import json
import boto3
from botocore.exceptions import ClientError
import urllib3 # Standard library alternative to 'requests' for Lambda/light scripts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "https://slack.com")

def lambda_handler(event, context):
    """
    Triggered by a CloudWatch High CPU Alert.
    Expects instance details in the event payload.
    """
    # 1. Extract context from the alert payload
    instance_id = event.get("detail", {}).get("instance-id", "i-0123456789abcdef0")
    
    # 2. Initialize AWS client using IAM Role permissions (no hardcoded keys)
    ec2_client = boto3.client('ec2', region_name='us-east-1')
    
    try:
        logger.info(f"Targeting stressed instance: {instance_id}")
        
        # 3. Automation Action: Create a snapshot of the root volume for debugging
        # First, find the root volume ID
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        volume_id = response['Reservations'][0]['Instances'][0]['BlockDeviceMappings'][0]['Ebs']['VolumeId']
        
        snapshot = ec2_client.create_snapshot(
            VolumeId=volume_id,
            Description=f"Automated snapshot due to High CPU alert on {instance_id}"
        )
        snapshot_id = snapshot['SnapshotId']
        logger.info(f"Snapshot created successfully: {snapshot_id}")
        
        # 4. Notify the team over Slack
        send_slack_notification(instance_id, f"Success - Snapshot {snapshot_id} captured.")
        
    except ClientError as ce:
        error_msg = ce.response['Error']['Message']
        logger.error(f"AWS API Error: {error_msg}")
        send_slack_notification(instance_id, f"Failed - AWS API Error: {error_msg}")
    except Exception as e:
        logger.error(f"General script error: {str(e)}")
        send_slack_notification(instance_id, f"Failed - Script Exception: {str(e)}")

def send_slack_notification(instance_id, status_message):
    """Helper function to send standard HTTP POST requests without external dependencies"""
    http = urllib3.PoolManager()
    payload = {
        "text": f"🚨 *Automation Alert*: High CPU Mitigation on `{instance_id}`\n*Status*: {status_message}"
    }
    try:
        http.request(
            'POST',
            SLACK_WEBHOOK_URL,
            body=json.dumps(payload),
            headers={'Content-Type': 'application/json'},
            timeout=5.0
        )
    except Exception as e:
        logger.error(f"Failed to push alert to Slack: {e}")
