# CloudWatch Event Rules for scheduling EC2 stop instances at 8 AM on weekdays
resource "aws_cloudwatch_event_rule" "ec2_auto_stop_rule" {
  name                = "ec2-auto-stop-weekdays-1600-ist"
  description         = "Triggers EC2 auto-stop at 4:00 PM IST on weekdays"
  schedule_expression = "cron(30 10 ? * SUN,MON-FRI *)" # 4:00 PM IST UTC, Monday to Friday
}

# CloudWatch Event Rule for scheduling EC2 start instances at 8 AM on weekdays
resource "aws_cloudwatch_event_rule" "ec2_auto_start_rule" {
  name                = "ec2-auto-start-weekdays-1600-ist"
  description         = "Triggers EC2 auto-start at 4:00 PM IST on weekdays"
  schedule_expression = "cron(30 10 ? * MON-FRI *)" # 4:00 PM IST UTC, Monday to Friday
}

# Target for EC2 Auto Stop Lambda
resource "aws_cloudwatch_event_target" "ec2_auto_stop_target" {
  rule      = aws_cloudwatch_event_rule.ec2_auto_stop_rule.name
  target_id = "EC2AutoStopLambda"
  arn       = aws_lambda_function.ec2_auto_stop.arn
}

#Target for EC2 Auto Start Lambda
resource "aws_cloudwatch_event_target" "ec2_auto_start_target" {
  rule      = aws_cloudwatch_event_rule.ec2_auto_start_rule.name
  target_id = "EC2AutoStartLambda"
  arn       = aws_lambda_function.ec2_auto_start.arn
}


# Permissions for CloudWatch to invoke EC2 Auto Stop Lambda
resource "aws_lambda_permission" "allow_cloudwatch_to_call_ec2_auto_stop" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ec2_auto_stop.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ec2_auto_stop_rule.arn
}


# Permissions for CloudWatch to invoke EC2 Auto Start Lambda
resource "aws_lambda_permission" "allow_cloudwatch_to_call_ec2_auto_start" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ec2_auto_start.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ec2_auto_start_rule.arn
}
