#!/bin/bash

# EC2 Setup Script
# Run this on your EC2 instance to set up the environment

set -e

echo "Setting up EC2 instance for AWS Cloud Log Analyzer..."

# Update system
sudo yum update -y

# Install Docker
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Nginx
sudo yum install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Configure firewall
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload

# Create application directory
mkdir -p /home/ec2-user/aws-log-analyzer

echo "EC2 setup complete!"
echo "Next steps:"
echo "1. Copy application files to /home/ec2-user/aws-log-analyzer"
echo "2. Copy .env file"
echo "3. Run docker-compose up -d"
