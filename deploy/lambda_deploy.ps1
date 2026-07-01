# Lambda Deployment Script for Windows
# Packages and deploys the Lambda function

Write-Host "Packaging Lambda function..." -ForegroundColor Green

$LAMBDA_DIR = "..\lambda"
$ZIP_FILE = "log_processor.zip"

# Create zip file
Set-Location $LAMBDA_DIR
Compress-Archive -Path "log_processor.py", "requirements.txt" -DestinationPath $ZIP_FILE -Force

Write-Host "Uploading Lambda function..." -ForegroundColor Green

# Check if AWS CLI is installed
$awsInstalled = Get-Command aws -ErrorAction SilentlyContinue
if (-not $awsInstalled) {
    Write-Host "AWS CLI not found. Please install it first." -ForegroundColor Red
    Write-Host "Run: pip install awscli" -ForegroundColor Yellow
    exit 1
}

# Update Lambda function
aws lambda update-function-code `
    --function-name log-processor `
    --zip-file fileb://"$ZIP_FILE"

Write-Host "Lambda deployment complete!" -ForegroundColor Green

# Clean up
Remove-Item $ZIP_FILE

Set-Location "..\deploy"
