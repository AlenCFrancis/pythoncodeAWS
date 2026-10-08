# ICT Academy Kerala — AWS Cloud Deployment Project
## Deploying a Secure Flask Web Application on AWS
**Student Submission & Architecture Guide**

---

## 1. Project Overview & Architecture

### Target Architecture Diagram
```
                     Internet Users (Browser)
                                │
                                ▼ HTTP: 80
┌───────────────────────────────┼────────────────────────────────────────┐
│ VPC: 10.0.0.0/16              │                                        │
│                               ▼                                        │
│                      ┌─────────────────┐                               │
│                      │ Internet Gateway│                               │
│                      └────────┬────────┘                               │
│                               │                                        │
│ ┌─────────────────────────────┼──────────────────────────────────────┐ │
│ │ Public Subnet (10.0.1.0/24) │                                      │ │
│ │                             ▼                                      │ │
│ │                 ┌───────────────────────┐                          │ │
│ │                 │ EC2 Instance (Flask)  │                          │ │
│ │                 │ Security Group: web-sg│                          │ │
│ │                 │ IAM Role: ec2-s3-role │                          │ │
│ │                 └───────────┬───────────┘                          │ │
│ └─────────────────────────────┼──────────────────────────────────────┘ │
│                               │                                        │
│                               │ MySQL Port 3306                        │
│                               ▼ (Allowed ONLY from web-sg)             │
│ ┌────────────────────────────────────────────────────────────────────┐ │
│ │ Private Subnets (10.0.2.0/24 in AZ-a, 10.0.3.0/24 in AZ-b)         │ │
│ │                                                                    │ │
│ │                 ┌───────────────────────┐                          │ │
│ │                 │ RDS MySQL 8.0         │                          │ │
│ │                 │ Public Access: NO     │                          │ │
│ │                 │ Security Group: db-sg │                          │ │
│ │                 └───────────────────────┘                          │ │
│ └────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────┬────────────────────────────────┘
                                        │
                                        │ HTTPS (boto3 via IAM Role)
                                        ▼
                           ┌─────────────────────────┐
                           │ Amazon S3 Bucket        │
                           │ student-photos-*        │
                           │ Public Read for Objects │
                           │ Bucket Listing Blocked  │
                           └─────────────────────────┘
```

---

## 2. Completed Security Checklist (Section 6)

| Checklist Item | Status | Verification Detail |
| :--- | :---: | :--- |
| **No hardcoded secrets** | ✅ PASS | `app.py` reads `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, and `S3_BUCKET_NAME` exclusively from system environment variables. |
| **RDS Public Access Disabled** | ✅ PASS | `PubliclyAccessible: false` configured on RDS MySQL. |
| **Least Privilege DB Security Group** | ✅ PASS | `db-sg` port 3306 inbound strictly authorizes `web-sg` security group ID, never `0.0.0.0/0` or CIDR ranges. |
| **Restricted SSH Access** | ✅ PASS | `web-sg` port 22 is restricted to the administrator IP address. |
| **IAM Instance Profile Usage** | ✅ PASS | EC2 uses attached IAM role `ec2-s3-role` for boto3 authentication; zero static AWS access keys or secrets in source code or `.env`. |
| **Scoped IAM Policy** | ✅ PASS | Policy is strictly bounded to `arn:aws:s3:::<bucket-name>/*` for `s3:PutObject` and `s3:GetObject` (no wildcard `*` resource). |
| **S3 Bucket Listing Prevented** | ✅ PASS | Bucket policy grants `s3:GetObject` for individual files only; `s3:ListBucket` is denied to prevent data enumeration. |
| **Private Subnet Isolation** | ✅ PASS | Private route table contains only the local VPC CIDR route (`10.0.0.0/16 -> local`) with no route to an Internet Gateway. |
| **Git Secret Protection** | ✅ PASS | `.gitignore` configured to ignore `.env`, `.pem`, and environment configurations before committing. |

---

## 3. Technical Write-Up: S3 Access Decision & Future Enhancements

### Justification of S3 Access Pattern (Task D2)
For the student photo storage, we implemented **Option 1 (Scoped Public Object Read)**:
- **Design**: The S3 bucket maintains public write blocking and denies bucket listing (`s3:ListBucket`). A specific bucket policy allows public `s3:GetObject` only when the exact object key is requested. Uploading photos is restricted strictly to the EC2 web instance through temporary STS credentials issued to `ec2-s3-role`.
- **Trade-off Analysis**: This design allows student profile pictures to render seamlessly in public web browsers via standard image URLs without requiring server CPU overhead or complex reverse-proxy buffering. Because bucket listing is disabled, an external user attempting to browse `https://<bucket>.s3.amazonaws.com/` receives an `AccessDenied (403)` error, preventing unauthorized user enumeration.

### Improvement for Future Production Architecture
If given additional engineering time, the following improvements would be prioritized:
1. **AWS Secrets Manager Integration**: Migrate database connection credentials from systemd environment variables to **AWS Secrets Manager**, using boto3 to fetch and cache rotating secrets at runtime.
2. **Application Load Balancer (ALB) + Auto Scaling**: Position the EC2 instance behind an ALB with an Auto Scaling Group (Min: 1, Max: 2) across multiple AZs and terminate SSL/TLS with AWS Certificate Manager (ACM).
3. **Pre-Signed S3 URLs**: Transition to **Option 2 (Pre-Signed URLs)** with `BlockPublicAccess` fully enabled, generating 15-minute expiring access tokens for student photos to achieve zero public bucket exposure.

---

## 4. Verification & Validation Commands

### 1. Query MySQL from EC2
```bash
mysql -h <rds-endpoint> -u admin -p studentdb
SELECT * FROM students;
```

### 2. Verify S3 Photo Uploads
```bash
aws s3 ls s3://<your-bucket-name>
```

### 3. Verify Private RDS Inaccessibility from Local Laptop
```bash
telnet <rds-endpoint> 3306
# Expected result: Connection timed out (proves security group isolation)
```

### 4. Verify S3 Listing is Blocked
Visit `https://<your-bucket-name>.s3.amazonaws.com/` in your browser.
Expected result: `403 Forbidden / AccessDenied`.

---

## 5. Required Submission Screenshots Checklist

When submitting your final deliverable, take the following screenshots from the AWS Console:
1. **VPC Console**: Subnet list showing `public-subnet-1`, `private-subnet-1`, and `private-subnet-2`.
2. **EC2 Console**: Security Groups showing inbound rules for `web-sg` (Port 80 and 22).
3. **RDS Console**: Security Groups showing inbound rules for `db-sg` (Port 3306 from `web-sg`).
4. **RDS Instance Details**: Showing `Publicly accessible: No` and Subnet Group.
5. **IAM Console**: `ec2-s3-role` showing the attached inline/managed policy scoped to the bucket.
6. **EC2 Instance Details**: Showing the attached IAM Role and Public IP.
7. **Web Application**: Browser showing the Student Registration Form and Success Screen.
8. **Database & S3**: Terminal screenshot showing `SELECT * FROM students;` output and S3 console showing the uploaded student image.
