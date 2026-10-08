#!/usr/bin/env bash
# ==============================================================================
# Reusable Linux VM Template Bootstrap Script
# Real-Time Linux Observability & Auto-Scaling Platform
# ==============================================================================
set -euo pipefail

BACKEND_API_URL="${BACKEND_API_URL:-http://192.168.1.100:5000}"
AGENT_REGISTRATION_KEY="${AGENT_REGISTRATION_KEY:-linux-agent-secret-key}"

echo "=========================================="
echo "Initializing Linux Observability Agent..."
echo "=========================================="

# 1. Detect Host Environment & Network
HOSTNAME_CURRENT=$(hostname)
PRIMARY_IP=$(ip -4 route get 1.1.1.1 | awk '{print $7; exit}')
CPU_CORES=$(nproc)
TOTAL_MEM_MB=$(free -m | awk '/^Mem:/{print $2}')
TOTAL_DISK_GB=$(df -BG / | awk 'NR==2{print $2}' | tr -d 'G')
OS_INFO=$(grep '^PRETTY_NAME=' /etc/os-release | cut -d= -f2 | tr -d '"' || echo "Linux")

echo "Host: ${HOSTNAME_CURRENT} | IP: ${PRIMARY_IP} | CPUs: ${CPU_CORES} | RAM: ${TOTAL_MEM_MB}MB"

# 2. Install & Start Prometheus Node Exporter
if ! command -v node_exporter &> /dev/null; then
    echo "Installing Prometheus Node Exporter..."
    apt-get update -y && apt-get install -y prometheus-node-exporter || true
fi

systemctl enable prometheus-node-exporter || true
systemctl restart prometheus-node-exporter || true

# 3. Configure & Start Fluent Bit
if ! command -v fluent-bit &> /dev/null; then
    echo "Installing Fluent Bit..."
    curl -fsSL https://packages.fluentbit.io/fluentbit.key | gpg --dearmor -o /usr/share/keyrings/fluentbit-keyring.gpg || true
    echo "deb [signed-by=/usr/share/keyrings/fluentbit-keyring.gpg] https://packages.fluentbit.io/ubuntu/jammy jammy main" > /etc/apt/sources.list.d/fluent-bit.list || true
    apt-get update -y && apt-get install -y fluent-bit || true
fi

# Write Fluent Bit Config
mkdir -p /etc/fluent-bit
cat <<EOF > /etc/fluent-bit/fluent-bit.conf
[SERVICE]
    Flush        1
    Daemon       Off
    Log_Level    info

[INPUT]
    Name         tail
    Path         /var/log/syslog,/var/log/auth.log
    Tag          linux.logs

[OUTPUT]
    Name         http
    Match        *
    Host         192.168.1.100
    Port         5000
    URI          /api/logs
    Format       json
EOF

systemctl enable fluent-bit || true
systemctl restart fluent-bit || true

# 4. Self-Register with Monitoring Backend
echo "Registering VM with Auto-Scaling Controller at ${BACKEND_API_URL}..."
PAYLOAD=$(cat <<EOF
{
    "hostname": "${HOSTNAME_CURRENT}",
    "ip": "${PRIMARY_IP}",
    "os": "${OS_INFO}",
    "cpu": ${CPU_CORES},
    "memory": ${TOTAL_MEM_MB},
    "disk": ${TOTAL_DISK_GB},
    "provider": "vmware"
}
EOF
)

curl -s -X POST "${BACKEND_API_URL}/api/hosts/register" \
    -H "Content-Type: application/json" \
    -H "X-Agent-Key: ${AGENT_REGISTRATION_KEY}" \
    -d "${PAYLOAD}"

# 5. Setup Periodic Heartbeat Cron / Timer
CRON_JOB="* * * * * curl -s -X POST ${BACKEND_API_URL}/api/hosts/host_${HOSTNAME_CURRENT//-/_}/heartbeat -H 'X-Agent-Key: ${AGENT_REGISTRATION_KEY}' > /dev/null 2>&1"
(crontab -l 2>/dev/null | grep -Fv "/api/hosts"; echo "${CRON_JOB}") | crontab -

echo "=========================================="
echo "VM Template Initialization Complete!"
echo "Status: ACTIVE in Monitoring Cluster"
echo "=========================================="
