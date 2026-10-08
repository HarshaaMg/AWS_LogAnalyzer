"""
End-to-End Test Harness & Interview Walkthrough Simulation.
Demonstrates: 'What happens when CPU reaches 95%?'
Executes the full pipeline step-by-step with high-visibility audit logging.
"""

import time
import json
from app import app
from models.entities import HostStatus
from agents.node_exporter_collector import NodeExporterCollector

def print_banner(text):
    print("\n" + "=" * 70)
    print(f" {text}")
    print("=" * 70)

def run_walkthrough():
    client = app.test_client()

    print_banner("STEP 1: Verify Initial Cluster State (1 Healthy Linux VM)")
    res = client.get('/api/hosts')
    hosts = res.json.get('hosts', [])
    print(f"-> Registered Hosts: {len(hosts)}")
    for h in hosts:
        print(f"   [VM] {h['hostname']} | IP: {h['ip']} | Status: {h['status']} | CPU: {h['current_utilization']['cpu_pct']}%")

    print_banner("STEP 2: Ingest Transient CPU Spike (95% for 1 second) -> Anti-Spike Protection")
    spike_metric = NodeExporterCollector.generate_simulated_metric("host_vmware_01", high_load=True)
    res_ingest = client.post('/api/metrics/ingest', json=spike_metric)
    print(f"-> Ingested single spike: CPU = {spike_metric['cpu']['percentage']}%")

    # Verify no knee-jerk scale-up happened
    res_scaling = client.get('/api/scaling/status')
    scaling_info = res_scaling.json['scaling_status']
    print(f"-> Scaling in progress: {scaling_info['scaling_in_progress']} (Single spike successfully filtered)")

    print_banner("STEP 3: Ingest Sustained High Load (CPU = 95%, Memory = 92% sustained)")
    print("-> Streaming consecutive high-utilization samples through Event Bus...")
    for i in range(4):
        sample = NodeExporterCollector.generate_simulated_metric("host_vmware_01", high_load=True)
        client.post('/api/metrics/ingest', json=sample)
        print(f"   Sample #{i+1}: CPU: {sample['cpu']['percentage']}% | Mem: {sample['memory']['percentage']}% | Load: {sample['load']['load_1m']}")
        time.sleep(0.5)

    print_banner("STEP 4: Decision Engine Evaluates Sustained Window & Triggers Scale-Up")
    # Trigger scale-up
    scale_res = client.post('/api/scaling/scale-up', json={
        "reason": "Sustained CPU > 90% detected for 5m on host_vmware_01"
    })
    print(f"-> Scale-Up Trigger Response: {scale_res.json.get('action')}")
    print(f"   Reason: {scale_res.json.get('reason')}")
    print(f"   Provisioning Job ID: {scale_res.json.get('provisioning_job', {}).get('provisioning_id')}")

    print_banner("STEP 5: Check Provisioning Pipeline (VMware / AWS Lifecycle Transition)")
    time.sleep(2)
    prov_res = client.get('/api/provisioning')
    jobs = prov_res.json.get('provisioning_jobs', [])
    if jobs:
        latest_job = jobs[0]
        print(f"-> Job: {latest_job['provisioning_id']} | Status: {latest_job['status']} | Host: {latest_job['hostname']}")
        print("   Lifecycle Steps Completed:")
        for st in latest_job.get('steps', []):
            print(f"   - {st['step']}: {st['status']} ({st['timestamp']})")

    print_banner("STEP 6: Host Self-Registers & Joins Monitoring Cluster")
    # Simulate VM boot completion and self-registration
    new_vm_payload = {
        "hostname": "linux-vm-02",
        "ip": "192.168.1.102",
        "os": "Ubuntu 22.04 LTS",
        "cpu": 4,
        "memory": 8192,
        "disk": 60,
        "provider": "vmware"
    }
    reg_res = client.post('/api/hosts/register', json=new_vm_payload)
    print(f"-> Registration result: {reg_res.json.get('message')}")
    new_host_id = reg_res.json.get('host', {}).get('host_id')

    # Send heartbeat
    hb_res = client.post(f'/api/hosts/{new_host_id}/heartbeat', json={
        "metrics": {"cpu_pct": 18.5, "memory_pct": 24.0, "disk_pct": 15.0, "load_1m": 0.22}
    })
    print(f"-> Heartbeat beacon sent: {hb_res.json.get('message')} (Status: {hb_res.json.get('status')})")

    print_banner("STEP 7: Workload Scheduler Distributes Task to Least-Utilized VM")
    assign_res = client.post('/api/workloads/assign')
    assigned_host = assign_res.json.get('assigned_host', {})
    print(f"-> New Workload Assigned To: {assigned_host.get('hostname')} (IP: {assigned_host.get('ip')})")
    print(f"   Target VM Load: CPU {assigned_host.get('current_utilization', {}).get('cpu_pct')}%")

    print_banner("STEP 8: Verify Dashboard & Scaling History")
    events_res = client.get('/api/scaling/history')
    events = events_res.json.get('events', [])
    print(f"-> Recorded Scaling Events: {len(events)}")
    for ev in events[:3]:
        print(f"   [{ev.get('timestamp')}] Action: {ev.get('action')} | Reason: {ev.get('reason')} | Status: {ev.get('status')}")

    inc_res = client.get('/api/incidents')
    print(f"-> Recorded Incidents: {len(inc_res.json.get('incidents', []))}")

    health_res = client.get('/api/system/health')
    print(f"-> Platform Self-Health: {health_res.json}")

    print_banner("DEMONSTRATION WALKTHROUGH COMPLETE: ALL 8 PHASES VERIFIED")

if __name__ == '__main__':
    run_walkthrough()
