@echo off
setlocal EnableDelayedExpansion

echo =========================================================================
echo ICT Academy Kerala - AWS Cloud Deployment Project
echo Deploying Secure Flask Web Application on AWS (ap-south-1)
echo =========================================================================
echo.

set REGION=ap-south-1
set PROFILE=aws-agent
set STACK_NAME=ict-student-app

echo [1/3] Enter Deployment Parameters:
echo.

:: Prompt for EC2 Key Pair
set /p KEY_NAME="Enter EC2 Key Pair Name (must exist in %REGION%): "
if "%KEY_NAME%"=="" (
    echo.
    echo [ERROR] Key Pair Name cannot be empty.
    exit /b 1
)

:: Prompt for SSH CIDR
set /p SSH_LOCATION="Enter your public IP CIDR for SSH access (e.g., 203.0.113.25/32): "
if "%SSH_LOCATION%"=="" (
    echo.
    echo [ERROR] SSH CIDR cannot be empty.
    exit /b 1
)

:: Prompt for DB Password securely without echoing to console
echo Enter RDS Master Database Password (minimum 8 characters):
for /f "delims=" %%p in ('powershell -NoProfile -Command "$p = Read-Host -AsSecureString; [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($p))"') do set "DB_PASSWORD=%%p"

:: Fallback if PowerShell masked input returned empty
if "%DB_PASSWORD%"=="" (
    set /p DB_PASSWORD="Enter RDS Master Database Password: "
)

if "%DB_PASSWORD%"=="" (
    echo.
    echo [ERROR] Database password cannot be empty.
    exit /b 1
)

echo.
echo =========================================================================
echo Deploying CloudFormation Stack '%STACK_NAME%' in Region '%REGION%' using Profile '%PROFILE%'...
echo This will create VPC, Subnets, Security Groups, IAM Role, S3 Bucket, RDS MySQL, and EC2 Instance.
echo =========================================================================
echo.

aws cloudformation deploy ^
  --template-file cloudformation.yaml ^
  --stack-name %STACK_NAME% ^
  --parameter-overrides DBPassword="%DB_PASSWORD%" KeyName="%KEY_NAME%" SSHLocation="%SSH_LOCATION%" ^
  --capabilities CAPABILITY_NAMED_IAM ^
  --region %REGION% ^
  --profile %PROFILE%

set DEPLOY_STATUS=%ERRORLEVEL%

:: Clear password variable from environment immediately after execution
set "DB_PASSWORD="

if %DEPLOY_STATUS% NEQ 0 (
    echo.
    echo [ERROR] Deployment failed with exit code %DEPLOY_STATUS%.
    echo Please check the CloudFormation events in the AWS Console for details.
    exit /b %DEPLOY_STATUS%
)

echo.
echo =========================================================================
echo Deployment Complete! Stack Outputs:
echo =========================================================================
aws cloudformation describe-stacks ^
  --stack-name %STACK_NAME% ^
  --region %REGION% ^
  --profile %PROFILE% ^
  --query "Stacks[0].Outputs" ^
  --output table

echo.
echo Open the WebsiteURL in your browser to test the Student Registration form!
exit /b 0
