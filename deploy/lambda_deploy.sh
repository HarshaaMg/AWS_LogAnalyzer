#!/bin/bash

# Lambda Deployment Script
# Packages and deploys the Lambda function

set -e

echo "Packaging Lambda function..."

LAMBDA_DIR="../lambda"
ZIP_FILE="log_processor.zip"

# Create zip file
cd "$LAMBDA_DIR"
zip -r "$ZIP_FILE" log_processor.py requirements.txt

echo "Uploading Lambda function..."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "AWS CLI not found. Please install it first."
    echo "Run: pip install awscli"
    exit 1
fi

# Update Lambda function
aws lambda update-function-code \
    --function-name log-processor \
    --zip-file fileb://"$ZIP_FILE"

echo "Lambda deployment complete!"

# Clean up
rm "$ZIP_FILE"
