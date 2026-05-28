import os
import logging
from datetime import datetime, timedelta, timezone
import boto3
from botocore.exceptions import ClientError

# Initialize loggers and clients
logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2 = boto3.client('ec2')
cloudwatch = boto3.client('cloudwatch')
sns = boto3.client('sns')

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')

def get_instance_name(instance):
    """Extracts the 'Name' tag from an EC2 instance if it exists."""
    for tag in instance.get('Tags', []):
        if tag['Key'] == 'Name':
            return tag['Value']
    return "Unnamed"

def get_idle_instances():
    """Identifies running EC2 instances with average CPU < 5% over 7 days."""
    idle_instances = []
    paginator = ec2.get_paginator('describe_instances')
    
    try:
        page_iterator = paginator.paginate(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        
        for page in page_iterator:
            for reservation in page['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    name = get_instance_name(instance)
                    
                    # Fetch metrics safely using timezone-aware datetimes
                    metrics = cloudwatch.get_metric_statistics(
                        Namespace='AWS/EC2',
                        MetricName='CPUUtilization',
                        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                        StartTime=datetime.now(timezone.utc) - timedelta(days=7),
                        EndTime=datetime.now(timezone.utc),
                        Period=86400,  # 1-day intervals
                        Statistics=['Average']
                    )
                    
                    datapoints = metrics.get('Datapoints', [])
                    if datapoints:
                        avg_cpu = sum(d['Average'] for d in datapoints) / len(datapoints)
                        if avg_cpu < 5:
                            idle_instances.append(f"{instance_id} ({name}) - Avg CPU: {avg_cpu:.2f}%")
                            
    except ClientError as e:
        logger.error(f"Error fetching EC2 instances or metrics: {e}")
        
    return idle_instances

def get_unused_volumes():
    """Identifies EBS volumes that are not attached to any instance."""
    unused_volumes = []
    paginator = ec2.get_paginator('describe_volumes')
    
    try:
        page_iterator = paginator.paginate(
            Filters=[{'Name': 'status', 'Values': ['available']}]
        )
        for page in page_iterator:
            for volume in page['Volumes']:
                vol_id = volume['VolumeId']
                vol_size = volume['Size']
                unused_volumes.append(f"{vol_id} ({vol_size} GiB)")
    except ClientError as e:
        logger.error(f"Error fetching EBS volumes: {e}")
        
    return unused_volumes

def lambda_handler(event, context):
    if not SNS_TOPIC_ARN:
        logger.error("SNS_TOPIC_ARN environment variable is missing.")
        return {'statusCode': 500, 'body': 'Configuration error.'}

    idle_instances = get_idle_instances()
    unused_volumes = get_unused_volumes()
    
    # Generate human-readable report
    report_lines = ["AWS Cost Optimization Report", "========================="]
    
    report_lines.append("\nIdle EC2 Instances (Last 7 Days < 5% CPU):")
    if idle_instances:
        report_lines.extend([f"- {inst}" for inst in idle_instances])
    else:
        report_lines.append("- None found.")
        
    report_lines.append("\nUnused EBS Volumes (Status: available):")
    if unused_volumes:
        report_lines.extend([f"- {vol}" for vol in unused_volumes])
    else:
        report_lines.append("- None found.")
        
    message = "\n".join(report_lines)
    
    # Send Notification
    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject='AWS Cost Optimization Report',
            Message=message
        )
    except ClientError as e:
        logger.error(f"Failed to send SNS message: {e}")
        return {'statusCode': 500, 'body': 'Failed to send notification.'}

    return {
        'statusCode': 200,
        'body': 'Report sent successfully.'
    }
