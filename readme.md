# 🚀 Python DevOps Usecases

This repository contains a collection of **real-world DevOps automation scripts** built using **Python, AWS (Lambda, EC2, EBS), and Terraform**.

The goal of this project is to demonstrate **practical automation use cases** such as:

* Cost optimization
* Backup automation
* Infrastructure provisioning
* API integrations

---

## 📂 Project Structure

```
python-devops-usecases/
│
├── github-api/              # GitHub API automation scripts
├── lambda/                  # AWS Lambda automation scripts
├── terraform-python-ec2/    # Terraform IaC setup
```

---

## 🛠️ Modules Overview

### 🔹 1. GitHub Automation (`github-api/`)

Automates repository management using GitHub REST API.

#### Scripts:

* `create_repo.py` → Create repositories programmatically
* `list_repos.py` → List repositories in a user/org account

#### 🎯 Use Cases:

* Bulk repo creation
* Auditing repositories
* Automating onboarding workflows

---

### 🔹 2. AWS Lambda Automation (`lambda/`)

Production-style automation scripts for AWS resource management.

---

#### 📌 a) EBS Snapshot Cleanup

**File:** `ebs_orphan_snapshot_cleanup.py`

##### ✅ What it does:

* Fetches all EBS snapshots owned by the account
* Identifies:

  * Orphan snapshots (no volume)
  * Snapshots of deleted volumes
  * Snapshots from unused volumes
* Deletes unnecessary snapshots

##### 💡 Why it matters:

* Prevents **storage cost leakage**
* Keeps AWS environment clean

---

#### 📌 b) EC2 AMI Backup (Basic)

**File:** `ec2_backup_basic.py`

##### ✅ What it does:

* Finds EC2 instances with:

  ```
  Name = dev-mysql
  ```
* Creates AMI backups
* Tags AMIs for identification

##### 💡 Why it matters:

* Simple backup automation
* Useful for dev/test environments

---

#### 📌 c) EC2 AMI Backup + Retention (Advanced)

**File:** `ec2_backup_with_retention.py`

##### ✅ What it does:

* Creates AMIs for tagged instances
* Applies metadata tags:

  * CreatedBy
  * InstanceId
  * Timestamp
* Deletes AMIs older than retention period
* Deletes associated EBS snapshots

##### 💡 Why it matters:

* Avoids **manual backup management**
* Reduces **AWS storage cost**
* Implements **lifecycle policy via code**

---

### 🔹 3. Terraform Infrastructure (`terraform-python-ec2/`)

Infrastructure-as-Code to deploy and automate the entire setup.

#### Includes:

* EC2 provisioning
* Lambda deployment
* IAM roles & permissions
* Security Groups (`sg.tf`)
* EventBridge scheduling (`event_bridge.tf`)

---

## ⚙️ Prerequisites

* Python 3.x
* Terraform
* AWS CLI configured
* GitHub Personal Access Token (for GitHub scripts)

---

## 🚀 Getting Started

### 1️⃣ Clone Repository

```bash
git clone https://github.com/venkatesh-thomm/python-devops.git
cd python-devops/python-devops-usecases
```

### 2️⃣ Install Dependencies

```bash
pip install -r github-api/requirements.txt
```

---

## ☁️ Deploy AWS Infrastructure

```bash
cd terraform-python-ec2
terraform init
terraform plan
terraform apply
```

---

## ⏰ Scheduling Automation

Using **EventBridge**, you can schedule:

* 🗓 Daily → EC2 backups
* 📅 Weekly → Snapshot cleanup

---

## 🔐 Required IAM Permissions

Your Lambda role should include:

* `ec2:DescribeInstances`
* `ec2:DescribeImages`
* `ec2:DescribeSnapshots`
* `ec2:DescribeVolumes`
* `ec2:CreateImage`
* `ec2:CreateTags`
* `ec2:DeregisterImage`
* `ec2:DeleteSnapshot`

---

## ⚠️ Important Notes

* These scripts **permanently delete AWS resources**
* Always test in a **non-production environment**
* Use proper tagging strategy to avoid accidental deletions

---

## 💡 Best Practices Implemented

* ✅ Tag-based filtering (safe operations)
* ✅ Retention-based cleanup
* ✅ Logging with CloudWatch
* ✅ Pagination handling (scalable)
* ✅ Modular design

---

## 🔥 Alternative Approach

For enterprise environments, consider using:

👉 AWS managed backup services (instead of custom scripts)

---

## 📈 Benefits

* 💰 Cost Optimization
* ⚙️ Automation
* 🧹 Resource Cleanup
* 🔄 Backup Reliability

---

## 👨‍💻 Author

**Venkatesh Thommandru**
DevOps | AWS | Automation Enthusiast

---
