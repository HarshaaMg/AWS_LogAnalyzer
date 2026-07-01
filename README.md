# AWS Cloud Log Analyzer

A production-ready, full-stack log monitoring and analysis platform built with Flask, React, Docker, and AWS services. It helps teams collect logs, analyze severity patterns, surface critical issues, and monitor system health through a responsive dashboard.

![Architecture](https://img.shields.io/badge/Stack-Flask%20%2B%20React%20%2B%20AWS-blue)
![Docker](https://img.shields.io/badge/Deployment-Docker%20Compose-green)
![Python](https://img.shields.io/badge/Python-3.11%2B-yellow)
![Node](https://img.shields.io/badge/Node.js-18%2B-lightgrey)

---

## Overview

AWS Cloud Log Analyzer is designed to simplify observability for applications and infrastructure by combining:

- log ingestion and parsing,
- real-time severity analysis,
- alert generation,
- dashboard-based monitoring,
- and cloud deployment support.

It supports both local development workflows and AWS-native deployments, making it suitable for demos, internal tools, and deployment experiments.

---

## Key Features

- Log ingestion from uploaded files and manual input
- Severity-based parsing for INFO, WARNING, ERROR, and CRITICAL logs
- Dashboard with summary cards, charts, search, and filters
- Alert creation for critical and error events
- JWT-based authentication
- Local storage mode for development
- AWS storage mode with DynamoDB, CloudWatch, Lambda, and SNS integration
- Docker Compose support for containerized deployment
- Dark mode support and responsive UI
- CSV export for logs

---

## Project Architecture

```text
User Browser
    │
    ▼
React Frontend
    │
    ▼
Flask Backend
    │
    ├── Local Storage Mode
    │     ├── backend/logs/
    │     └── backend/local_storage/
    │
    └── AWS Storage Mode
          ├── DynamoDB
          ├── CloudWatch Logs
          └── SNS
```

---

## Tech Stack

### Backend
- Python 3.11+
- Flask
- Flask-JWT-Extended
- Flask-CORS
- boto3
- python-dotenv
- Gunicorn

### Frontend
- React 18
- React Router
- Axios
- Tailwind CSS
- Chart.js
- Lucide React

### Infrastructure & Deployment
- Docker
- Docker Compose
- Nginx
- Terraform
- AWS Lambda
- AWS CloudWatch
- AWS SNS
- AWS DynamoDB

---

## Repository Structure

```text
aws-log-analyzer/
├── backend/
│   ├── app.py
│   ├── aws_storage_adapter.py
│   ├── dummy_log_generator.py
│   ├── local_log_reader.py
│   ├── notification_service.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── local_storage/
│       ├── alerts.json
│       └── stats.json
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.js
│   │   │   └── Login.js
│   │   ├── App.js
│   │   ├── App.css
│   │   ├── index.css
│   │   └── index.js
│   ├── package.json
│   ├── Dockerfile
│   ├── nginx.conf
│   └── tailwind.config.js
├── cloudwatch/
│   ├── cloudwatch_sender.py
│   ├── log_generator.py
│   ├── setup_aws_resources.py
│   └── requirements.txt
├── lambda/
│   └── log_processor.py
├── terraform/
│   ├── main.tf
│   ├── outputs.tf
│   └── variables.tf
├── deploy/
│   ├── deploy_ec2.sh
│   ├── lambda_deploy.sh
│   ├── setup_ec2.sh
│   └── nginx.conf
├── docker-compose.yml
├── generate_logs.py
├── populate_dynamodb.py
├── PROJECT_DOCUMENTATION.md
├── PROJECT_DESCRIPTION_AND_EDGE_CASES.md
└── README.md
```

---

## Getting Started

### Prerequisites

Make sure the following are installed:

- Python 3.11+
- Node.js 18+
- Docker Desktop (optional, for containerized deployment)
- AWS CLI and credentials (optional, for AWS mode)

---

## Local Development Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd aws-log-analyzer
```

### 2. Create environment variables

Create a `.env` file in the project root if needed.

Example:

```env
JWT_SECRET_KEY=local-secret-key
STORAGE_MODE=local
AWS_REGION=us-east-1
```

### 3. Install backend dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Install frontend dependencies

```bash
cd ../frontend
npm install
```

### 5. Start the backend

```bash
cd ../backend
python app.py
```

The backend will run at:

- http://127.0.0.1:5000

### 6. Start the frontend

In a new terminal:

```bash
cd frontend
npm start
```

The frontend will run at:

- http://127.0.0.1:3000

### 7. Login

Use the demo credentials:

- Username: admin
- Password: admin123

---

## Docker Deployment

### Build and run with Docker Compose

```bash
docker compose up --build -d
```

### Stop containers

```bash
docker compose down
```

### Access services

- Frontend: http://localhost:80
- Backend: http://localhost:5000

---

## AWS Deployment

The project includes deployment assets for AWS-based usage.

### AWS services used

- DynamoDB for log and alert storage
- CloudWatch Logs for log collection
- Lambda for processing
- SNS for notifications
- IAM and EC2 for infrastructure deployment

### Optional setup steps

```bash
cd cloudwatch
pip install -r requirements.txt
python setup_aws_resources.py
```

---

## API Overview

### Authentication

- POST /api/login
- Requires username and password

### Core endpoints

- GET /api/logs
- POST /api/logs
- POST /api/upload
- GET /api/alerts
- GET /api/stats
- POST /api/stats/refresh
- GET /api/health

### Example

```bash
curl http://127.0.0.1:5000/api/health
```

---

## Dashboard Features

The dashboard includes:

- total log counters,
- error and warning summaries,
- critical event counts,
- pie charts and line charts,
- log search,
- severity filters,
- upload modal,
- CSV export,
- and refresh controls.

---

## Usage Examples

### Generate sample logs

```bash
cd cloudwatch
python log_generator.py 100
```

### Upload a log file

Use the upload button in the dashboard to upload a .log, .txt, or .json file.

### Manual log entry

You can add a log directly through the API using a POST request to /api/logs.

---

## Configuration

### Environment variables

| Variable | Purpose | Default |
|---|---|---|
| JWT_SECRET_KEY | Secret key for JWT tokens | local-secret-key |
| STORAGE_MODE | local or aws | local |
| AWS_REGION | AWS region for cloud operations | us-east-1 |
| SNS_TOPIC_ARN | SNS topic ARN for alerts | none |
| SMTP_SERVER | SMTP server for email alerts | smtp.gmail.com |
| SMTP_USERNAME | SMTP username | empty |
| SMTP_PASSWORD | SMTP password | empty |
| ALERT_EMAIL | Recipient email for alerts | configured email |

---

## Edge Cases and Reliability Notes

The project already includes handling for several edge cases, including:

- invalid login attempts,
- missing auth tokens,
- unsupported file uploads,
- malformed log lines,
- missing storage files,
- AWS credential issues,
- docker daemon unavailability,
- and empty or no-result dashboards.

For a detailed breakdown, see [PROJECT_DESCRIPTION_AND_EDGE_CASES.md](PROJECT_DESCRIPTION_AND_EDGE_CASES.md).

---

## Development Notes

Recommended next improvements:

- add unit and integration tests,
- implement proper database-backed auth,
- add alert deduplication,
- improve error handling and logging,
- add rate limiting and request validation,
- and strengthen production readiness for cloud deployments.

---

## License

This project is intended for educational, demo, and internal monitoring use.

---

## Contributing

Contributions are welcome. If you improve the UI, add features, fix bugs, or document workflows, feel free to open a pull request.
| AWS_SECRET_ACCESS_KEY | AWS secret key | - |
| SNS_TOPIC_ARN | SNS topic ARN for alerts | - |
| ALERT_EMAIL | Email for SNS alerts | - |

## 🧪 Testing

### Test Log Generation
```bash
cd cloudwatch
python log_generator.py 10
```

### Test CloudWatch Integration
```bash
python cloudwatch_sender.py application.log
```

### Test API Endpoints
```bash
# Health check
curl http://localhost:5000/api/health

# Login
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

## 🔒 Security

- JWT authentication for all API endpoints
- Environment variables for sensitive data
- IAM roles for AWS resources
- HTTPS recommended for production
- Regular security updates for dependencies

## 📱 Mobile Support

The dashboard is fully responsive and works on:
- iOS devices (iPhone, iPad)
- Android devices
- Tablets
- Desktop browsers

## 🔄 Auto-Refresh

The dashboard automatically refreshes every 10 seconds to show real-time data.

## 📥 CSV Export

Download logs as CSV files from the dashboard using the "Download CSV" button.

## 🔍 Search & Filter

- **Search**: Search logs by message content or log level
- **Filter**: Filter logs by severity (INFO, WARNING, ERROR, CRITICAL)

## 🐛 Troubleshooting

### Common Issues

**DynamoDB connection error**
- Verify AWS credentials in .env file
- Check IAM permissions for DynamoDB

**Lambda not triggering**
- Verify CloudWatch subscription filter
- Check Lambda execution role permissions

**Frontend not connecting to backend**
- Check CORS configuration
- Verify backend is running on port 5000
- Check proxy settings in package.json

**SNS alerts not sending**
- Verify SNS topic ARN
- Check email subscription is confirmed
- Verify IAM permissions for SNS

## 📝 License

MIT License

## 👥 Contributing

Contributions, issues, and feature requests are welcome!

## 🙏 Acknowledgments

- AWS for cloud services
- Microverse for project inspiration
- Open source community

## 📞 Support

For support, email support@example.com or open an issue in the repository.
