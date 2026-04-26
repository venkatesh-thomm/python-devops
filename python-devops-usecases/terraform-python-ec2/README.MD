# 🛠️ DevOps Automation with Python

---
## what is lambda
👉 AWS Lambda = run your code without managing servers, and you pay only when it runs [it's Event driven].

 ⏱️ How long does it run?
  Minimum: a few milliseconds
  Maximum: 15 minutes (900 seconds) per execution

## 📌 Use Cases 
### Schedule Cron Job to Start/Stop EC2 Instances

Use **AWS Lambda + EventBridge (Cron)** to automate instance management.

#### Example Lambda (Start EC2)

```python
import boto3

ec2 = boto3.client('ec2')

def lambda_handler(event, context):
    ec2.start_instances(InstanceIds=['i-xxxxxxxx'])
    print("EC2 Started")
```

#### Example Lambda (Stop EC2)

```python
import boto3

ec2 = boto3.client('ec2')

def lambda_handler(event, context):
    ec2.stop_instances(InstanceIds=['i-xxxxxxxx'])
    print("EC2 Stopped")
```

#### Cron Expression (EventBridge)

```
cron(0 9 * * ? *)  # Start at 9 AM daily
cron(0 19 * * ? *) # Stop at 7 PM daily
```

---

## 🐍 Python Virtual Environment Setup

### 🔹 Create Virtual Environment

```bash
python -m venv devops
```

### 🔹 Activate Virtual Environment

```bash
source ./devops/Scripts/activate   # Windows Git Bash
# or
.\devops\Scripts\activate         # Windows CMD
# or
source devops/bin/activate        # Linux/Mac
```

### 🔹 Install a Package

```bash
pip install <package-name>
```

### 🔹 Uninstall a Package

```bash
pip uninstall <package-name>
```

### 🔹 List Installed Packages

```bash
pip list --format=freeze
```

---

## 📦 Requirements Management

### 🔹 Generate requirements.txt

```bash
pip freeze > requirements.txt
```

### 🔹 Install from requirements.txt

```bash
pip install -r requirements.txt
```

---

## 🧠 Python Concepts

* **Package** → Collection of libraries
* **Library** → Collection of modules
* **Module** → Collection of functions

---

## 🐞 Debugging in Python

Use built-in debugger:

```python
import pdb; pdb.set_trace()
```

---

## ☁️ Fetch Logs from CloudWatch

```python
import boto3

client = boto3.client('logs')

response = client.filter_log_events(
    logGroupName='your-log-group'
)

with open("logs.txt", "w") as f:
    for event in response['events']:
        f.write(event['message'] + "\n")
```

---

## 🚀 Deploy Python Script to AWS Lambda

Steps:

1. Write your Python script
2. Zip the file
3. Upload to Lambda
4. Attach IAM Role (EC2 permissions)
5. Add EventBridge trigger (cron)

---


## 🔐 Prerequisites

* Python 3.x
* AWS CLI configured
* GitHub Personal Access Token
* Required permissions for EC2 and CloudWatch

---

## 💡 Notes

* Never hardcode credentials → use environment variables
* Use IAM roles instead of access keys in AWS
* Automate everything wherever possible

---

## 📚 References

* AWS Lambda Documentation
* GitHub REST API Docs
* Boto3 Documentation

---




