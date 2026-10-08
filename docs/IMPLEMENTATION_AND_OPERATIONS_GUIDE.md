# Implementation & Operations Guide: Fluent Bit, Node Exporter & Platform Technologies

> **Document Scope**: Practical, production-grade guide on how each technology in this platform is implemented, configured, and run. This includes **Fluent Bit**, **Prometheus Node Exporter**, **Linux VM Guest Initialization**, **Streaming Event Bus (Kafka / In-Memory)**, **Sliding-Window Decision Engine**, **Flask Backend API**, **React Observability UI**, and **AWS CloudWatch / Terraform**.

---

## Table of Contents
1. [Architecture Overview & Technology Roles](#1-architecture-overview--technology-roles)
2. [Fluent Bit: Log Shipper Implementation & Execution](#2-fluent-bit-log-shipper-implementation--execution)
3. [Prometheus Node Exporter: Metric Collector Setup](#3-prometheus-node-exporter-metric-collector-setup)
4. [Linux VM Guest Self-Registration Script (`vm_template_init.sh`)](#4-linux-vm-guest-self-registration-script-vm_template_initsh)
5. [Streaming Event Bus: Kafka, Redpanda & In-Memory Fallback](#5-streaming-event-bus-kafka-redpanda--in-memory-fallback)
6. [Stream Processor & Auto-Scaling Decision Engine](#6-stream-processor--auto-scaling-decision-engine)
7. [Step-by-Step Execution Runbook](#7-step-by-step-execution-runbook)
8. [Verification & Simulation Testing](#8-verification--simulation-testing)
9. [CloudWatch & AWS Integration](#9-cloudwatch--aws-integration)

---

## 1. Architecture Overview & Technology Roles

The platform unifies real-time Linux kernel telemetry, distributed log streaming, and closed-loop auto-scaling across VMware and AWS environments:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   MONITORED LINUX VM                                   │
│                                                                                        │
│  [Syslog / Auth / Apps]         [Kernel /proc & /sys]          [Cloud-Init / Cron]     │
│             │                             │                             │              │
│      (Log Forwarder)             (Telemetry Exposer)           (Self-Register & HB)    │
│             ▼                             ▼                             ▼              │
│       Fluent Bit                   Node Exporter               vm_template_init.sh     │
│     (Port: 2020)                    (Port: 9100)                        │              │
└─────────────┬─────────────────────────────┬─────────────────────────────┬──────────────┘
              │ POST /api/logs              │ Scraped via Python          │ POST /api/hosts/register
              ▼                             ▼                             │ POST /api/hosts/:id/heartbeat
┌─────────────────────────────────────────────────────────────────────────▼──────────────┐
│                            CENTRAL FLASK OBSERVABILITY BACKEND                         │
│                                                                                        │
│   [EventStream Ingestion Engine] ◄── In-Memory Ring Buffer / Apache Kafka / Redpanda   │
│                 │                                                                      │
│                 ▼                                                                      │
│   [Sliding Window Stream Processor] (5-min window, moving avg, anti-spike filter)      │
│                 │                                                                      │
│                 ▼                                                                      │
│   [Resource Shortage Decision Engine] (Checks: Cooldown, Locks, Limits, Thresholds)    │
│                 │                                                                      │
│                 ├── Overload Confirmed ──► [Scaling Controller]                        │
│                 │                                  │                                   │
│                 │                                  ▼                                   │
│                 │                        [VMware / AWS Provisioner]                    │
│                 │                                  │                                   │
│                 │                                  ▼                                   │
│                 │                        New VM Spawned & Booted                       │
│                 │                                                                      │
│   [Storage Layer] ◄── Dual Mode: Local JSON Store OR AWS DynamoDB                      │
│   [Alerting Service] ──► Multi-Channel: AWS SNS, Twilio SMS, SMTP Email                │
└────────────────────────────────────────┬───────────────────────────────────────────────┘
                                         │ REST API / WebSocket
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                REACT 18 OPERATOR DASHBOARD                             │
│                                                                                        │
│  - Live Telemetry Charts (CPU, Memory, Disk, Load via Chart.js)                        │
│  - Monitored Linux VM Inventory Table with dynamic utilization progress bars           │
│  - Auto-Scaling Audit Log, Incident Feeds, and Provisioning Pipeline Tracker           │
│  - Workload Dispatcher (Least-Utilized VM dynamic load routing)                        │
│  - Log Search, Severity Classification & File Upload Parser                            │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Fluent Bit: Log Shipper Implementation & Execution

### What Fluent Bit Does
[Fluent Bit](https://fluentbit.io/) is an ultra-lightweight, high-performance log shipper written in C. It consumes less than 50MB of RAM and minimal CPU while tailing Linux system logs (`/var/log/syslog`, `/var/log/auth.log`) and application log files, formatting them as JSON, and pushing them over HTTP to the backend API (`/api/logs`).

### Installation on Ubuntu / Debian (Target Linux VMs)

Run the following commands in the VM terminal:

```bash
# 1. Add the official Fluent Bit GPG signing key
curl -fsSL https://packages.fluentbit.io/fluentbit.key | sudo gpg --dearmor -o /usr/share/keyrings/fluentbit-keyring.gpg

# 2. Add the Fluent Bit repository to APT sources
echo "deb [signed-by=/usr/share/keyrings/fluentbit-keyring.gpg] https://packages.fluentbit.io/ubuntu/jammy jammy main" | sudo tee /etc/apt/sources.list.d/fluent-bit.list

# 3. Update repositories and install fluent-bit
sudo apt-get update -y
sudo apt-get install -y fluent-bit
```

### Configuration (`/etc/fluent-bit/fluent-bit.conf`)

Configure Fluent Bit to tail system logs and stream them to the platform backend:

```ini
[SERVICE]
    Flush         1
    Daemon        Off
    Log_Level     info
    Parsers_File  parsers.conf

# 1. INPUT: Ingest Linux Syslog and Authentication Logs
[INPUT]
    Name          tail
    Path          /var/log/syslog,/var/log/auth.log
    Tag           linux.system
    Refresh_Interval 5
    Read_from_Head  On

# 2. INPUT: Ingest Custom Application Logs
[INPUT]
    Name          tail
    Path          /app/logs/*.log,/var/log/application.log
    Tag           linux.application
    Refresh_Interval 5

# 3. FILTER: Add Metadata & Host Identification
[FILTER]
    Name          record_modifier
    Match         *
    Record        hostname ${HOSTNAME}
    Record        source fluent-bit

# 4. OUTPUT: Forward to the Observability Backend REST API
[OUTPUT]
    Name          http
    Match         *
    Host          127.0.0.1
    Port          5000
    URI           /api/logs
    Format        json
    Header        Content-Type application/json
    Header        X-Agent-Key linux-agent-secret-key
```

### Running and Verifying Fluent Bit

```bash
# Test run directly in foreground to verify configuration:
/opt/fluent-bit/bin/fluent-bit -c /etc/fluent-bit/fluent-bit.conf

# Enable and start as a background systemd service:
sudo systemctl enable fluent-bit
sudo systemctl start fluent-bit
sudo systemctl status fluent-bit
```

---

## 3. Prometheus Node Exporter: Metric Collector Setup

### What Node Exporter Does
Prometheus Node Exporter runs as a lightweight daemon on each Linux host, exposing low-level hardware and OS metrics directly from `/proc` and `/sys` over HTTP on port `9100` in the standard OpenMetrics exposition format.

### Installation on Ubuntu / Debian

```bash
# 1. Install via package manager
sudo apt-get update -y
sudo apt-get install -y prometheus-node-exporter

# 2. Enable and start the systemd service
sudo systemctl enable prometheus-node-exporter
sudo systemctl start prometheus-node-exporter

# 3. Verify metrics endpoint is active
curl -s http://localhost:9100/metrics | head -n 25
```

### How the Platform Scrapes and Ingests Node Exporter Telemetry

The platform provides [backend/agents/node_exporter_collector.py](file:///c:/Users/harsh/OneDrive/Desktop/aws/AWS_LogAnalyzer/backend/agents/node_exporter_collector.py):
1. Connects to `http://<vm-ip>:9100/metrics`.
2. Computes CPU utilization percentage:
   $$\text{CPU \%} = 100 \times \left(1 - \frac{\Delta \text{idle}}{\Delta \text{total}}\right)$$
3. Computes memory utilization percentage:
   $$\text{Memory \%} = 100 \times \left(1 - \frac{\text{MemAvailable}}{\text{MemTotal}}\right)$$
4. Extracts 1-minute, 5-minute, and 15-minute load averages (`node_load1`, `node_load5`, `node_load15`).
5. Posts structured telemetry payload to `/api/metrics/ingest`.

---

## 4. Linux VM Guest Self-Registration Script (`vm_template_init.sh`)

When a new Linux VM is cloned by VMware or launched as an AWS EC2 instance, the script [backend/agents/vm_template_init.sh](file:///c:/Users/harsh/OneDrive/Desktop/aws/AWS_LogAnalyzer/backend/agents/vm_template_init.sh) is triggered via **Cloud-Init** or a **systemd oneshot service**.

### Script Workflow:
1. **Host Environment Detection**:
   - Queries `hostname`, detects primary network IP (`ip -4 route get 1.1.1.1`).
   - Counts CPU cores (`nproc`), total RAM (`free -m`), and root disk size (`df -BG /`).
2. **Prometheus Node Exporter**: Installs, enables, and restarts `prometheus-node-exporter`.
3. **Fluent Bit**: Installs, creates `/etc/fluent-bit/fluent-bit.conf`, and starts the service.
4. **Platform Self-Registration**:
   - Sends `POST /api/hosts/register` with hardware specs and IP.
   - Initial status set to `ACTIVE`.
5. **Heartbeat Cron**:
   - Installs a cron job running every minute:
     ```bash
     * * * * * curl -s -X POST http://<backend-ip>:5000/api/hosts/host_<hostname>/heartbeat -H 'X-Agent-Key: linux-agent-secret-key' > /dev/null 2>&1
     ```

### Running the Bootstrap Script Manually on a Test VM:

```bash
# Make script executable
chmod +x backend/agents/vm_template_init.sh

# Run with environment override to point to your backend IP:
BACKEND_API_URL="http://192.168.1.100:5000" ./backend/agents/vm_template_init.sh
```

---

## 5. Streaming Event Bus: Kafka, Redpanda & In-Memory Fallback

The streaming layer in [backend/streaming/event_stream.py](file:///c:/Users/harsh/OneDrive/Desktop/aws/AWS_LogAnalyzer/backend/streaming/event_stream.py) decouples telemetry collection from analytics.

### Dual-Mode Architecture:
- **Mode 1: Distributed Streaming (Kafka / Redpanda)**:
  Used when `KAFKA_BOOTSTRAP_SERVERS` is defined (e.g., `localhost:9092`). Messages are serialized to JSON and published to the `linux-metrics` and `linux-logs` topics.
- **Mode 2: Resilient In-Memory Ring Buffer**:
  If Kafka is not configured or goes offline, the system automatically falls back to an internal thread-safe in-memory ring buffer (up to 5,000 samples). This guarantees zero crashes during local development or offline testing.

### Running Kafka / Redpanda Locally with Docker:

If you want a live Kafka broker:

```bash
# Launch lightweight single-node Redpanda (100% Kafka API compatible):
docker run -d --name redpanda \
  -p 9092:9092 \
  vectorized/redpanda:latest \
  redpanda start --overprovisioned --smp 1 --memory 512M --reserve-memory 0M --node-id 0 --check=false
```

Then add this to your `backend/.env`:
```env
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_METRICS_TOPIC=linux-metrics
KAFKA_LOGS_TOPIC=linux-logs
```

---

## 6. Stream Processor & Auto-Scaling Decision Engine

The pipeline processes high-frequency samples and prevents accidental "knee-jerk" auto-scaling actions.

### 1. Sliding Window (`StreamProcessor`)
- Implemented in [backend/streaming/stream_processor.py](file:///c:/Users/harsh/OneDrive/Desktop/aws/AWS_LogAnalyzer/backend/streaming/stream_processor.py).
- Maintains a 5-minute rolling window per host (up to 60 telemetry points).
- Computes moving averages for CPU, Memory, Disk, and Load.

### 2. Anti-Spike Protection
- A single isolated spike (e.g., 95% CPU for 1 second) is treated as a transient anomaly and discarded.
- Only sustained saturation (at least 3 consecutive samples $\ge 85\%$ with average $\ge 90\%$) qualifies for scaling consideration.

### 3. Decision Engine Safety Checks
- Implemented in [backend/scaling/decision_engine.py](file:///c:/Users/harsh/OneDrive/Desktop/aws/AWS_LogAnalyzer/backend/scaling/decision_engine.py).
- **Auto-Scaling Enabled Check**: Verifies `AUTO_SCALING_ENABLED=true`.
- **Scaling Lock**: Prevents multiple scale-ups from executing simultaneously while a VM is booting.
- **Cooldown Enforcement**: Rejects scale-up requests if the cooldown timer (`COOLDOWN_PERIOD=300`) has not elapsed.
- **Maximum VM Boundary**: Enforces `MAX_VM_COUNT` limit to prevent runaway cloud bills.
- **Dry-Run Mode**: If `DRY_RUN_MODE=true`, logs `WOULD_PROVISION (DRY-RUN)` and audits the action without calling cloud APIs.

---

## 7. Step-by-Step Execution Runbook

### Prerequisites
- **Python**: 3.10+ installed (`python --version`)
- **Node.js**: v18+ installed (`node -v`)
- **Git**

### Step 1: Start the Backend Server

```bash
# Navigate to the backend directory
cd backend

# Install dependencies (only required once)
pip install -r requirements.txt

# Run the Flask backend
python app.py
```

- Backend URL: `http://127.0.0.1:5000`
- On startup, the backend automatically initializes:
  - In-memory event stream bus.
  - Primary demo Linux VM (`linux-vm-01`) in `ACTIVE` state.
  - Initial sample application and system logs in `backend/logs/`.
  - Background supervisor for heartbeat watchdog and live telemetry updates.

### Step 2: Start the React Frontend

Open a new terminal:

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies (only required once)
npm install

# Start the React development server
npm start
```

- Frontend URL: `http://localhost:3000`
- Webpack dev server automatically proxies `/api` calls to `http://127.0.0.1:5000`.

### Step 3: Access and Use the Platform

1. Open your browser to: **`http://localhost:3000`**
2. Log in using the built-in credentials:
   - **Username**: `admin`
   - **Password**: `admin123`
3. Explore the **Observability & Auto-Scaling** tab:
   - View real-time cluster utilization cards.
   - Click telemetry tabs (**CPU**, **Memory**, **Disk**, **Load**) to view live Chart.js graphs.
   - Inspect the **Monitored Linux Virtual Machines** table.
   - Click **Trigger Manual Scale-Up** to initiate VM provisioning.
   - Click **Dispatch Workload (Least-Utilized VM)** to dynamically assign tasks to the lowest-load host.
   - Review the **Scaling Event History** panel for real-time audit logging.
4. Explore the **Log Analytics & Alerts** tab:
   - View severity breakdowns (Pie Chart) and error trends.
   - Filter logs by severity (`CRITICAL`, `ERROR`, `WARNING`, `INFO`).
   - Upload new `.log`, `.txt`, or `.json` files to parse logs and generate immediate alerts.

---

## 8. Verification & Simulation Testing

To verify the complete 8-phase autonomous auto-scaling pipeline without waiting for live hardware alerts, run the end-to-end test harness:

```bash
cd backend
python test_auto_scaling.py
```

### What the Simulation Validates:
1. **Phase 1**: Confirms cluster state with active Linux VM.
2. **Phase 2**: Ingests transient 95% CPU spike (proves anti-spike filter blocks knee-jerk scale-up).
3. **Phase 3**: Streams sustained high load across sliding window samples.
4. **Phase 4**: Decision engine confirms sustained exhaustion and triggers scale-up.
5. **Phase 5**: Provisioning pipeline executes lifecycle transitions (`ALLOCATE_RESOURCE` $\to$ `DRY_RUN_EVALUATE`).
6. **Phase 6**: Guest VM self-registers via `POST /api/hosts/register` and sends initial heartbeat.
7. **Phase 7**: Workload scheduler detects new VM and rebalances tasks to the least-utilized host.
8. **Phase 8**: Verifies scaling audit history, active incidents, and platform self-health.

---

## 9. CloudWatch & AWS Integration

### Running the CloudWatch Sender
To forward local application logs directly to AWS CloudWatch:

1. Configure your AWS credentials in your environment or `backend/.env`:
   ```env
   AWS_REGION=us-east-1
   AWS_ACCESS_KEY_ID=your-access-key-id
   AWS_SECRET_ACCESS_KEY=your-secret-access-key
   ```
2. Run the sender utility:
   ```bash
   # One-time batch upload of existing application logs
   python cloudwatch/cloudwatch_sender.py

   # Continuous log file monitoring and streaming (tail mode)
   python cloudwatch/cloudwatch_sender.py --tail 5
   ```

### Deploying AWS Cloud Infrastructure with Terraform
All AWS resources (DynamoDB tables, SNS topics, CloudWatch Log Groups, EC2 security groups, and IAM roles) are defined declaratively in [terraform/main.tf](file:///c:/Users/harsh/OneDrive/Desktop/aws/AWS_LogAnalyzer/terraform/main.tf):

```bash
cd terraform

# 1. Initialize Terraform providers
terraform init

# 2. Review deployment plan
terraform plan

# 3. Apply and provision AWS cloud infrastructure
terraform apply
```
