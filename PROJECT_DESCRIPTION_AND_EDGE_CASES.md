# AWS Cloud Log Analyzer - Project Description and Edge Cases

## 1. Project Overview

AWS Cloud Log Analyzer is a full-stack monitoring application designed to ingest, analyze, visualize, and alert on application logs. It supports both local development workflows and AWS-native cloud deployments.

The system is intended for teams that want a lightweight alternative to large enterprise observability platforms while still being able to:

- collect log data from files or manual input,
- classify logs by severity,
- generate summary statistics,
- visualize trends and error patterns,
- raise alerts for critical issues,
- and expose the data through a web dashboard.

---

## 2. What the Project Does

### Core capabilities

- Reads log files from local storage and parses them into structured entries.
- Accepts log uploads through the web interface.
- Supports local storage mode for development and offline usage.
- Supports AWS storage mode for DynamoDB, CloudWatch, and SNS integration.
- Provides a React-based dashboard for monitoring and searching logs.
- Offers JWT-based authentication for protected API endpoints.
- Enables alert creation for CRITICAL and ERROR events.
- Supports basic refresh and statistics generation.
- Includes Docker and deployment scripts for containerized and cloud deployment.

### Intended users

- Developers monitoring local application output.
- DevOps engineers tracking service health and incidents.
- Teams evaluating cloud-based observability without adopting a heavy platform.

---

## 3. High-Level Architecture

### Frontend

- Built with React.
- Provides login and dashboard views.
- Displays charts, stats, alerts, search controls, and file upload.
- Uses Axios for API communication and localStorage for auth tokens.

### Backend

- Built with Flask.
- Exposes REST endpoints for authentication, uploads, logs, alerts, stats, and health checks.
- Supports two storage modes:
  - Local mode: JSON files and log files.
  - AWS mode: DynamoDB, CloudWatch, and SNS.

### Storage and persistence

- Local mode stores data in:
  - backend/logs/
  - backend/local_storage/alerts.json
  - backend/local_storage/stats.json
- AWS mode relies on DynamoDB tables such as CloudLogs, CloudAlerts, and CloudStats.

### Notification layer

- The notification service can create alert records and optionally send email or SMS notifications.
- In local mode it persists alerts to a JSON file.
- In AWS mode it stores alerts in DynamoDB and can publish SNS alerts.

---

## 4. Main Application Flow

### 4.1 Authentication flow

1. User submits login credentials.
2. Backend validates them against a demo user store.
3. If valid, a JWT is issued and stored in the frontend.
4. The dashboard becomes accessible.

### 4.2 Log ingestion flow

1. A log file is uploaded or a log entry is generated manually.
2. The backend parses the log content.
3. The parsed entries are stored in the active storage backend.
4. Alerts are created for CRITICAL and ERROR logs.

### 4.3 Statistics and dashboard flow

1. Backend reads logs and calculates summary metrics.
2. Dashboard displays totals, warnings, errors, and critical events.
3. Charts and tables are refreshed periodically.

---

## 5. Important Implementation Notes

### Supported log format

The project parses common patterns such as:

- [TIMESTAMP] LEVEL MESSAGE
- TIMESTAMP LEVEL MESSAGE

If a line does not match these patterns, it is treated as an INFO-level entry with the full raw line included as the message.

### Authentication assumption

Authentication is demo-based and not backed by a production database. The current implementation uses a hardcoded user map.

### Storage mode behavior

- Local mode is ideal for development and testing.
- AWS mode requires configured AWS credentials and the relevant resources to exist.

### Docker support

The project includes Dockerfiles and Compose configuration for frontend and backend services.

---

## 6. Edge Cases and Expected Handling

The table below summarizes the major edge cases this project may encounter and how the current implementation behaves.

