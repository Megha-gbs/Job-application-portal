# AWS Serverless Job Application Portal

A fully serverless job application management system built using AWS services including Lambda, API Gateway, DynamoDB, and S3.

## Overview

This project allows job applicants to submit applications and upload resumes through a web interface. Administrators can view, edit, and delete applications through a dedicated admin dashboard.

The solution is built using a serverless architecture, eliminating the need to manage servers while providing scalability, reliability, and cost efficiency.

---

## Architecture

```text
┌─────────────────────┐
│   S3 Static Website │
│ (index.html/admin)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│    API Gateway      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   AWS Lambda        │
└──────┬───────┬──────┘
       │       │
       ▼       ▼
┌──────────┐ ┌──────────┐
│ DynamoDB │ │    S3    │
│Applications│ Resumes  │
└──────────┘ └──────────┘
```

---

## Features

### Applicant Portal

- Submit job applications
- Upload resumes
- Form validation
- Responsive user interface

### Admin Dashboard

- View all applications
- Edit application details
- Delete applications
- Real-time data retrieval

### AWS Services

- AWS Lambda
- Amazon API Gateway
- Amazon DynamoDB
- Amazon S3
- IAM Roles and Policies

---

## Tech Stack

| Technology | Purpose |
|------------|---------|
| HTML | Frontend Structure |
| CSS | Styling |
| JavaScript | Client-side Logic |
| AWS Lambda | Backend Processing |
| API Gateway | REST API |
| DynamoDB | Data Storage |
| S3 | Resume Storage & Website Hosting |

---

## Project Structure

```text
aws-job-application-project/

├── index.html
├── admin.html
├── lambda_function.py
├── README.md

```

---

## AWS Resources

### DynamoDB

**Table Name**

```text
JobApplications
```

**Partition Key**

```text
applicationId
```

### Resume Bucket

```text
job-applications-resumes-YOURNAME
```

### Lambda Function

```text
JobApplicationsHandler
```

Runtime:

```text
Python 3.12
```

### API Gateway

Resources:

```text
/applications
/applications/{id}
```

Methods:

```text
GET
POST
PUT
DELETE
```

---

## Deployment Steps

### 1. Create DynamoDB Table

Create a DynamoDB table named:

```text
JobApplications
```

Partition Key:

```text
applicationId
```

---

### 2. Create Resume Storage Bucket

Create an S3 bucket:

```text
job-applications-resumes-YOURNAME
```

---

### 3. Deploy Lambda Function

Upload:

```text
lambda_function.py
```

Update configuration:

```python
DYNAMODB_TABLE_NAME = "JobApplications"
S3_RESUME_BUCKET = "job-applications-resumes-YOURNAME"
```

Deploy the function.

---

### 4. Configure API Gateway

Create:

```text
/applications
/applications/{id}
```

Add methods:

```text
GET
POST
PUT
DELETE
```

Connect all methods to Lambda.

Enable CORS.

Deploy API to:

```text
prod
```

---

### 5. Update Frontend

Replace:

```javascript
const API_BASE_URL = "YOUR_API_GATEWAY_URL";
```

with your deployed API URL.

---

### 6. Host Frontend

Create an S3 bucket for website hosting.

Upload:

```text
index.html
admin.html
```

Enable Static Website Hosting.

---

## IAM Permissions

### DynamoDB

```json
{
  "Effect": "Allow",
  "Action": [
    "dynamodb:PutItem",
    "dynamodb:GetItem",
    "dynamodb:Scan",
    "dynamodb:UpdateItem",
    "dynamodb:DeleteItem"
  ]
}
```

### Amazon S3

```json
{
  "Effect": "Allow",
  "Action": [
    "s3:PutObject",
    "s3:GetObject",
    "s3:DeleteObject"
  ]
}
```

---

## Application Workflow

1. User opens the website hosted on S3.
2. User fills out the job application form.
3. Resume is uploaded to Amazon S3.
4. Application details are stored in DynamoDB.
5. API Gateway routes requests to Lambda.
6. Lambda processes all CRUD operations.
7. Admin dashboard retrieves applications from DynamoDB.

---

## Cost Estimate

Under AWS Free Tier:

| Service | Free Tier |
|----------|-----------|
| Lambda | 1M Requests |
| API Gateway | 1M Requests |
| DynamoDB | 25 GB Storage |
| S3 | 5 GB Storage |

Expected cost for learning and demo usage:

```text
$0 - $1/month
```

---

## Learning Outcomes

This project demonstrates:

- Serverless Architecture
- AWS Lambda Development
- API Gateway Integration
- DynamoDB CRUD Operations
- S3 File Upload Handling
- IAM Permissions Management
- Static Website Hosting
- Cloud Application Deployment

---

## Future Enhancements

- Amazon Cognito Authentication
- Resume Parsing with Textract
- Email Notifications with SES
- CloudFront CDN Integration
- CI/CD Pipeline with GitHub Actions
- Infrastructure as Code using Terraform

---

## Author

Developed as a cloud-native serverless project on AWS.

If you found this project useful, consider giving the repository a ⭐.