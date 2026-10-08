# Comprehensive File Explanations Guide

## Real-Time Linux Observability, Log Analytics & Auto-Scaling Platform

This document is the definitive architectural and engineering reference for every file across the entire repository. It details each file's **purpose**, **architectural motivation (why it was created)**, **functional mechanics (what it does)**, **key classes/functions**, and **subsystem dependencies**.

---

## Table of Contents

1. [Architectural Overview & Repository Layout](#1-architectural-overview--repository-layout)
2. [Root-Level Configuration & Utility Scripts](#2-root-level-configuration--utility-scripts)
3. [Backend Core & Initialization](#3-backend-core--initialization)
4. [Backend Data Models (backend/models/)](#4-backend-data-models-backendmodels)
5. [Backend Storage Subsystem & Factory](#5-backend-storage-subsystem--factory)
6. [Backend API Blueprints & Routing (backend/routes/)](#6-backend-api-blueprints--routing-backendroutes)
7. [Backend Autonomous Scaling & Decision Engine (backend/scaling/)](#7-backend-autonomous-scaling--decision-engine-backendscaling)
8. [Backend Hybrid VM Provisioners (backend/provisioners/)](#8-backend-hybrid-vm-provisioners-backendprovisioners)
9. [Backend Streaming Bus & Sliding Window Analytics (backend/streaming/)](#9-backend-streaming-bus--sliding-window-analytics-backendstreaming)
10. [Backend Linux Agents & Telemetry Collectors (backend/agents/)](#10-backend-linux-agents--telemetry-collectors-backendagents)
11. [Backend Local Storage Schemas & Persistence (backend/local_storage/)](#11-backend-local-storage-schemas--persistence-backendlocal_storage)
12. [Backend Integration Test Suite](#12-backend-integration-test-suite)
13. [Frontend Application Architecture (frontend/)](#13-frontend-application-architecture-frontend)
14. [CloudWatch & Serverless Processing (cloudwatch/ & lambda/)](#14-cloudwatch--serverless-processing-cloudwatch--lambda)
15. [Infrastructure as Code & Deployment Automation (terraform/ & deploy/)](#15-infrastructure-as-code--deployment-automation-terraform--deploy)
16. [Documentation Catalog](#16-documentation-catalog)

---

## 1. Architectural Overview & Repository Layout

The platform integrates high-resolution telemetry, stream analytics, autonomous auto-scaling, and dual-layer provisioning with legacy log ingestion. The codebase is organized into discrete, highly cohesive modules:

```
AWS_LogAnalyzer/
├── docker-compose.yml                     # Multi-container orchestration (Backend + Frontend)
├── generate_logs.py                       # CLI synthetic log generator
├── populate_dynamodb.py                   # AWS DynamoDB seeding utility
├── FILE_EXPLANATIONS.md                   # This comprehensive file guide
├── PROJECT_DESCRIPTION_AND_EDGE_CASES.md  # Failure modes and edge cases reference
├── PROJECT_DOCUMENTATION.md               # Primary technical manual and architecture guide
├── README.md                              # Developer onboarding and quickstart guide
│
├── backend/                               # Flask Python backend
│   ├── app.py                             # Main Flask application and server entrypoint
│   ├── local_storage_manager.py           # Thread-safe atomic JSON persistence engine
│   ├── storage_factory.py                 # Abstract storage provider factory
│   ├── aws_storage_adapter.py             # DynamoDB and CloudWatch SDK adapter
│   ├── notification_service.py            # Local, Email, SMS, and SNS alerting engine
│   ├── local_log_reader.py                # Legacy raw log parser and reader
│   ├── dummy_log_generator.py             # Synthetic log stream generator
│   ├── test_auto_scaling.py               # End-to-end integration test suite
│   ├── requirements.txt                   # Python package dependencies
│   ├── Dockerfile                         # Production backend container image
│   ├── .env.example                       # Environment configuration template
│   │
│   ├── models/                            # Domain entities and schemas
│   │   └── entities.py                    # Host, Metric, ScalingEvent, Incident, ProvisioningTask
│   │
│   ├── routes/                            # Modular Flask REST API Blueprints
│   │   ├── hosts_bp.py                    # Host registration, inventory, and heartbeats
│   │   ├── metrics_bp.py                  # Telemetry ingestion, real-time query, and aggregation
│   │   ├── scaling_bp.py                  # Auto-scaling policies, triggers, history, and status
│   │   └── health_bp.py                   # Component health probes and diagnostics
│   │
│   ├── scaling/                           # Auto-scaling decision and orchestration engine
│   │   ├── decision_engine.py             # Rule evaluation, hysteresis, cooldown, and limits
│   │   ├── scaling_controller.py          # Asynchronous provisioning worker pool & dispatcher
│   │   └── workload_scheduler.py          # Least-utilized healthy VM workload router
│   │
│   ├── provisioners/                      # Dual-layer hypervisor orchestration
│   │   ├── base.py                        # Abstract base provisioner interface
│   │   ├── vmware_provisioner.py          # Layer 1: VMware Workstation / vSphere REST FSM
│   │   ├── aws_provisioner.py             # Layer 2: AWS EC2 Boto3 SDK provisioner
│   │   └── factory.py                     # Hypervisor provisioner factory
│   │
│   ├── streaming/                         # High-throughput event streaming & sliding window
│   │   ├── event_stream.py                # Kafka / Redpanda producer with in-memory ring buffer
│   │   └── stream_processor.py            # 5-minute sliding window time-series aggregator
│   │
│   ├── agents/                            # Linux host metrics collection & boot-time scripts
│   │   ├── node_exporter_collector.py     # Prometheus Node Exporter metrics scraper
│   │   ├── fluent_bit_parser.py           # Fluent Bit structured log parser
│   │   └── vm_template_init.sh            # cloud-init guest bootstrap shell script
│   │
│   └── local_storage/                     # Atomic JSON persistence directory
│       ├── hosts.json                     # Registered Linux hosts and state
│       ├── resource_metrics.json          # Hardware telemetry time-series records
│       ├── scaling_events.json            # SCALE_OUT / SCALE_IN audit logs
│       ├── incidents.json                 # Unhealthy node and failure incident records
│       ├── provisioning.json              # Asynchronous provisioning task FSM states
│       ├── alerts.json                    # Critical log alerts
│       └── stats.json                     # Cluster-wide log statistics
│
├── frontend/                              # React 18 single-page application
│   ├── public/index.html                  # HTML5 application shell
│   ├── src/
│   │   ├── index.js                       # React DOM initialization
│   │   ├── index.css                      # Tailwind directives and CSS variables
│   │   ├── App.js                         # Root React component, auth state & dark theme
│   │   ├── App.css                        # Global layout overrides and animations
│   │   └── components/
│   │       ├── Dashboard.js               # Unified dashboard with tabbed navigation
│   │       ├── LinuxObservability.js      # Host metrics, VM table, charts, scaling controls
│   │       └── Login.js                   # JWT authentication UI
│   ├── package.json                       # NPM dependencies and scripts
│   ├── tailwind.config.js                 # Custom color themes and responsive breakpoints
│   ├── postcss.config.js                  # PostCSS plugins (Tailwind, Autoprefixer)
│   ├── nginx.conf                         # Production SPA web server configuration
│   └── Dockerfile                         # Multi-stage production container build
│
├── cloudwatch/                            # AWS CloudWatch log shipping tools
│   ├── cloudwatch_sender.py               # CloudWatch Logs batch & tail publisher
│   ├── log_generator.py                   # Continuous CloudWatch-format log generator
│   ├── setup_aws_resources.py             # Automated AWS resource setup script
│   └── requirements.txt                   # CloudWatch script dependencies
│
├── lambda/                                # AWS Serverless event processing
│   ├── log_processor.py                   # AWS Lambda log parser and DynamoDB/SNS router
│   ├── log_processor.zip                  # Ready-to-deploy zipped Lambda artifact
│   └── requirements.txt                   # Lambda runtime dependencies
│
├── terraform/                             # Declarative Infrastructure as Code
│   ├── main.tf                            # EC2, DynamoDB, SNS, IAM, and Security Groups
│   ├── variables.tf                       # Terraform input parameters
│   └── outputs.tf                         # Infrastructure endpoints and resource ARNs
│
└── deploy/                                # Shell scripts for cloud provisioning
    ├── deploy_ec2.sh                      # EC2 git pull and container restart script
    ├── setup_ec2.sh                       # Initial EC2 Docker environment bootstrap
    ├── lambda_deploy.sh                   # Linux/macOS Lambda packager and updater
    ├── lambda_deploy.ps1                  # Windows PowerShell Lambda packager
    ├── lambda-policy.json                 # IAM permissions policy for Lambda execution
    ├── lambda-trust-policy.json           # IAM trust relationship policy for Lambda
    └── nginx.conf                         # EC2 reverse proxy configuration
```

---

## 2. Root-Level Configuration & Utility Scripts

### `docker-compose.yml`
- **Purpose**: Multi-container orchestration definition for running the complete frontend and backend environment with a single command.
- **Why Created**: Eliminates configuration drift across development, staging, and production environments by guaranteeing consistent network routing, volume mounts, and environment variable bindings.
- **What It Does**:
  - Configures the `backend` service: Builds `backend/Dockerfile`, exposes port `5000:5000`, maps local storage volumes (`./backend/local_storage:/app/local_storage` and `./backend/logs:/app/logs`), and sets environment variables (`STORAGE_MODE=local`, `FLASK_ENV=production`).
  - Configures the `frontend` service: Builds `frontend/Dockerfile`, exposes port `80:80`, and connects to the backend over the shared Docker bridge network `log-analyzer-network`.
  - Configures container restart policies (`restart: unless-stopped`).

### `generate_logs.py`
- **Purpose**: Standalone CLI script for generating synthetic application log files with realistic timestamps, components, and severity levels.
- **Why Created**: Enables rapid functional testing of log ingestion, upload processing, and severity filtering without requiring an external running production application.
- **What It Does**:
  - Synthesizes formatted log lines matching the standard pattern: `[YYYY-MM-DD HH:MM:SS] [LEVEL] [COMPONENT] Message`.
  - Randomly selects from realistic messages across `INFO`, `WARNING`, `ERROR`, and `CRITICAL` levels.
  - Writes directly into `backend/logs/application.log` or a custom output path.

### `populate_dynamodb.py`
- **Purpose**: AWS DynamoDB database seeding script.
- **Why Created**: Allows developers and CI/CD pipelines to pre-populate AWS tables with realistic log entries, alerts, and metrics to validate the AWS-backed operational mode.
- **What It Does**:
  - Connects to AWS DynamoDB using Boto3.
  - Inserts batch records into `CloudLogs`, `CloudAlerts`, and `CloudStats`.
  - Validates partition key (`LogId`, `AlertId`) and sort key schemas, handling provisioned throughput constraints with retries.

### `.gitignore`
- **Purpose**: Git version control exclusion list.
- **Why Created**: Prevents sensitive API credentials, build artifacts, local database dumps, and virtual environments from accidentally being committed to public repositories.
- **What It Does**:
  - Ignores `.env`, `__pycache__/`, `*.pyc`, `venv/`, `node_modules/`, `build/`, `*.log`, and temporary local storage backups.

---

## 3. Backend Core & Initialization

### `backend/app.py`
- **Purpose**: Main Flask application factory, server entrypoint, and central coordinator.
- **Why Created**: Serves as the central API gateway that binds all route blueprints, configures middleware, initializes the storage layer, and manages security policies.
- **What It Does**:
  - Instantiates the Flask WSGI application with CORS support (`Flask-CORS`).
  - Configures JWT authentication (`PyJWT` / `flask-jwt-extended`) with secret key validation and expiration handling.
  - Automatically initializes local storage directories (`backend/local_storage/` and `backend/logs/`) on startup.
  - Registers modular REST blueprints:
    - `/api/hosts` $\rightarrow$ `hosts_bp`
    - `/api/metrics` $\rightarrow$ `metrics_bp`
    - `/api/scaling` $\rightarrow$ `scaling_bp`
    - `/api/health` $\rightarrow$ `health_bp`
  - Maintains full backward compatibility with legacy endpoints:
    - `POST /api/login`: Validates user credentials and issues JWT bearer tokens.
    - `GET /api/logs`: Retrieves parsed log records with level filtering and search queries.
    - `POST /api/logs`: Ingests a single structured log entry.
    - `POST /api/upload`: Handles multipart log file uploads with 16MB file limit enforcement.
    - `GET /api/alerts`: Retrieves active system alerts.
    - `GET /api/stats` and `POST /api/stats/refresh`: Calculates and refreshes aggregate log metrics.
- **Key Inter-Module Relations**: Imports from `backend/routes/`, `backend/local_storage_manager.py`, `backend/storage_factory.py`, and `backend/notification_service.py`.

### `backend/requirements.txt`
- **Purpose**: Python package dependency manifest.
- **Why Created**: Ensures deterministic, reproducible Python virtual environments across bare metal, Docker containers, and CI/CD pipelines.
- **What It Does**:
  - Specifies required packages: `Flask`, `Flask-CORS`, `PyJWT`, `boto3`, `python-dotenv`, `gunicorn`, `requests`, and `kafka-python`.

### `backend/Dockerfile`
- **Purpose**: Container definition for the Python Flask backend.
- **Why Created**: Packages the Python runtime, system dependencies, and application code into a lightweight, deployable container image.
- **What It Does**:
  - Uses `python:3.11-slim` base image for minimal attack surface and fast startup.
  - Installs compilation dependencies (`gcc`, `curl`).
  - Installs requirements via `pip install --no-cache-dir`.
  - Exposes port `5000`.
  - Starts the application using Gunicorn WSGI server (`gunicorn --bind 0.0.0.0:5000 app:app --workers 4 --threads 2`).

### `backend/.env.example`
- **Purpose**: Environment configuration template.
- **Why Created**: Documents all required and optional environment variables for new developers and automated deployment scripts.
- **What It Does**:
  - Defines `FLASK_ENV`, `PORT`, `JWT_SECRET_KEY`, `STORAGE_MODE`, `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `SNS_TOPIC_ARN`, `KAFKA_BOOTSTRAP_SERVERS`, `HYPERVISOR_TYPE`, and `AUTOSCALING_DRY_RUN`.

---

## 4. Backend Data Models (`backend/models/`)

### `backend/models/entities.py`
- **Purpose**: Strongly typed domain models and entity definitions for the observability and scaling ecosystem.
- **Why Created**: Eliminates ad-hoc dictionaries across the backend, establishing strict data contracts, validation rules, and JSON serialization methods for all platform entities.
- **Key Classes**:
  - `Host`: Represents a monitored Linux virtual machine or bare-metal host. Fields: `host_id`, `hostname`, `ip_address`, `cpu_cores`, `memory_gb`, `os_info`, `hypervisor`, `state` (`PENDING`, `RUNNING`, `DRAINING`, `STOPPED`, `TERMINATED`), `is_healthy`, `last_heartbeat`, `tags`. Includes `.to_dict()` and `.from_dict()` methods.
  - `Metric`: Represents a discrete time-series hardware sample. Fields: `metric_id`, `host_id`, `timestamp`, `cpu_percent`, `memory_percent`, `disk_percent`, `network_rx_kbps`, `network_tx_kbps`, `load_1m`, `process_count`, `error_rate`.
  - `ScalingEvent`: Represents an audit log of an auto-scaling evaluation or execution. Fields: `event_id`, `timestamp`, `action` (`SCALE_OUT`, `SCALE_IN`, `NO_ACTION`), `trigger_reason`, `target_host_id`, `metrics_snapshot`, `status` (`SUCCESS`, `FAILED`, `SIMULATED`), `cooldown_remaining`.
  - `Incident`: Represents an anomaly, threshold breach, or host outage. Fields: `incident_id`, `timestamp`, `host_id`, `severity` (`CRITICAL`, `WARNING`), `title`, `description`, `acknowledged`.
  - `ProvisioningTask`: Represents an asynchronous VM provisioning or de-provisioning lifecycle task. Fields: `task_id`, `host_id`, `action`, `state` (`REQUESTED`, `CREATING`, `CLONING`, `CONFIGURING_IP`, `RUNNING`, `FAILED`), `progress_pct`, `created_at`, `updated_at`, `error_message`.
- **Key Inter-Module Relations**: Imported by all routes, provisioners, decision engines, and storage managers.

---

## 5. Backend Storage Subsystem & Factory

### `backend/local_storage_manager.py`
- **Purpose**: High-reliability, thread-safe, atomic JSON persistence manager.
- **Why Created**: Guarantees zero data loss or corruption during concurrent writes without requiring an external SQL database in local development or edge environments.
- **What It Does**:
  - Uses `threading.Lock` to synchronize read/write access across multiple worker threads.
  - Implements atomic file writes: serializes data, writes to a temporary file (`<filename>.tmp`), flushes and syncs to disk (`os.fsync`), and performs an atomic rename (`os.replace`).
  - Implements automatic corruption recovery: if `json.load()` fails due to an incomplete write or power outage, it renames the corrupted file to `<filename>.corrupt.<timestamp>` and re-initializes a valid empty structure.
  - Provides CRUD methods for hosts, metrics, scaling events, incidents, provisioning tasks, and legacy alerts.

### `backend/storage_factory.py`
- **Purpose**: Factory pattern implementation for abstracting storage providers.
- **Why Created**: Enables seamless switching between local file-based storage and AWS cloud storage via a single environment variable (`STORAGE_MODE=local` vs. `STORAGE_MODE=aws`).
- **What It Does**:
  - Inspects `STORAGE_MODE`.
  - Returns either an instance of `LocalStorageManager` or `AWSStorageAdapter`.
  - Ensures callers interact with a uniform API interface regardless of underlying persistence technology.

### `backend/aws_storage_adapter.py`
- **Purpose**: AWS cloud persistence adapter utilizing DynamoDB, CloudWatch, and SNS.
- **Why Created**: Enables enterprise cloud deployments where metrics, logs, and alerts must be stored in managed, auto-scaling AWS data stores.
- **What It Does**:
  - Connects to DynamoDB using Boto3 resource interfaces.
  - Manages operations on `CloudLogs`, `CloudAlerts`, `CloudStats`, `Hosts`, and `ResourceMetrics` tables.
  - Publishes critical security and capacity alerts to AWS SNS topics.
  - Implements automatic retries with exponential backoff for DynamoDB throttling.

### `backend/notification_service.py`
- **Purpose**: Centralized alerting and notification dispatcher.
- **Why Created**: Decouples alert generation logic from delivery channels, supporting local in-app alerts, email (SMTP), SMS (Twilio), and AWS SNS.
- **What It Does**:
  - Evaluates alert severity.
  - In local mode, appends alert records to `backend/local_storage/alerts.json`.
  - In AWS mode, dispatches JSON payloads to configured SNS Topic ARNs.
  - Handles network timeouts and missing credential edge cases gracefully without blocking main application flows.

### `backend/local_log_reader.py`
- **Purpose**: High-performance local log file parser and aggregator.
- **Why Created**: Provides core parsing capabilities for reading and querying raw `.log` and `.txt` files stored in `backend/logs/`.
- **What It Does**:
  - Reads raw log files line-by-line using streaming iterators to prevent high memory usage.
  - Parses timestamps and severity levels (`CRITICAL`, `ERROR`, `WARNING`, `INFO`) using compiled regular expressions.
  - Provides in-memory search, keyword filtering, and pagination.

### `backend/dummy_log_generator.py`
- **Purpose**: Background synthetic log generator service.
- **Why Created**: Generates dynamic log entries in development environments to populate charts and alert feeds.
- **What It Does**:
  - Runs in a background daemon thread.
  - Emits representative logs for simulated application components (AuthService, DatabasePool, PaymentGateway, APIRouter) at configurable intervals.

---

## 6. Backend API Blueprints & Routing (`backend/routes/`)

### `backend/routes/hosts_bp.py`
- **Purpose**: REST API Blueprint for Linux host inventory management and health heartbeats.
- **Why Created**: Provides dedicated endpoints for host registration, heartbeat watchdogs, and inventory status reporting.
- **Key Endpoints**:
  - `GET /api/hosts`: Lists all registered hosts with optional state and health filtering.
  - `POST /api/hosts/register`: Registers a new host or updates an existing host idempotently.
  - `POST /api/hosts/<host_id>/heartbeat`: Updates the `last_heartbeat` timestamp. Evaluates silence: flags `DEGRADED` if silent > 90s, `OFFLINE` if silent > 180s.
  - `GET /api/hosts/<host_id>`: Returns detailed metadata for a single host.
  - `DELETE /api/hosts/<host_id>`: Deregisters a host from the active inventory.

### `backend/routes/metrics_bp.py`
- **Purpose**: REST API Blueprint for hardware metric telemetry ingestion and querying.
- **Why Created**: Handles high-throughput metric ingestion from agent daemons and serves time-series data to frontend visual charts.
- **Key Endpoints**:
  - `POST /api/metrics/ingest`: Accepts real-time hardware telemetry payloads, forwards to the `EventStream`, and stores in persistence.
  - `GET /api/metrics/latest`: Returns the most recent hardware metrics for all active hosts.
  - `GET /api/metrics/history/<host_id>`: Returns time-series metric history for a host over a requested time range (e.g. 1h, 6h, 24h).
  - `GET /api/metrics/cluster-summary`: Returns cluster-wide average CPU, memory, disk, network, and active VM counts.

### `backend/routes/scaling_bp.py`
- **Purpose**: REST API Blueprint for auto-scaling policies, manual provisioning triggers, and audit history.
- **Why Created**: Exposes control plane operations for inspecting auto-scaling configurations, viewing scaling decisions, and executing manual scale-out/scale-in overrides.
- **Key Endpoints**:
  - `GET /api/scaling/policy`: Returns current auto-scaling thresholds, cooldown settings, and capacity boundaries.
  - `POST /api/scaling/policy`: Dynamically updates scaling policy parameters at runtime.
  - `POST /api/scaling/evaluate`: Manually triggers a cluster evaluation by the `DecisionEngine`.
  - `POST /api/scaling/scale-out`: Manually commands the launch of a new VM instance.
  - `POST /api/scaling/scale-in`: Manually commands the graceful termination of an underutilized VM.
  - `GET /api/scaling/events`: Returns the historical log of scaling actions and simulation audits.
  - `GET /api/scaling/tasks/<task_id>`: Polls the FSM progress of an asynchronous provisioning task.

### `backend/routes/health_bp.py`
- **Purpose**: REST API Blueprint for system health probes and component diagnostics.
- **Why Created**: Enables Docker, Kubernetes, and load balancers to perform liveness and readiness health checks.
- **Key Endpoints**:
  - `GET /api/health`: Returns overall system health (`UP` / `DEGRADED`), uptime, storage mode, and component status (Storage, Event Bus, Decision Engine, Provisioner).

---

## 7. Backend Autonomous Scaling & Decision Engine (`backend/scaling/`)

### `backend/scaling/decision_engine.py`
- **Purpose**: Core mathematical and rule-based decision engine for autonomous auto-scaling.
- **Why Created**: Translates raw hardware metrics into intelligent, stable scaling decisions while preventing destructive failure modes such as flapping and premature spike reactions.
- **What It Does**:
  - Aggregates sustained metrics from the `SlidingWindowProcessor`.
  - Evaluates cluster-wide thresholds:
    - **Scale-Out Trigger**: Cluster average CPU > 80% OR Memory > 85%.
    - **Scale-In Trigger**: Cluster average CPU < 25% AND Memory < 30%.
  - Enforces operational constraints:
    - **Cooldown Lock**: Rejects scaling actions if fewer than 300 seconds have elapsed since the prior event.
    - **Capacity Boundaries**: Strictly limits cluster size between `min_vms` (default: 2) and `max_vms` (default: 8).
    - **Dry-Run Mode**: Evaluates rules, logs decisions, and audits simulation records without invoking hypervisor provisioning.
- **Key Methods**: `evaluate_cluster()`, `should_scale_out()`, `should_scale_in()`, `select_scale_in_candidate()`.

### `backend/scaling/scaling_controller.py`
- **Purpose**: Asynchronous task executor and provisioning orchestrator.
- **Why Created**: Prevents synchronous HTTP requests from blocking during long-running VM operations (cloning, booting, IP assignment).
- **What It Does**:
  - Manages a background `concurrent.futures.ThreadPoolExecutor`.
  - Spawns asynchronous worker threads for `provision_instance()` and `deprovision_instance()`.
  - Tracks task lifecycle within `ProvisioningTask` records, updating progress percentage and FSM states in storage.
  - Invokes the appropriate provisioner via `ProvisionerFactory`.

### `backend/scaling/workload_scheduler.py`
- **Purpose**: Intelligent compute workload dispatcher and load balancer.
- **Why Created**: Routes incoming background tasks and batch jobs to the optimal Linux host based on real-time resource availability.
- **What It Does**:
  - Queries active, healthy hosts (`state == 'RUNNING'` and `is_healthy == True`).
  - Computes composite utilization score for each candidate node:
    $$\text{Score} = (\text{CPU}\% \times 0.5) + (\text{Memory}\% \times 0.3) + (\text{Disk}\% \times 0.2)$$
  - Selects and returns the least-utilized host.
  - Handles edge cases where zero healthy hosts are available by triggering an emergency scale-out event.

---

## 8. Backend Hybrid VM Provisioners (`backend/provisioners/`)

### `backend/provisioners/base.py`
- **Purpose**: Abstract Base Class defining the interface contract for all hypervisor provisioners.
- **Why Created**: Enforces a strict interface so the scaling controller can operate uniformly across VMware, AWS, or future hypervisor backends (GCP, Azure, Proxmox).
- **Abstract Methods**:
  - `provision_instance(hostname, cpu, ram_mb, tags) -> Host`: Boots a new VM instance.
  - `deprovision_instance(host_id) -> bool`: Gracefully stops and destroys a VM instance.
  - `get_instance_status(host_id) -> str`: Queries hypervisor for instance state.

### `backend/provisioners/vmware_provisioner.py`
- **Purpose**: Layer 1 provisioner orchestrating VMware Workstation / vSphere via `vmrun` and REST APIs.
- **Why Created**: Enables rapid, low-cost local development and private datacenter infrastructure management.
- **What It Does**:
  - Implements a complete Finite State Machine: `REQUESTED` $\rightarrow$ `CREATING` $\rightarrow$ `CLONING` $\rightarrow$ `CONFIGURING_IP` $\rightarrow$ `RUNNING`.
  - Performs linked clones from golden base templates (`ubuntu-22.04-template.vmx`) using `vmrun clone`.
  - Automates VM power operations (`start`, `stop`, `reset`).
  - Queries VMware Guest Tools for dynamic DHCP IP assignment.
  - Implements rollback and cleanup routines on failure.

### `backend/provisioners/aws_provisioner.py`
- **Purpose**: Layer 2 provisioner orchestrating AWS EC2 cloud instances via Boto3.
- **Why Created**: Enables automated cloud elasticity and multi-region scale-out when local capacity is saturated.
- **What It Does**:
  - Connects to AWS EC2 via Boto3 client and resource interfaces.
  - Launches EC2 instances using configured Launch Templates or explicit AMI parameters.
  - Injects `cloud-init` user data scripts (`vm_template_init.sh`) for automated daemon installation.
  - Attaches standard resource tags: `Project=LinuxObservabilityAutoScaling`, `ManagedBy=DecisionEngine`.
  - Polls instance status until `running` and public/private IP addresses are confirmed.

### `backend/provisioners/factory.py`
- **Purpose**: Factory for instantiating hypervisor provisioners.
- **Why Created**: Decouples configuration inspection from provisioner consumer logic.
- **What It Does**:
  - Inspects `HYPERVISOR_TYPE` environment variable (`vmware` vs. `aws`).
  - Instantiates and returns the configured singleton provisioner.

---

## 9. Backend Streaming Bus & Sliding Window Analytics (`backend/streaming/`)

### `backend/streaming/event_stream.py`
- **Purpose**: High-throughput real-time event streaming bus.
- **Why Created**: Decouples metric producers (Node Exporter, Fluent Bit) from consumers (Sliding Window Processor, Storage, Alerting) to prevent ingestion backpressure.
- **What It Does**:
  - Connects to an external Apache Kafka or Redpanda broker cluster on topic `host-metrics-raw`.
  - Implements a thread-safe in-memory ring buffer (capacity: 10,000 items) that automatically activates if Kafka is unavailable or disconnected.
  - Provides pub/sub interfaces: `publish_metric()`, `publish_event()`, `consume()`.

### `backend/streaming/stream_processor.py`
- **Purpose**: Real-time sliding window statistical aggregator.
- **Why Created**: Eliminates metric noise and false-positive spikes by calculating continuous rolling statistics over a 5-minute sliding window.
- **What It Does**:
  - Maintains a time-indexed queue of metric samples per host.
  - Automatically evicts samples older than 300 seconds (5 minutes).
  - Calculates rolling metrics: mean CPU, sustained memory utilization, 95th percentile ($P95$) network throughput, and anomaly indicators.
  - Provides `get_window_stats(host_id)` for consumption by the `DecisionEngine`.

---

## 10. Backend Linux Agents & Telemetry Collectors (`backend/agents/`)

### `backend/agents/node_exporter_collector.py`
- **Purpose**: Prometheus Node Exporter metric scraper and parser.
- **Why Created**: Ingests industry-standard Linux hardware telemetry directly from Prometheus Node Exporter daemons running on port `9100`.
- **What It Does**:
  - Connects via HTTP to `http://<host_ip>:9100/metrics`.
  - Parses OpenMetrics text format for key gauges:
    - `node_cpu_seconds_total` (calculates user, system, iowait, and idle CPU percentages).
    - `node_memory_MemTotal_bytes` and `node_memory_MemAvailable_bytes` (calculates true memory consumption).
    - `node_filesystem_free_bytes` (calculates disk usage).
    - `node_network_receive_bytes_total` and `node_network_transmit_bytes_total`.
    - `node_load1` and `node_procs_running`.
  - Formats data into a `Metric` entity and posts it to `/api/metrics/ingest`.

### `backend/agents/fluent_bit_parser.py`
- **Purpose**: Fluent Bit log shipping parser.
- **Why Created**: Ingests high-frequency system and application logs streamed from Fluent Bit agent daemons running on Linux hosts.
- **What It Does**:
  - Parses structured JSON and standard syslog inputs.
  - Normalizes timestamps to ISO 8601 UTC.
  - Extracts severity levels using regex heuristics.
  - Routes error and critical events directly to the alerting pipeline.

### `backend/agents/vm_template_init.sh`
- **Purpose**: Cloud-init bootstrap script for freshly provisioned Linux virtual machines.
- **Why Created**: Automates the installation, configuration, and service startup of telemetry agents during the initial VM boot sequence.
- **What It Does**:
  - Updates apt package indexes.
  - Downloads and installs Prometheus Node Exporter as a `systemd` service.
  - Installs and configures Fluent Bit to tail `/var/log/syslog` and `/var/log/auth.log`.
  - Registers the new VM with the central control plane via `POST /api/hosts/register`.
  - Starts recurring heartbeats via cron or systemd timer.

---

## 11. Backend Local Storage Schemas & Persistence (`backend/local_storage/`)

### `backend/local_storage/hosts.json`
- **Purpose**: Persistent inventory of all registered Linux virtual machines and bare-metal hosts.
- **Structure**: JSON array of `Host` objects including IP addresses, CPU cores, RAM, lifecycle state (`RUNNING`, `DRAINING`, etc.), and last heartbeat timestamp.

### `backend/local_storage/resource_metrics.json`
- **Purpose**: Time-series log of all ingested hardware metrics across all monitored hosts.
- **Structure**: JSON array of `Metric` objects containing timestamp, host ID, CPU %, memory %, disk %, network I/O, load average, and process counts.

### `backend/local_storage/scaling_events.json`
- **Purpose**: Immutable audit log of all auto-scaling decisions, rule evaluations, and provisioning executions.
- **Structure**: JSON array of `ScalingEvent` objects detailing timestamp, action (`SCALE_OUT`, `SCALE_IN`, `NO_ACTION`), trigger reason, snapshot metrics, and status.

### `backend/local_storage/incidents.json`
- **Purpose**: Incident log recording host outages, watchdog expirations, and hypervisor provisioning failures.
- **Structure**: JSON array of `Incident` objects containing timestamp, host ID, severity, title, detailed description, and acknowledgment state.

### `backend/local_storage/provisioning.json`
- **Purpose**: State store for tracking asynchronous VM provisioning tasks and their FSM transitions.
- **Structure**: JSON array of `ProvisioningTask` objects tracking task ID, action, state (`CLONING`, `CONFIGURING_IP`, `RUNNING`, `FAILED`), and progress percentage.

### `backend/local_storage/alerts.json`
- **Purpose**: Legacy alert store for high-severity log events (`CRITICAL`, `ERROR`).
- **Structure**: JSON array of alert records including log message, severity, timestamp, and notification dispatch status.

### `backend/local_storage/stats.json`
- **Purpose**: Aggregated cluster-wide log statistics.
- **Structure**: JSON object tracking total logs, error counts, warning counts, critical counts, and last refresh timestamp.

---

## 12. Backend Integration Test Suite

### `backend/test_auto_scaling.py`
- **Purpose**: Comprehensive end-to-end integration and regression test suite.
- **Why Created**: Validates all layers of the observability and auto-scaling platform in a single automated test run without external dependencies.
- **What It Tests**:
  1. **Phase 1**: Host Registration and Inventory Persistence (`POST /api/hosts/register`).
  2. **Phase 2**: High-Resolution Metric Ingestion (`POST /api/metrics/ingest`).
  3. **Phase 3**: Event Stream & Sliding Window Aggregation (`get_window_stats()`).
  4. **Phase 4**: Decision Engine Under Sustained High Load (verifies `SCALE_OUT` trigger).
  5. **Phase 5**: Cooldown Lock Enforcement (verifies subsequent evaluation blocked during cooldown).
  6. **Phase 6**: Least-Utilized Workload Scheduling (verifies routing to healthiest host).
  7. **Phase 7**: Transient Spike Rejection (verifies single spike does not trigger scale-out).
  8. **Phase 8**: Host Heartbeat Watchdog & Incident Generation (verifies `DEGRADED` and `OFFLINE` transitions).

---

## 13. Frontend Application Architecture (`frontend/`)

### `frontend/src/App.js`
- **Purpose**: Root React component, top-level state manager, and routing controller.
- **Why Created**: Manages global application state, authentication tokens, dark/light theme switching, and top-level navigation.
- **What It Does**:
  - Reads stored JWT tokens from browser `localStorage`.
  - Renders `Login` component if unauthenticated.
  - Renders `Dashboard` component if authenticated.
  - Manages dark mode class toggles on the root document element.

### `frontend/src/components/Dashboard.js`
- **Purpose**: Unified main dashboard shell with tabbed navigation.
- **Why Created**: Seamlessly merges the new **Linux Observability & Auto-Scaling** views with the legacy **Log Analytics & Severity Analysis** views into a single unified dashboard.
- **What It Does**:
  - Provides tab navigation: **Linux Observability & Scaling** vs. **Log Analytics & Ingestion**.
  - Renders `LinuxObservability` component under the observability tab.
  - Renders summary statistics cards, interactive log charts (Pie, Line), recent logs table, search filters, and file upload modal under the log analytics tab.
  - Implements auto-refresh interval polling every 10 seconds.
  - Provides CSV log export functionality.

### `frontend/src/components/LinuxObservability.js`
- **Purpose**: Feature-rich, real-time Linux infrastructure observability and auto-scaling control panel.
- **Why Created**: Delivers a modern UI for monitoring host health, viewing live resource metrics, inspecting scaling events, and executing manual scale-out/scale-in overrides.
- **Key UI Sections**:
  - **Cluster Overview Cards**: Displays Active VMs, Average CPU %, Average Memory %, Network Throughput, and Active Incidents with color-coded health badges.
  - **Monitored Hosts & VM Table**: Displays host ID, hostname, IP address, OS, CPU cores, RAM, lifecycle status badges (`RUNNING`, `DRAINING`, `OFFLINE`), and quick actions.
  - **Live Resource Utilization Charts**: Renders real-time CPU and Memory time-series line charts comparing multiple hosts simultaneously.
  - **Auto-Scaling Control Panel**: Displays current policy thresholds, cooldown countdown, and buttons for manual **Scale Out (+1 VM)** and **Scale In (-1 VM)** actions.
  - **Scaling Audit & Incident Log**: Displays real-time audit feed of scaling decisions, rule triggers, and host health incidents.

### `frontend/src/components/Login.js`
- **Purpose**: User authentication page component.
- **Why Created**: Provides an interface for logging into the platform using username and password credentials.
- **What It Does**:
  - Submits credentials to `POST /api/login`.
  - Stores returned JWT token in browser `localStorage`.
  - Displays validation errors for invalid credentials.

### `frontend/src/index.js`
- **Purpose**: React application DOM entrypoint.
- **What It Does**: Bootstraps the React virtual DOM into the root `#root` container using React 18 `createRoot`.

### `frontend/src/index.css` & `frontend/src/App.css`
- **Purpose**: Global CSS styling, Tailwind imports, custom animations, and CSS variables.
- **What It Does**: Declares Tailwind directives (`@tailwind base`, `@tailwind components`, `@tailwind utilities`), custom scrollbars, glowing status indicators, and glassmorphic card styles.

### `frontend/package.json`
- **Purpose**: Frontend dependency and script configuration.
- **What It Does**: Declares dependencies (`react`, `react-dom`, `axios`, `chart.js`, `react-chartjs-2`, `lucide-react`, `tailwindcss`) and scripts (`start`, `build`, `test`).

### `frontend/nginx.conf`
- **Purpose**: Nginx web server configuration for production frontend container.
- **What It Does**: Serves static production assets from `/usr/share/nginx/html`, enables gzip compression, configures cache headers, and provides fallback routing to `index.html` for single-page application routing.

### `frontend/Dockerfile`
- **Purpose**: Multi-stage production container build for the React frontend.
- **What It Does**:
  - Stage 1: Builds the production React bundle using `node:18-alpine`.
  - Stage 2: Copies static assets into `nginx:alpine` and applies `nginx.conf`.

---

## 14. CloudWatch & Serverless Processing (`cloudwatch/` & `lambda/`)

### `cloudwatch/cloudwatch_sender.py`
- **Purpose**: Standalone CLI utility for shipping local log files to AWS CloudWatch Logs.
- **Why Created**: Enables hybrid architectures where on-premise log files are replicated into AWS CloudWatch log streams.
- **What It Does**: Reads local log files, creates CloudWatch Log Groups and Log Streams if absent, and pushes log events via Boto3 `PutLogEvents` with sequence token management.

### `cloudwatch/log_generator.py`
- **Purpose**: Continuous log generator for CloudWatch integration testing.
- **What It Does**: Emits formatted log streams at configurable intervals directly into stdout or files for ingestion testing.

### `cloudwatch/setup_aws_resources.py`
- **Purpose**: Automated AWS setup script.
- **What It Does**: Creates necessary DynamoDB tables (`CloudLogs`, `CloudAlerts`, `CloudStats`), SNS topics, and IAM roles via Boto3 calls.

### `lambda/log_processor.py`
- **Purpose**: Serverless log processing AWS Lambda function.
- **Why Created**: Provides serverless, event-driven log parsing inside the AWS cloud.
- **What It Does**:
  - Triggered by CloudWatch Logs subscription filters.
  - Decompresses and decodes CloudWatch event data.
  - Parses log severity and writes records into DynamoDB.
  - Publishes SNS alerts when `CRITICAL` or `ERROR` logs are detected.

---

## 15. Infrastructure as Code & Deployment Automation (`terraform/` & `deploy/`)

### `terraform/main.tf`
- **Purpose**: Declarative Terraform configuration provisioning AWS infrastructure.
- **Why Created**: Implements Infrastructure as Code (IaC) for reproducible, version-controlled cloud infrastructure.
- **What It Provisions**:
  - EC2 instance for hosting the platform backend and frontend.
  - DynamoDB tables (`CloudLogs`, `CloudAlerts`, `CloudStats`, `Hosts`, `ResourceMetrics`).
  - SNS topic for critical alerts and email/SMS subscriptions.
  - CloudWatch Log Groups.
  - IAM roles and policies with least-privilege permissions.
  - Security Groups with ingress rules for SSH (22), HTTP (80), and API (5000).

### `terraform/variables.tf` & `terraform/outputs.tf`
- **Purpose**: Terraform input variable declarations and output endpoints.
- **What It Does**: Parameterizes AWS region, instance types, and project names; outputs public IP addresses, table names, and topic ARNs.

### `deploy/setup_ec2.sh`
- **Purpose**: Bash script for bootstrapping a fresh Ubuntu EC2 instance.
- **What It Does**: Installs Docker, Docker Compose, Git, and updates system packages.

### `deploy/deploy_ec2.sh`
- **Purpose**: Automated application deployment script for EC2.
- **What It Does**: Pulls latest repository changes, builds Docker containers, and executes `docker-compose up -d`.

### `deploy/lambda_deploy.sh` & `deploy/lambda_deploy.ps1`
- **Purpose**: Linux/macOS Bash and Windows PowerShell packaging scripts for the AWS Lambda function.
- **What It Does**: Zips `lambda/log_processor.py` with its dependencies and uploads the package to AWS Lambda via AWS CLI.

---

## 16. Documentation Catalog

- **`README.md`**: Master onboarding and developer guide featuring quickstart instructions, system architecture diagrams, environment variable reference, and API endpoint documentation.
- **`PROJECT_DOCUMENTATION.md`**: In-depth technical architecture manual covering the 21 major architectural subsystems, data flows, and design decisions.
- **`PROJECT_DESCRIPTION_AND_EDGE_CASES.md`**: Comprehensive reference documenting all failure modes, edge cases (transient spikes, flapping, hypervisor timeouts, split-brain), and operational mitigations.
- **`FILE_EXPLANATIONS.md`**: This document — the definitive reference for every single file in the repository.
- **`docs/ARCHITECTURE_AND_TECHNOLOGY_GUIDE.md`**: Clean, high-level architecture and technology guide tailored for presentations, viva examinations, interviews, and rapid 5–10 minute architectural comprehension.