| Edge Case | What can happen | Current behavior |
|---|---|---|
| Invalid login credentials | User enters wrong username/password | Returns 401 and shows an error on the login screen |
| Missing authentication token | User opens protected pages without logging in | Frontend redirects to login; backend rejects protected routes |
| Empty log file upload | User uploads a file with no readable lines | Upload succeeds but produces no parsed logs |
| Unsupported file type | User uploads a file with an unsupported extension | Backend rejects the request with a 400 error |
| File too large | Upload exceeds 16MB limit | Backend rejects request due to content-length limit |
| Missing file in upload request | Request contains no file field | Backend returns a 400 error |
| Malformed log line | Line does not match expected pattern | Backend classifies it as INFO and preserves the raw line |
| Empty log directory | No log files exist | Stats may show zero values and the dashboard stays empty but functional |
| Local storage files missing | alerts.json or stats.json do not exist | Backend creates them on startup when in local mode |
| Corrupt JSON in local storage | alerts.json or stats.json contains invalid JSON | Backend may fail when reading files unless the files are repaired |
| AWS credentials missing | AWS mode is selected without valid credentials | AWS adapter may fail when contacting DynamoDB or CloudWatch |
| DynamoDB tables missing | Required tables are not provisioned | AWS operations may fail and return empty results or throw errors |
| SNS topic ARN missing | Critical alerts are attempted without SNS configuration | SNS alert sending is skipped gracefully |
| Notification credentials missing | Email or SMS settings are incomplete | Notification sending is skipped without crashing the app |
| No logs available for stats refresh | Refresh endpoint has nothing to analyze | Stats are computed as zeros and stored |
| Search query with no matches | User searches for a term that is absent | The log list simply shows no matching entries |
| Filter by severity with no results | User selects a severity with no matching logs | Empty result state is shown in the UI |
| Backend unavailable | Flask service is down | Frontend requests fail and the dashboard may show loading or error states |
| Frontend cannot reach backend | Proxy or port configuration is incorrect | Login and dashboard requests fail and the app appears broken |
| Port conflict on frontend dev server | Port 3000 is already in use | React dev server prompts to use another port |
| Docker daemon unavailable | Docker Desktop or engine is not running | Compose commands fail and containers cannot start |
| Missing environment variables | JWT secret or other settings are absent | App still starts with defaults, but behavior may be insecure or incomplete |
| Unsupported storage mode | STORAGE_MODE is set to an unknown value | The app defaults to local behavior rather than failing hard |
| Large log file or large volume of entries | Many lines are uploaded at once | Parsing may be slower and API response time may increase |
| Special characters in log messages | Messages contain commas, quotes, or newlines | CSV export may need escaping; raw display should still work |
| Duplicate alerts | Repeated CRITICAL or ERROR logs are processed repeatedly | The system will create multiple alert entries unless deduplicated |
| Manual log entry with missing message | POST /api/logs receives no message | The backend may store empty or invalid content |
| Request body missing JSON | API endpoint expects JSON but receives invalid input | The backend may throw an exception and return a 500 error |
| Network timeout or transient AWS issue | Cloud services temporarily fail | The app should log the issue and return safe fallback values |
| Frontend auth token expired | JWT has expired or is invalid | Protected calls fail and user may need to log in again |
| Browser storage cleared | Local token is removed unexpectedly | The app may treat the user as unauthenticated |
| Empty alerts list | No alerts have been created yet | Dashboard renders an empty alert section without crashing |
| Empty stats object | Stats were never initialized | Frontend should render zeroed values rather than fail |

---

## 7. Operational Recommendations

### Recommended hardening improvements

- Add proper database-backed user management instead of a hardcoded demo user store.
- Add better validation for malformed JSON payloads.
- Add better error handling and user feedback for failed API calls.
- Add alert deduplication to prevent repeated critical alerts.
- Add log rotation and retention support.
- Add rate limiting and request validation for production use.
- Add retries for transient AWS and network failures.
- Add tests for upload, parsing, auth, and stats refresh flows.
- Improve Docker startup reliability and environment configuration.

### Production readiness notes

The current version is suitable for demos, local development, and lightweight monitoring scenarios. It is not yet a full production-grade observability platform because it lacks advanced scaling, strong persistence guarantees, and comprehensive security controls.

---

## 8. Summary

AWS Cloud Log Analyzer is a practical, lightweight monitoring solution that combines a Flask backend, a React frontend, and flexible storage options to make log analysis accessible. Its main strengths are simplicity, local-first support, AWS integration, and an easy-to-use dashboard.

The major project risks are around edge-case robustness, operational resilience, and production hardening. The current implementation handles many common scenarios reasonably well, but it would benefit from stronger validation, better fault tolerance, and more complete production safeguards.
