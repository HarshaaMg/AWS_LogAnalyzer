#!/bin/bash

# EC2 Deployment Script for AWS Cloud Log Analyzer
# This script deploys the application to an EC2 instance

set -e

echo "Starting EC2 deployment..."

# Configuration
EC2_USER="ec2-user"
EC2_HOST=$1
KEY_PATH=$2

if [ -z "$EC2_HOST" ] || [ -z "$KEY_PATH" ]; then
    echo "Usage: ./deploy_ec2.sh <EC2_HOST> <KEY_PATH>"
    exit 1
fi

echo "Deploying to $EC2_HOST..."

# Copy files to EC2
echo "Copying files to EC2..."
scp -i "$KEY_PATH" -r ../backend "$EC2_USER@$EC2_HOST:/home/$EC2_USER/"
scp -i "$KEY_PATH" -r ../frontend "$EC2_USER@$EC2_HOST:/home/$EC2_USER/"
scp -i "$KEY_PATH" ../docker-compose.yml "$EC2_USER@$EC2_HOST:/home/$EC2_USER/"
scp -i "$KEY_PATH" ../.env "$EC2_USER@$EC2_HOST:/home/$EC2_USER/"

# Install Docker on EC2
echo "Installing Docker on EC2..."
ssh -i "$KEY_PATH" "$EC2_USER@$EC2_HOST" << 'ENDSSH'
    sudo yum update -y
    sudo yum install -y docker
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -a -G docker ec2-user
ENDSSH

# Build and start containers
echo "Building and starting containers..."
ssh -i "$KEY_PATH" "$EC2_USER@$EC2_HOST" << 'ENDSSH'
    cd /home/ec2-user
    docker-compose down
    docker-compose build
    docker-compose up -d
ENDSSH

echo "Deployment complete!"
echo "Application is running on http://$EC2_HOST"
