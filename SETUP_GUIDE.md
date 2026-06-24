# AWS Serverless Job Application Portal - Setup Guide

## Architecture Overview

```
[S3 Static Website] → [API Gateway] → [Lambda Function] → [DynamoDB]
        ↓                                      ↓
   (index.html)                          [S3 Resumes Bucket]
   (admin.html)
```

---

## Step 1: Create DynamoDB Table

1. Go to **AWS Console → DynamoDB → Create Table**
2. Settings:
   - Table name: `JobApplications`
   - Partition key: `applicationId` (String)
   - Leave sort key empty
   - Use default settings (On-demand capacity recommended for learning)
3. Click **Create Table**

---

## Step 2: Create S3 Bucket for Resumes

1. Go to **AWS Console → S3 → Create Bucket**
2. Settings:
   - Bucket name: `job-applications-resumes-YOURNAME` (must be globally unique)
   - Region: Same as your Lambda
   - Uncheck "Block all public access" (needed for presigned URLs to work)
   - Acknowledge the warning
3. Click **Create Bucket**

---

## Step 3: Create the Lambda Function

1. Go to **AWS Console → Lambda → Create Function**
2. Settings:
   - Function name: `JobApplicationsHandler`
   - Runtime: Python 3.12
   - Architecture: x86_64
   - Execution role: Create a new role with basic Lambda permissions
3. Click **Create Function**
4. In the code editor, paste the entire content of `lambda_function.py`
5. **Update the configuration** at the top of the file:
   - `DYNAMODB_TABLE_NAME = 'JobApplications'`
   - `S3_RESUME_BUCKET = 'job-applications-resumes-YOURNAME'`
6. Go to **Configuration → General** and set:
   - Timeout: 30 seconds
   - Memory: 256 MB
7. Click **Deploy**

### Lambda IAM Permissions

Add these permissions to your Lambda execution role:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:PutItem",
                "dynamodb:GetItem",
                "dynamodb:Scan",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem"
            ],
            "Resource": "arn:aws:dynamodb:YOUR-REGION:YOUR-ACCOUNT-ID:table/JobApplications"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::job-applications-resumes-YOURNAME/*"
        }
    ]
}
```

Go to **IAM → Roles → Your Lambda Role → Add inline policy** and paste the above JSON.

---

## Step 4: Create API Gateway

1. Go to **AWS Console → API Gateway → Create API**
2. Choose **REST API** → Build
3. Settings:
   - API name: `JobApplicationsAPI`
   - Endpoint type: Regional
4. Click **Create API**

### Create Resources and Methods:

**Resource: /applications**
1. Actions → Create Resource
   - Resource name: `applications`
   - Enable CORS: ✅ Yes
2. Select `/applications` → Actions → Create Method
   - Add **GET** method → Integration type: Lambda → Select your function
   - Add **POST** method → Integration type: Lambda → Select your function

**Resource: /applications/{id}**
1. Select `/applications` → Actions → Create Resource
   - Resource name: `{id}`
   - Resource path: `{id}`
   - Enable CORS: ✅ Yes
2. Select `/applications/{id}` → Actions → Create Method
   - Add **GET** method → Integration type: Lambda → Select your function
   - Add **PUT** method → Integration type: Lambda → Select your function
   - Add **DELETE** method → Integration type: Lambda → Select your function

### Enable CORS (for each resource):
1. Select resource → Actions → Enable CORS
2. Leave defaults → Click "Enable CORS and replace existing CORS headers"

### Deploy API:
1. Actions → Deploy API
2. Stage: Create new → Stage name: `prod`
3. Click **Deploy**
4. **Copy the Invoke URL** (looks like: `https://abc123.execute-api.us-east-1.amazonaws.com/prod`)

---

## Step 5: Update Frontend with API URL

In BOTH `index.html` and `admin.html`, find this line:

```javascript
const API_BASE_URL = 'https://YOUR-API-GATEWAY-ID.execute-api.YOUR-REGION.amazonaws.com/prod';
```

Replace it with your actual API Gateway invoke URL from Step 4.

---

## Step 6: Host Frontend on S3

1. Go to **AWS Console → S3 → Create Bucket**
2. Settings:
   - Bucket name: `job-portal-frontend-YOURNAME` (must be globally unique)
   - Region: Any
   - **Uncheck** "Block all public access"
   - Acknowledge the warning
3. Click **Create Bucket**

### Enable Static Website Hosting:
1. Go to bucket → **Properties** tab
2. Scroll to "Static website hosting" → Edit
3. Enable it
   - Index document: `index.html`
4. Save

### Set Bucket Policy (Public Read):
1. Go to **Permissions** tab → Bucket Policy → Edit
2. Paste:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::job-portal-frontend-YOURNAME/*"
        }
    ]
}
```

### Upload Files:
1. Upload `index.html` and `admin.html` to the bucket
2. Your website URL will be:
   `http://job-portal-frontend-YOURNAME.s3-website-REGION.amazonaws.com`

---

## How It All Works Together

1. **User visits S3 website URL** → Sees the job application form
2. **User fills form + uploads resume** → Frontend sends POST to API Gateway
3. **API Gateway** → Routes request to Lambda function
4. **Lambda function**:
   - Decodes the base64 resume file
   - Uploads resume to S3 resume bucket
   - Saves application data to DynamoDB
   - Returns success response
5. **Admin clicks Admin Panel button** → Redirects to admin.html
6. **Admin page loads** → Fetches all applications via GET from API Gateway
7. **Admin can Edit/Delete** → Sends PUT/DELETE to API Gateway → Lambda updates/deletes from DynamoDB

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| CORS errors in browser | Make sure CORS is enabled on API Gateway for all methods |
| 403 on API calls | Check Lambda has proper IAM permissions |
| Resume upload fails | Increase Lambda timeout to 30s and memory to 256MB |
| Empty table in admin | Verify the API URL is correct in both HTML files |
| S3 website not loading | Check bucket policy allows public read |

---

## Cost Estimate (Free Tier)

- **Lambda**: 1M free requests/month
- **DynamoDB**: 25 GB storage + 25 read/write capacity units free
- **S3**: 5 GB storage + 20,000 GET requests free
- **API Gateway**: 1M API calls free for 12 months

This project will run essentially free under AWS Free Tier for learning purposes.
