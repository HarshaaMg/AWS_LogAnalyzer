# AWS Cloud Log Analyzer - Complete Project Documentation

## Table of Contents
1. [Problem Statement](#problem-statement)
2. [Solution Overview](#solution-overview)
3. [System Architecture](#system-architecture)
4. [Data Flow Diagram](#data-flow-diagram)
5. [Technical Implementation](#technical-implementation)
6. [Features and Capabilities](#features-and-capabilities)
7. [Deployment Options](#deployment-options)
8. [API Documentation](#api-documentation)
9. [Configuration Guide](#configuration-guide)
10. [Troubleshooting](#troubleshooting)

---

## Problem Statement

### The Challenge

Organizations face significant challenges in monitoring and analyzing application logs:

1. **Scattered Log Sources**: Logs are distributed across multiple servers, applications, and services
2. **Real-time Analysis Gap**: Delayed detection of critical errors leads to extended downtime
3. **Alert Fatigue**: Too many false positives make it difficult to identify real issues
4. **Scalability Issues**: Traditional log analysis tools cannot handle growing log volumes
5. **Mobile Accessibility**: Lack of mobile-friendly dashboards for on-the-go monitoring
6. **Cost Constraints**: Enterprise solutions are expensive and complex to implement

### Impact

- **Increased Downtime**: Critical errors go undetected for hours
- **Poor User Experience**: Service degradation affects end users
- **Operational Overhead**: Manual log analysis consumes valuable engineering time
- **Security Risks**: Security breaches may go unnoticed in log noise
- **Compliance Issues**: Inability to track and audit system events

---

## Solution Overview

### AWS Cloud Log Analyzer

A comprehensive, full-stack cloud monitoring system that provides:

- **Automated Log Collection**: Collects logs from multiple sources automatically
- **Real-time Analysis**: Processes and analyzes logs in real-time
- **Intelligent Alerting**: Sends notifications for critical errors via email and SMS
- **Mobile Dashboard**: Responsive web interface accessible from any device
- **Dual Storage Mode**: Supports both local file storage and AWS cloud storage
- **File Upload**: Easy log file upload for ad-hoc analysis
- **Cost-Effective**: Open-source solution with minimal infrastructure costs

### Key Differentiators

1. **Flexibility**: Works with local files or AWS services
2. **Mobile-First**: Designed for mobile accessibility
3. **Easy Deployment**: Docker-based deployment for quick setup
4. **Real-Time Alerts**: Email and SMS notifications for critical issues
5. **No Vendor Lock-in**: Can run entirely on-premises or use AWS selectively

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     AWS Cloud Log Analyzer                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Frontend   │    │   Backend    │    │  Storage     │      │
│  │   (React)    │◄──►│   (Flask)    │◄──►│   Layer      │      │
│  │              │    │              │    │              │      │
│  │ - Dashboard  │    │ - REST API   │    │ - Local Files│      │
│  │ - Charts     │    │ - Auth       │    │ - DynamoDB   │      │
│  │ - Upload     │    │ - Analysis   │    │ - CloudWatch │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │              │
│         │                   │                   │              │
│         ▼                   ▼                   ▼              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Browser    │    │ Notification │    │   AWS Services│      │
│  │   (Mobile)   │    │   Service    │    │   (Optional) │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Architecture

#### Frontend Layer (React.js)
```
┌─────────────────────────────────────┐
│         React Frontend               │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────┐  ┌─────────┐          │
│  │ Login   │  │Dashboard│          │
│  │ Component│ │ Component│          │
│  └─────────┘  └─────────┘          │
│       │            │                │
│       └────┬───────┘                │
│            ▼                        │
│  ┌─────────────────────┐           │
│  │  API Integration    │           │
│  │  (Axios HTTP Client)│           │
│  └─────────────────────┘           │
│                                     │
│  ┌─────────────────────┐           │
│  │  Chart.js           │           │
│  │  (Data Visualization)│          │
│  └─────────────────────┘           │
│                                     │
└─────────────────────────────────────┘
```

#### Backend Layer (Flask)
```
┌─────────────────────────────────────┐
│         Flask Backend               │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐   │
│  │      API Endpoints           │   │
│  ├─────────────────────────────┤   │
│  │ POST /api/login             │   │
│  │ GET  /api/logs              │   │
│  │ POST /api/logs              │   │
│  │ POST /api/upload            │   │
│  │ GET  /api/alerts            │   │
│  │ GET  /api/stats             │   │
│  │ POST /api/stats/refresh     │   │
│  │ GET  /api/health            │   │
│  └─────────────────────────────┘   │
│                │                     │
│                ▼                     │
│  ┌─────────────────────────────┐   │
│  │      Storage Adapter        │   │
│  ├─────────────────────────────┤   │
│  │ Local Mode:                 │   │
│  │ - LocalLogReader           │   │
│  │ - JSON Files               │   │
│  │                             │   │
│  │ AWS Mode:                   │   │
│  │ - AWSStorageAdapter        │   │
│  │ - DynamoDB                  │   │
│  │ - CloudWatch                │   │
│  │ - SNS                       │   │
│  └─────────────────────────────┘   │
│                │                     │
│                ▼                     │
│  ┌─────────────────────────────┐   │
│  │   Notification Service      │   │
│  ├─────────────────────────────┤   │
│  │ - Email Alerts (SMTP)       │   │
│  │ - SMS Alerts (Twilio)       │   │
│  │ - SNS Alerts (AWS)          │   │
│  └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

### Storage Mode Architecture

#### Local Mode (Default)
```
┌─────────────────────────────────────┐
│         Local Storage Mode          │
├─────────────────────────────────────┤
│                                     │
│  Log Files                          │
│  ┌─────────────────────────────┐   │
│  │ backend/logs/                │   │
│  │ ├── application.log         │   │
│  │ ├── system.log               │   │
│  │ ├── auth.log                 │   │
│  │ └── manual_logs.log          │   │
│  └─────────────────────────────┘   │
│                │                     │
│                ▼                     │
│  Local Storage                     │
│  ┌─────────────────────────────┐   │
│  │ backend/local_storage/      │   │
│  │ ├── alerts.json             │   │
│  │ └── stats.json              │   │
│  └─────────────────────────────┘   │
│                                     │
│  ✓ No AWS credentials required      │
│  ✓ Zero cloud costs                 │
│  ✓ Fast local access                │
│  ✓ Ideal for development/testing   │
│                                     │
└─────────────────────────────────────┘
```

#### AWS Mode
```
┌─────────────────────────────────────┐
│           AWS Storage Mode           │
├─────────────────────────────────────┤
│                                     │
│  AWS Services                       │
│  ┌─────────────────────────────┐   │
│  │ DynamoDB                     │   │
│  │ ├── CloudLogs Table          │   │
│  │ ├── CloudAlerts Table        │   │
│  │ └── CloudStats Table         │   │
│  └─────────────────────────────┘   │
│                │                     │
│                ▼                     │
│  ┌─────────────────────────────┐   │
│  │ CloudWatch Logs              │   │
│  │ - Log Groups                 │   │
│  │ - Log Streams                │   │
│  └─────────────────────────────┘   │
│                │                     │
│                ▼                     │
│  ┌─────────────────────────────┐   │
│  │ SNS (Simple Notification    │   │
│  │     Service)                │   │
│  │ - Alert Topics              │   │
│  │ - Email Subscriptions       │   │
│  └─────────────────────────────┘   │
│                                     │
│  ✓ Highly scalable                  │
│  ✓ Managed services                 │
│  ✓ Global availability              │
│  ✓ Production-ready                │
│                                     │
└─────────────────────────────────────┘
```

---

## Data Flow Diagram

### Log Collection and Analysis Flow

```
┌──────────────┐
│  Log Source  │
│ (Application │
│    / Server) │
└──────┬───────┘
       │
       │ 1. Generate Logs
       ▼
┌──────────────┐
│ Log File     │
│ (.log/.txt)  │
└──────┬───────┘
       │
       ├─────────────────┐
       │                 │
       │ 2a. Manual Upload│
       ▼                 │
┌──────────────┐          │ 2b. Auto-Collection
│  Dashboard   │          │
│  Upload UI   │          │
└──────┬───────┘          │
       │                  │
       │ 3. POST /api/upload
       ▼                  │
┌──────────────┐          │
│ Flask Backend│◄─────────┘
│              │
└──────┬───────┘
       │
       │ 4. Parse Logs
       ▼
┌──────────────┐
│ Log Parser   │
│ - Extract    │
│   Timestamp  │
│ - Extract    │
│   Level      │
│ - Extract    │
│   Message    │
└──────┬───────┘
       │
       ├─────────────────┐
       │                 │
       │ 5a. Local Mode   │ 5b. AWS Mode
       ▼                 ▼
┌──────────────┐  ┌──────────────┐
│ Local Files  │  │  DynamoDB    │
│ - logs/      │  │ - CloudLogs  │
│ - storage/   │  │              │
└──────┬───────┘  └──────┬───────┘
       │                 │
       └────────┬────────┘
                │
                │ 6. Analyze Logs
                ▼
         ┌──────────────┐
         │ Log Analyzer │
         │ - Count Errors│
         │ - Count Warnings│
         │ - Detect Critical│
         │ - Calculate Trends│
         └──────┬───────┘
                │
                ├─────────────────┐
                │                 │
                │ 7a. Store Stats│ 7b. Check Critical
                ▼                 ▼
         ┌──────────────┐  ┌──────────────┐
         │ Stats Storage│  │ Alert Service│
         │ - stats.json │  │ - Email      │
         │ - DynamoDB   │  │ - SMS        │
         └──────┬───────┘  │ - SNS        │
                │          └──────┬───────┘
                │                 │
                └────────┬────────┘
                         │
                         │ 8. Return Results
                         ▼
                  ┌──────────────┐
                  │  Dashboard   │
                  │ - Update UI  │
                  │ - Show Charts│
                  │ - Display Logs│
                  └──────────────┘
```

### Real-time Monitoring Flow

```
┌──────────────┐
│   Browser    │
│  (Dashboard) │
└──────┬───────┘
       │
       │ 1. Auto-refresh (10s)
       ▼
┌──────────────┐
│ GET /api/stats│
│ GET /api/logs │
└──────┬───────┘
       │
       │ 2. Fetch from Storage
       ▼
┌──────────────┐
│ Storage Layer│
│ (Local/AWS)  │
└──────┬───────┘
       │
       │ 3. Return Data
       ▼
┌──────────────┐
│  Dashboard   │
│  Update UI   │
└──────┬───────┘
       │
       │ 4. Check for Critical
       ▼
┌──────────────┐
│ Alert Check  │
└──────┬───────┘
       │
       │ 5. If Critical
       ▼
┌──────────────┐
│ Notification │
│   Service    │
└──────┬───────┘
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌──────────────┐  ┌──────────────┐
│   Email      │  │     SMS      │
│ (SMTP/Gmail) │  │  (Twilio)    │
└──────────────┘  └──────────────┘
       │                 │
       └────────┬────────┘
                │
                │ 6. Send to User
                ▼
         ┌──────────────┐
         │  Mobile Device│
         │  (User)       │
         └──────────────┘
```

### Authentication Flow

```
┌──────────────┐
│   Browser    │
│  (Login Page)│
└──────┬───────┘
       │
       │ 1. Enter Credentials
       ▼
┌──────────────┐
│ POST /api/login│
│ {username,   │
│  password}   │
└──────┬───────┘
       │
       │ 2. Validate
       ▼
┌──────────────┐
│ Flask Auth   │
│ - Check Users│
│ - Generate JWT│
└──────┬───────┘
       │
       │ 3. Return Token
       ▼
┌──────────────┐
│  Browser     │
│  Store Token │
│  (localStorage)│
└──────┬───────┘
       │
       │ 4. Include in Requests
       ▼
┌──────────────┐
│ API Requests │
│ Authorization:│
│ Bearer <token>│
└──────┬───────┘
       │
       │ 5. Validate JWT
       ▼
┌──────────────┐
│ Flask JWT    │
│ - Verify Token│
│ - Allow Access│
└──────┬───────┘
       │
       │ 6. Return Data
       ▼
┌──────────────┐
│  Dashboard   │
│  Display Data│
└──────────────┘
```

---

## Technical Implementation

### Technology Stack

#### Frontend
- **React.js 18.2**: Modern UI framework
- **Tailwind CSS**: Utility-first CSS framework
- **Chart.js 4.4**: Data visualization library
- **React Chart.js 2**: React wrapper for Chart.js
- **Lucide React**: Icon library
- **Axios 1.6**: HTTP client for API calls
- **React Router 6.20**: Client-side routing

#### Backend
- **Flask 3.0**: Python web framework
- **Flask-CORS 4.0**: Cross-origin resource sharing
- **Flask-JWT-Extended 4.6**: JWT authentication
- **Boto3 1.34**: AWS SDK for Python
- **Python-dotenv 1.0**: Environment variable management
- **Gunicorn 21.2**: Production WSGI server

#### AWS Services (Optional)
- **DynamoDB**: NoSQL database for log storage
- **CloudWatch Logs**: Log aggregation and monitoring
- **SNS**: Simple Notification Service for alerts
- **IAM**: Identity and Access Management

#### Notification Services
- **SMTP/Gmail**: Email alerts
- **Twilio**: SMS alerts (optional)
- **AWS SNS**: Cloud-based notifications (AWS mode)

#### Deployment
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **Nginx**: Reverse proxy and static file serving

### Project Structure

```
aws-log-analyzer/
├── backend/                    # Flask backend application
│   ├── app.py                 # Main Flask application
│   ├── local_log_reader.py    # Local file log parser
│   ├── dummy_log_generator.py # Sample log generator
│   ├── notification_service.py # Email/SMS notification service
│   ├── aws_storage_adapter.py  # AWS storage adapter
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile             # Docker image definition
│   ├── logs/                  # Local log files directory
│   └── local_storage/         # Local JSON storage
│       ├── alerts.json
│       └── stats.json
│
├── frontend/                   # React frontend application
│   ├── src/
│   │   ├── components/
│   │   │   ├── Login.js      # Login component
│   │   │   └── Dashboard.js  # Main dashboard component
│   │   ├── App.js            # Main React app
│   │   ├── App.css           # App styles
│   │   ├── index.js          # React entry point
│   │   └── index.css         # Global styles
│   ├── public/
│   │   └── index.html        # HTML template
│   ├── package.json          # Node.js dependencies
│   ├── Dockerfile            # Docker image definition
│   ├── nginx.conf            # Nginx configuration
│   ├── tailwind.config.js    # Tailwind CSS configuration
│   └── postcss.config.js     # PostCSS configuration
│
├── cloudwatch/                # AWS CloudWatch integration
│   ├── log_generator.py      # CloudWatch log generator
│   ├── cloudwatch_sender.py  # CloudWatch log sender
│   ├── setup_aws_resources.py # AWS resource setup
│   └── requirements.txt      # Python dependencies
│
├── lambda/                    # AWS Lambda functions
│   ├── log_processor.py      # Log processing Lambda
│   └── requirements.txt      # Python dependencies
│
├── terraform/                 # Infrastructure as Code
│   ├── main.tf               # Main Terraform configuration
│   ├── variables.tf          # Variable definitions
│   └── outputs.tf            # Output definitions
│
├── deploy/                    # Deployment scripts
│   ├── deploy_ec2.sh         # EC2 deployment script
│   ├── setup_ec2.sh          # EC2 setup script
│   ├── lambda_deploy.sh      # Lambda deployment script
│   └── nginx.conf            # Nginx configuration
│
├── docker-compose.yml         # Docker Compose configuration
├── .env.example              # Environment variables template
├── generate_logs.py          # Log generation script
├── README.md                 # Project documentation
├── LOCAL_SETUP.md            # Local setup guide
├── MODE_SWITCHING.md         # Storage mode switching guide
└── PROJECT_DOCUMENTATION.md  # This file
```

### Key Components Implementation

#### 1. Log Parser (local_log_reader.py)

**Purpose**: Parse local log files into structured data

**Implementation**:
```python
class LocalLogReader:
    def __init__(self, log_dir='logs'):
        self.log_dir = log_dir
    
    def read_log_file(self, filename):
        # Read and parse log file
        # Support multiple formats:
        # [TIMESTAMP] LEVEL MESSAGE
        # TIMESTAMP LEVEL MESSAGE
        # Plain text (treated as INFO)
    
    def get_all_logs(self):
        # Read all log files in directory
        # Sort by timestamp
        # Return structured log entries
```

**Supported Formats**:
- `[2024-01-15 10:30:45] ERROR Database connection failed`
- `2024-01-15 10:30:45 ERROR Database connection failed`
- Plain text messages (INFO level)

#### 2. Notification Service (notification_service.py)

**Purpose**: Send alerts via email and SMS

**Implementation**:
```python
class NotificationService:
    def send_email_alert(self, subject, message):
        # SMTP email sending
        # Supports Gmail and other SMTP servers
    
    def send_sms_alert(self, message):
        # Twilio SMS sending
        # Optional feature
    
    def create_alert(self, level, message, source):
        # Create alert record
        # Send notifications for CRITICAL level
        # Store alert history
```

**Alert Triggers**:
- CRITICAL logs → Email + SMS
- ERROR logs → Email (configurable)
- Manual log addition with ERROR/CRITICAL level

#### 3. AWS Storage Adapter (aws_storage_adapter.py)

**Purpose**: Interface with AWS services

**Implementation**:
```python
class AWSStorageAdapter:
    def __init__(self):
        # Initialize boto3 clients
        # DynamoDB, CloudWatch, SNS
    
    def get_logs(self, limit, severity):
        # Query DynamoDB for logs
        # Support filtering by severity
    
    def add_log(self, level, message, source):
        # Add log to DynamoDB
        # Store with timestamp and metadata
    
    def send_sns_alert(self, subject, message):
        # Publish to SNS topic
        # Trigger email subscriptions
```

**AWS Services Used**:
- **DynamoDB**: Log, alert, and stats storage
- **CloudWatch Logs**: Log aggregation
- **SNS**: Alert notifications

#### 4. Flask Backend (app.py)

**Purpose**: REST API and business logic

**Key Endpoints**:
```python
POST /api/login              # User authentication
GET  /api/logs               # Retrieve logs
POST /api/logs               # Add log entry
POST /api/upload             # Upload log file
GET  /api/alerts             # Retrieve alerts
GET  /api/stats              # Retrieve statistics
POST /api/stats/refresh      # Refresh statistics
GET  /api/health             # Health check
```

**Storage Mode Switching**:
```python
STORAGE_MODE = os.getenv('STORAGE_MODE', 'local')

if STORAGE_MODE == 'aws':
    storage_adapter = AWSStorageAdapter()
else:
    log_reader = LocalLogReader()
```

#### 5. React Dashboard (Dashboard.js)

**Purpose**: User interface for log analysis

**Key Features**:
- Real-time statistics display
- Interactive charts (Pie, Line)
- Log table with filtering
- File upload modal
- Alert notifications
- Dark/Light mode toggle
- Mobile-responsive design

**State Management**:
```javascript
const [stats, setStats] = useState(null);
const [logs, setLogs] = useState([]);
const [alerts, setAlerts] = useState([]);
const [showUploadModal, setShowUploadModal] = useState(false);
```

**Auto-refresh**:
```javascript
useEffect(() => {
  fetchData();
  const interval = setInterval(fetchData, 10000);
  return () => clearInterval(interval);
}, [filterSeverity]);
```

---

## Features and Capabilities

### 1. Log Collection

**Methods**:
- **Manual Upload**: Upload log files through dashboard
- **File Placement**: Place log files in `backend/logs/` directory
- **Dummy Generation**: Generate sample logs for testing
- **AWS Integration**: CloudWatch log streaming (AWS mode)

**Supported Formats**:
- `.log` files
- `.txt` files
- `.json` files

**Log Levels**:
- INFO: Informational messages
- WARNING: Warning messages
- ERROR: Error messages
- CRITICAL: Critical system failures

### 2. Real-time Analysis

**Metrics Calculated**:
- Total log count
- Error count
- Warning count
- Critical count
- Most frequent errors
- Error trends over time

**Analysis Frequency**:
- Auto-refresh every 10 seconds
- Manual refresh button
- Real-time updates after upload

### 3. Intelligent Alerting

**Alert Types**:
- **Email Alerts**: SMTP-based email notifications
- **SMS Alerts**: Twilio-based SMS notifications
- **SNS Alerts**: AWS SNS notifications (AWS mode)

**Alert Triggers**:
- CRITICAL log level → Immediate alert
- ERROR log level → Configurable alert
- Manual log addition with critical level

**Alert Content**:
- Error message
- Timestamp
- Source
- Severity level

### 4. Mobile Dashboard

**Features**:
- Responsive design for all screen sizes
- Touch-friendly interface
- Dark/Light mode toggle
- Optimized charts for mobile
- Fast loading times

**Supported Devices**:
- iOS (iPhone, iPad)
- Android devices
- Tablets
- Desktop browsers

### 5. Dual Storage Mode

**Local Mode**:
- No AWS credentials required
- Zero cloud costs
- Fast local access
- Ideal for development/testing

**AWS Mode**:
- Highly scalable
- Managed services
- Global availability
- Production-ready

### 6. File Upload

**Features**:
- Drag-and-drop file upload
- Multiple file format support
- Real-time upload progress
- Automatic log parsing
- Immediate analysis results

**Upload Process**:
1. Click "Upload Log File" button
2. Select file from device
3. Automatic parsing
4. Display results (logs parsed, errors found)
5. Auto-refresh dashboard

### 7. Data Visualization

**Charts**:
- **Pie Chart**: Log distribution by level
- **Line Chart**: Error trends over time
- **Stat Cards**: Key metrics at a glance

**Customization**:
- Dark/Light mode
- Responsive sizing
- Interactive tooltips
- Color-coded severity

### 8. Search and Filter

**Search**:
- Search by message content
- Search by log level
- Real-time filtering

**Filter**:
- Filter by severity level
- Filter by time range
- Filter by source

### 9. Export Functionality

**CSV Export**:
- Download logs as CSV
- Include timestamp, level, message, source
- Compatible with Excel, Google Sheets

### 10. Security

**Authentication**:
- JWT-based authentication
- Secure token storage
- Token expiration (24 hours)

**Authorization**:
- Protected API endpoints
- Role-based access (admin)
- Secure file upload

---

## Deployment Options

### 1. Local Development

**Prerequisites**:
- Python 3.11+
- Node.js 18+
- Git

**Setup**:
```bash
# Clone repository
git clone <repository-url>
cd aws-log-analyzer

# Setup backend
cd backend
pip install -r requirements.txt
python app.py

# Setup frontend (new terminal)
cd frontend
npm install
npm start

# Generate logs
python generate_logs.py
```

**Access**:
- Frontend: http://localhost:3000
- Backend: http://localhost:5000

### 2. Docker Deployment

**Prerequisites**:
- Docker
- Docker Compose

**Setup**:
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

**Access**:
- Frontend: http://localhost
- Backend: http://localhost:5000

### 3. AWS Deployment

**Prerequisites**:
- AWS Account
- AWS CLI configured
- Terraform installed

**Setup**:
```bash
# Configure Terraform
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars

# Deploy infrastructure
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars

# Deploy Lambda
cd ..
chmod +x deploy/lambda_deploy.sh
./deploy/lambda_deploy.sh
```

**Components Deployed**:
- EC2 instance
- DynamoDB tables
- CloudWatch log groups
- SNS topics
- Lambda functions
- IAM roles

### 4. EC2 Deployment

**Setup**:
```bash
# Setup EC2 instance
chmod +x deploy/setup_ec2.sh
./deploy/setup_ec2.sh

# Deploy to EC2
chmod +x deploy/deploy_ec2.sh
./deploy/deploy_ec2.sh <EC2_HOST> <KEY_PATH>
```

---

## API Documentation

### Authentication

All endpoints (except `/api/login` and `/api/health`) require JWT authentication.

**Login**
```http
POST /api/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": "admin"
}
```

**Usage**:
```http
Authorization: Bearer <access_token>
```

### Endpoints

#### 1. Get Logs
```http
GET /api/logs?limit=50&severity=ERROR
Authorization: Bearer <token>
```

**Parameters**:
- `limit` (optional): Number of logs to return (default: 50)
- `severity` (optional): Filter by log level (INFO, WARNING, ERROR, CRITICAL)

**Response**:
```json
{
  "logs": [
    {
      "log_id": "log_1234567890",
      "timestamp": "2024-01-15T10:30:45",
      "level": "ERROR",
      "message": "Database connection failed",
      "severity": "ERROR",
      "source": "application"
    }
  ]
}
```

#### 2. Add Log
```http
POST /api/logs
Authorization: Bearer <token>
Content-Type: application/json

{
  "level": "ERROR",
  "message": "Database connection failed",
  "source": "manual"
}
```

**Response**:
```json
{
  "message": "Log added successfully",
  "log": {
    "log_id": "log_1234567890",
    "timestamp": "2024-01-15T10:30:45",
    "level": "ERROR",
    "message": "Database connection failed",
    "severity": "ERROR",
    "source": "manual"
  }
}
```

#### 3. Upload Log File
```http
POST /api/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <log_file>
```

**Response**:
```json
{
  "message": "File uploaded successfully",
  "filename": "application.log",
  "logs_parsed": 200,
  "critical_errors": 5,
  "errors": 15
}
```

#### 4. Get Alerts
```http
GET /api/alerts
Authorization: Bearer <token>
```

**Response**:
```json
{
  "alerts": [
    {
      "alert_id": "alert_1234567890",
      "timestamp": "2024-01-15T10:30:45",
      "level": "CRITICAL",
      "message": "System crash imminent",
      "source": "log_analysis"
    }
  ]
}
```

#### 5. Get Statistics
```http
GET /api/stats
Authorization: Bearer <token>
```

**Response**:
```json
{
  "stats": {
    "stat_id": "latest",
    "total_logs": 280,
    "total_errors": 15,
    "total_warnings": 30,
    "critical_count": 5,
    "most_frequent_errors": [
      {
        "message": "Database connection failed",
        "count": 8
      }
    ],
    "error_trends": [5, 8, 3, 10, 15],
    "updated_at": "2024-01-15T10:30:45"
  }
}
```

#### 6. Refresh Statistics
```http
POST /api/stats/refresh
Authorization: Bearer <token>
```

**Response**:
```json
{
  "message": "Stats refreshed",
  "stats": {
    "stat_id": "latest",
    "total_logs": 280,
    "total_errors": 15,
    "total_warnings": 30,
    "critical_count": 5,
    "most_frequent_errors": [],
    "error_trends": [],
    "updated_at": "2024-01-15T10:30:45"
  }
}
```

#### 7. Health Check
```http
GET /api/health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:45",
  "service": "AWS Cloud Log Analyzer"
}
```

---

## Configuration Guide

### Environment Variables

#### Required Variables

```bash
JWT_SECRET_KEY=your-secret-key-here
```

#### Storage Mode Configuration

```bash
# Storage Mode: 'local' or 'aws'
STORAGE_MODE=local
```

#### AWS Configuration (AWS Mode Only)

```bash
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=AKIA5J7F4KY63RP5SUVL
AWS_SECRET_ACCESS_KEY=your-secret-access-key
SNS_TOPIC_ARN=arn:aws:sns:ap-south-1:914773268029:log-alerts
```

#### Email Configuration

```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_EMAIL=harshamg41@gmail.com
```

#### SMS Configuration (Optional)

```bash
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=+1234567890
MOBILE_NUMBER=+919876543210
```

### Gmail App Password Setup

1. Go to Google Account settings
2. Security → 2-Step Verification
3. App passwords → Generate new app password
4. Use the generated password in `SMTP_PASSWORD`

### Twilio Setup (Optional)

1. Sign up at twilio.com
2. Get Account SID and Auth Token from dashboard
3. Purchase a phone number
4. Add credentials to `.env` file

---

## Troubleshooting

### Common Issues

#### 1. Backend Not Starting

**Problem**: Backend fails to start

**Solutions**:
- Check Python version (3.11+ required)
- Install dependencies: `pip install -r requirements.txt`
- Check port 5000 is not in use
- Verify `.env` file exists

#### 2. Frontend Not Connecting to Backend

**Problem**: Frontend shows connection errors

**Solutions**:
- Verify backend is running on port 5000
- Check CORS configuration in backend
- Verify proxy setting in `package.json`
- Check network connectivity

#### 3. No Logs Showing in Dashboard

**Problem**: Dashboard shows no logs

**Solutions**:
- Generate dummy logs: `python generate_logs.py`
- Verify log files exist in `backend/logs/`
- Check file permissions
- Try refreshing stats manually

#### 4. AWS Mode Not Working

**Problem**: AWS mode connection errors

**Solutions**:
- Verify AWS credentials in `.env`
- Check AWS region matches resources
- Ensure DynamoDB tables exist
- Verify IAM permissions
- Run `python cloudwatch/setup_aws_resources.py`

#### 5. Email Alerts Not Sending

**Problem**: Email alerts not received

**Solutions**:
- Verify SMTP credentials
- Check Gmail app password (not regular password)
- Verify email address is correct
- Check firewall settings
- Test SMTP connection manually

#### 6. Docker Container Issues

**Problem**: Docker containers not starting

**Solutions**:
- Check Docker is running: `docker ps`
- Rebuild containers: `docker-compose up -d --build`
- Check volume mounts
- Verify environment variables
- Check container logs: `docker-compose logs backend`

#### 7. Mobile Access Not Working

**Problem**: Cannot access from mobile device

**Solutions**:
- Ensure mobile and laptop on same WiFi
- Check firewall settings
- Verify backend binding to 0.0.0.0
- Use IP address instead of localhost
- Check router settings

### Debug Mode

Enable debug mode for detailed error messages:

```bash
# Backend
cd backend
FLASK_DEBUG=1 python app.py

# Frontend
cd frontend
npm start
```

### Log Files

Check log files for errors:

```bash
# Backend logs
backend/logs/application.log

# Docker logs
docker-compose logs backend
docker-compose logs frontend
```

---

## Conclusion

The AWS Cloud Log Analyzer provides a comprehensive solution for log monitoring and analysis with the following key benefits:

### Key Achievements

1. **Flexibility**: Dual storage mode (local/AWS) for different use cases
2. **Accessibility**: Mobile-responsive dashboard for on-the-go monitoring
3. **Real-time Alerts**: Email and SMS notifications for critical issues
4. **Ease of Use**: Simple file upload and intuitive interface
5. **Cost-Effective**: Open-source with minimal infrastructure costs
6. **Scalability**: AWS mode for production-scale deployments

### Use Cases

- **Development**: Local mode for testing and development
- **Small Teams**: Local mode with email alerts
- **Enterprise**: AWS mode with full cloud integration
- **Mobile Monitoring**: Dashboard accessible from any device
- **Incident Response**: Real-time alerts for critical issues

### Future Enhancements

- Machine learning for anomaly detection
- Integration with more log sources
- Advanced analytics and reporting
- Multi-user support with roles
- Custom alert rules and thresholds
- Integration with Slack and Microsoft Teams

---

## Contact and Support

For support, issues, or contributions:
- Email: support@example.com
- GitHub: [Repository URL]
- Documentation: [Documentation URL]

---

**Version**: 1.0.0  
**Last Updated**: June 25, 2026  
**License**: MIT
