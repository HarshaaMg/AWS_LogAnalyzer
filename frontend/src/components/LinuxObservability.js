import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Server,
  Cpu,
  HardDrive,
  Activity,
  AlertOctagon,
  ArrowUpRight,
  ArrowDownRight,
  ShieldAlert,
  Clock,
  Zap,
  Play,
  CheckCircle2,
  RotateCw,
  Box
} from 'lucide-react';
import { Line } from 'react-chartjs-2';

export default function LinuxObservability({ isDarkMode }) {
  const [clusterSummary, setClusterSummary] = useState(null);
  const [hosts, setHosts] = useState([]);
  const [scalingStatus, setScalingStatus] = useState(null);
  const [scalingEvents, setScalingEvents] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [provisioningJobs, setProvisioningJobs] = useState([]);
  const [activeChartTab, setActiveChartTab] = useState('cpu');
  const [chartDataPoints, setChartDataPoints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionMessage, setActionMessage] = useState(null);

  const getAuthHeaders = () => {
    const currentToken = localStorage.getItem('token');
    return currentToken ? { Authorization: `Bearer ${currentToken}` } : {};
  };

  const fetchObservabilityData = async () => {
    try {
      const authHeaders = getAuthHeaders();
      const [resSummary, resHosts, resScaling, resEvents, resIncidents, resJobs, resChart] = await Promise.all([
        axios.get('/api/resources', { headers: authHeaders }),
        axios.get('/api/hosts', { headers: authHeaders }),
        axios.get('/api/scaling/status', { headers: authHeaders }),
        axios.get('/api/scaling/history?limit=10', { headers: authHeaders }),
        axios.get('/api/incidents/active', { headers: authHeaders }),
        axios.get('/api/provisioning?limit=10', { headers: authHeaders }),
        axios.get(`/api/resources/${activeChartTab}?limit=20`, { headers: authHeaders })
      ]);

      setClusterSummary(resSummary.data.cluster_summary);
      setHosts(resHosts.data.hosts || []);
      setScalingStatus(resScaling.data.scaling_status);
      setScalingEvents(resEvents.data.events || []);
      setIncidents(resIncidents.data.active_incidents || []);
      setProvisioningJobs(resJobs.data.provisioning_jobs || []);
      setChartDataPoints(resChart.data.data || []);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching observability data:', err);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchObservabilityData();
    const interval = setInterval(fetchObservabilityData, 5000); // 5-second polling for real-time responsiveness
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeChartTab]);

  const handleManualScaleUp = async () => {
    try {
      setActionMessage('Initiating manual scale-up...');
      const res = await axios.post('/api/scaling/scale-up', { reason: 'Operator manual scale-up trigger' }, { headers: getAuthHeaders() });
      setActionMessage(`Scale-Up Success: ${res.data.action}`);
      setTimeout(() => setActionMessage(null), 4000);
      fetchObservabilityData();
    } catch (err) {
      setActionMessage(`Scale-up failed: ${err.response?.data?.error || err.message}`);
      setTimeout(() => setActionMessage(null), 4000);
    }
  };

  const handleManualScaleDown = async () => {
    try {
      setActionMessage('Evaluating safe scale-down...');
      const res = await axios.post('/api/scaling/scale-down', { reason: 'Operator manual decommission' }, { headers: getAuthHeaders() });
      setActionMessage(`Scale-Down Success: ${res.data.action}`);
      setTimeout(() => setActionMessage(null), 4000);
      fetchObservabilityData();
    } catch (err) {
      setActionMessage(`Scale-down rejected: ${err.response?.data?.error || err.message}`);
      setTimeout(() => setActionMessage(null), 4000);
    }
  };

  const handleAssignWorkload = async () => {
    try {
      const res = await axios.post('/api/workloads/assign', {}, { headers: getAuthHeaders() });
      const assigned = res.data.assigned_host;
      setActionMessage(`Task assigned to least-utilized VM: ${assigned.hostname} (CPU: ${assigned.current_utilization.cpu_pct}%)`);
      setTimeout(() => setActionMessage(null), 4000);
      fetchObservabilityData();
    } catch (err) {
      setActionMessage(`Workload assignment error: ${err.response?.data?.error || err.message}`);
      setTimeout(() => setActionMessage(null), 4000);
    }
  };

  // Prepare Chart.js dataset
  const chartLabels = chartDataPoints.map((d, i) => {
    if (d.timestamp) {
      const date = new Date(d.timestamp);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }
    return `T-${chartDataPoints.length - i}`;
  });

  const chartValues = chartDataPoints.map(d => d.value);

  const lineChartData = {
    labels: chartLabels.length > 0 ? chartLabels : ['Now'],
    datasets: [
      {
        label: `${activeChartTab.toUpperCase()} Utilization`,
        data: chartValues.length > 0 ? chartValues : [0],
        borderColor: activeChartTab === 'cpu' ? '#3B82F6' : activeChartTab === 'memory' ? '#10B981' : activeChartTab === 'disk' ? '#F59E0B' : '#8B5CF6',
        backgroundColor: activeChartTab === 'cpu' ? 'rgba(59, 130, 246, 0.1)' : activeChartTab === 'memory' ? 'rgba(16, 185, 129, 0.1)' : activeChartTab === 'disk' ? 'rgba(245, 158, 11, 0.1)' : 'rgba(139, 92, 246, 0.1)',
        tension: 0.3,
        fill: true
      }
    ]
  };

  const lineChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false }
    },
    scales: {
      y: {
        beginAtZero: true,
        max: activeChartTab === 'load' ? undefined : 100,
        grid: { color: isDarkMode ? '#374151' : '#E5E7EB' }
      },
      x: {
        grid: { display: false }
      }
    }
  };

  if (loading && !clusterSummary) {
    return (
      <div className="flex items-center justify-center p-16">
        <RotateCw className="w-8 h-8 text-blue-500 animate-spin mr-3" />
        <span className="text-gray-500 text-sm font-medium">Connecting to Linux Observability Cluster...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Action Notification Banner */}
      {actionMessage && (
        <div className="p-3 bg-blue-600 text-white rounded-lg shadow-md flex items-center justify-between text-sm animate-pulse">
          <div className="flex items-center space-x-2">
            <Zap className="w-4 h-4" />
            <span>{actionMessage}</span>
          </div>
        </div>
      )}

      {/* 1. SYSTEM OVERVIEW CARDS */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
        <div className={`p-4 rounded-xl shadow-sm border ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <div className="flex items-center justify-between text-gray-500 mb-2">
            <span className="text-xs font-medium uppercase">Total VMs</span>
            <Server className="w-4 h-4 text-blue-500" />
          </div>
          <div className="text-2xl font-bold">{clusterSummary?.total_hosts ?? 0}</div>
          <div className="text-xs text-gray-400 mt-1">{clusterSummary?.total_cpu_cores ?? 0} Total Cores</div>
        </div>

        <div className={`p-4 rounded-xl shadow-sm border ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <div className="flex items-center justify-between text-gray-500 mb-2">
            <span className="text-xs font-medium uppercase">Active VMs</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-2xl font-bold text-emerald-500">{clusterSummary?.active_hosts ?? 0}</div>
          <div className="text-xs text-gray-400 mt-1">Ready for workloads</div>
        </div>

        <div className={`p-4 rounded-xl shadow-sm border ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <div className="flex items-center justify-between text-gray-500 mb-2">
            <span className="text-xs font-medium uppercase">Unhealthy</span>
            <AlertOctagon className="w-4 h-4 text-rose-500" />
          </div>
          <div className="text-2xl font-bold text-rose-500">{clusterSummary?.unhealthy_hosts ?? 0}</div>
          <div className="text-xs text-gray-400 mt-1">Missing heartbeat</div>
        </div>

        <div className={`p-4 rounded-xl shadow-sm border ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <div className="flex items-center justify-between text-gray-500 mb-2">
            <span className="text-xs font-medium uppercase">Provisioning</span>
            <RotateCw className="w-4 h-4 text-indigo-500 animate-spin" />
          </div>
          <div className="text-2xl font-bold text-indigo-500">{clusterSummary?.provisioning_hosts ?? 0}</div>
          <div className="text-xs text-gray-400 mt-1">In boot sequence</div>
        </div>

        <div className={`p-4 rounded-xl shadow-sm border ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <div className="flex items-center justify-between text-gray-500 mb-2">
            <span className="text-xs font-medium uppercase">Cluster CPU</span>
            <Cpu className="w-4 h-4 text-blue-500" />
          </div>
          <div className="text-2xl font-bold">{clusterSummary?.average_cpu_pct ?? 0}%</div>
          <div className="w-full bg-gray-200 rounded-full h-1.5 mt-2">
            <div className="bg-blue-500 h-1.5 rounded-full" style={{ width: `${Math.min(clusterSummary?.average_cpu_pct || 0, 100)}%` }}></div>
          </div>
        </div>

        <div className={`p-4 rounded-xl shadow-sm border ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <div className="flex items-center justify-between text-gray-500 mb-2">
            <span className="text-xs font-medium uppercase">Cluster RAM</span>
            <Activity className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-2xl font-bold">{clusterSummary?.average_memory_pct ?? 0}%</div>
          <div className="w-full bg-gray-200 rounded-full h-1.5 mt-2">
            <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: `${Math.min(clusterSummary?.average_memory_pct || 0, 100)}%` }}></div>
          </div>
        </div>

        <div className={`p-4 rounded-xl shadow-sm border ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <div className="flex items-center justify-between text-gray-500 mb-2">
            <span className="text-xs font-medium uppercase">Cluster Disk</span>
            <HardDrive className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold">{clusterSummary?.average_disk_pct ?? 0}%</div>
          <div className="w-full bg-gray-200 rounded-full h-1.5 mt-2">
            <div className="bg-amber-500 h-1.5 rounded-full" style={{ width: `${Math.min(clusterSummary?.average_disk_pct || 0, 100)}%` }}></div>
          </div>
        </div>
      </div>

      {/* 2. MAIN GRID: RESOURCE GRAPHS & SCALING CONTROLLER */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Resource Graph Widget */}
        <div className={`lg:col-span-2 p-5 rounded-xl shadow-sm border ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <div className="flex flex-wrap items-center justify-between pb-4 border-b border-gray-200 dark:border-gray-700 mb-4">
            <div>
              <h3 className="font-semibold text-lg">Cluster Resource Telemetry</h3>
              <p className="text-xs text-gray-400">Streamed from Node Exporter & Metric Aggregator</p>
            </div>
            <div className="flex space-x-1 bg-gray-100 dark:bg-gray-700 p-1 rounded-lg">
              {['cpu', 'memory', 'disk', 'load', 'io'].map(tab => (
                <button
                  key={tab}
                  onClick={() => setActiveChartTab(tab)}
                  className={`px-3 py-1 text-xs font-medium rounded-md uppercase transition-colors ${
                    activeChartTab === tab
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'text-gray-500 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>
          <div className="h-64">
            <Line data={lineChartData} options={lineChartOptions} />
          </div>
        </div>

        {/* Auto-Scaling Controller Panel */}
        <div className={`p-5 rounded-xl shadow-sm border ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <div className="flex items-center justify-between pb-3 border-b border-gray-200 dark:border-gray-700 mb-4">
            <h3 className="font-semibold text-lg flex items-center space-x-2">
              <Zap className="w-5 h-5 text-amber-500" />
              <span>Scaling Controller</span>
            </h3>
            <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${
              scalingStatus?.scaling_in_progress
                ? 'bg-indigo-100 text-indigo-700'
                : scalingStatus?.in_cooldown
                ? 'bg-amber-100 text-amber-700'
                : 'bg-emerald-100 text-emerald-700'
            }`}>
              {scalingStatus?.scaling_in_progress ? 'PROVISIONING' : scalingStatus?.in_cooldown ? 'COOLDOWN' : 'ACTIVE'}
            </span>
          </div>

          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">VM Capacity Range:</span>
              <span className="font-medium">{scalingStatus?.min_vm_count} Min / {scalingStatus?.max_vm_count} Max</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Current / Active:</span>
              <span className="font-medium">{scalingStatus?.current_vm_count} total ({scalingStatus?.active_vm_count} active)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Dry-Run Mode:</span>
              <span className={`font-semibold ${scalingStatus?.dry_run_mode ? 'text-amber-500' : 'text-emerald-500'}`}>
                {scalingStatus?.dry_run_mode ? 'ENABLED (Safe)' : 'DISABLED (Real)'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Cooldown Remaining:</span>
              <span className="font-medium flex items-center space-x-1">
                <Clock className="w-3.5 h-3.5 text-gray-400" />
                <span>{scalingStatus?.cooldown_remaining_seconds ?? 0}s</span>
              </span>
            </div>

            {/* Quick Action Buttons */}
            <div className="pt-3 border-t border-gray-200 dark:border-gray-700 space-y-2">
              <button
                onClick={handleManualScaleUp}
                className="w-full flex items-center justify-center space-x-1 py-2 px-3 bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs rounded-lg transition-colors"
              >
                <ArrowUpRight className="w-4 h-4" />
                <span>Trigger Manual Scale-Up</span>
              </button>
              <button
                onClick={handleManualScaleDown}
                className="w-full flex items-center justify-center space-x-1 py-2 px-3 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 font-medium text-xs rounded-lg transition-colors"
              >
                <ArrowDownRight className="w-4 h-4" />
                <span>Trigger Safe Scale-Down</span>
              </button>
              <button
                onClick={handleAssignWorkload}
                className="w-full flex items-center justify-center space-x-1 py-2 px-3 bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-xs rounded-lg transition-colors"
              >
                <Box className="w-4 h-4" />
                <span>Dispatch Workload (Least-Utilized VM)</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 3. LINUX VM HOST TABLE */}
      <div className={`p-5 rounded-xl shadow-sm border ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-lg flex items-center space-x-2">
              <Server className="w-5 h-5 text-blue-500" />
              <span>Monitored Linux Virtual Machines</span>
            </h3>
            <p className="text-xs text-gray-400">VMware & AWS EC2 cluster members with real-time heartbeat and utilization</p>
          </div>
          <button
            onClick={fetchObservabilityData}
            className="flex items-center space-x-1 text-xs px-2.5 py-1.5 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-md"
          >
            <RotateCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase bg-gray-50 dark:bg-gray-700/50 text-gray-500">
              <tr>
                <th className="px-4 py-3">Host / ID</th>
                <th className="px-4 py-3">Provider / IP</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">CPU</th>
                <th className="px-4 py-3">Memory</th>
                <th className="px-4 py-3">Disk</th>
                <th className="px-4 py-3">Load 1m</th>
                <th className="px-4 py-3">Workloads</th>
                <th className="px-4 py-3">Heartbeat</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {hosts.map(h => (
                <tr key={h.host_id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                  <td className="px-4 py-3 font-medium">
                    <div>{h.hostname}</div>
                    <div className="text-xs text-gray-400">{h.host_id}</div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="uppercase text-xs font-semibold text-indigo-500">{h.provider}</div>
                    <div className="text-xs font-mono">{h.ip}</div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                      h.status === 'ACTIVE'
                        ? 'bg-emerald-100 text-emerald-700'
                        : h.status === 'UNHEALTHY'
                        ? 'bg-rose-100 text-rose-700'
                        : 'bg-amber-100 text-amber-700 animate-pulse'
                    }`}>
                      {h.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center space-x-2">
                      <span>{h.current_utilization?.cpu_pct ?? 0}%</span>
                      <div className="w-12 bg-gray-200 dark:bg-gray-600 rounded-full h-1.5">
                        <div
                          className={`h-1.5 rounded-full ${
                            (h.current_utilization?.cpu_pct || 0) > 85 ? 'bg-rose-500' : 'bg-blue-500'
                          }`}
                          style={{ width: `${Math.min(h.current_utilization?.cpu_pct || 0, 100)}%` }}
                        ></div>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center space-x-2">
                      <span>{h.current_utilization?.memory_pct ?? 0}%</span>
                      <div className="w-12 bg-gray-200 dark:bg-gray-600 rounded-full h-1.5">
                        <div
                          className={`h-1.5 rounded-full ${
                            (h.current_utilization?.memory_pct || 0) > 85 ? 'bg-rose-500' : 'bg-emerald-500'
                          }`}
                          style={{ width: `${Math.min(h.current_utilization?.memory_pct || 0, 100)}%` }}
                        ></div>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">{h.current_utilization?.disk_pct ?? 0}%</td>
                  <td className="px-4 py-3 font-mono">{h.current_utilization?.load_1m ?? 0.0}</td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded-md font-semibold text-xs">
                      {h.active_workloads ?? 0}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-400">
                    {h.last_heartbeat ? new Date(h.last_heartbeat).toLocaleTimeString() : 'N/A'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 4. LOWER TRIPLE PANELS: INCIDENTS, PROVISIONING, & SCALING HISTORY */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Incident Panel */}
        <div className={`p-5 rounded-xl shadow-sm border ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <div className="flex items-center justify-between pb-3 border-b border-gray-200 dark:border-gray-700 mb-4">
            <h3 className="font-semibold text-lg flex items-center space-x-2">
              <ShieldAlert className="w-5 h-5 text-rose-500" />
              <span>Active Incidents & Alerts</span>
            </h3>
            <span className="text-xs bg-rose-100 text-rose-700 px-2 py-0.5 rounded-full font-semibold">
              {incidents.length} Active
            </span>
          </div>

          <div className="space-y-3 max-h-60 overflow-y-auto">
            {incidents.length === 0 ? (
              <div className="text-center py-8 text-gray-400 text-sm">
                <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-80" />
                No active resource incidents. All VMs within safe thresholds.
              </div>
            ) : (
              incidents.map(inc => (
                <div key={inc.incident_id} className="p-3 rounded-lg border border-rose-200 bg-rose-50 dark:bg-rose-950/20 dark:border-rose-900 text-xs">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-bold text-rose-600 dark:text-rose-400 uppercase">{inc.type}</span>
                    <span className="text-gray-400">{inc.duration} sustained</span>
                  </div>
                  <div className="text-gray-700 dark:text-gray-300">
                    Host: <b>{inc.host_id}</b> | Threshold: {inc.threshold}% | Value: <b className="text-rose-600">{inc.actual_value}%</b>
                  </div>
                  <div className="mt-1 text-gray-500 dark:text-gray-400 flex items-center space-x-1">
                    <Zap className="w-3.5 h-3.5 text-amber-500" />
                    <span>Action Taken: {inc.action}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Provisioning Pipeline Panel */}
        <div className={`p-5 rounded-xl shadow-sm border ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <div className="flex items-center justify-between pb-3 border-b border-gray-200 dark:border-gray-700 mb-4">
            <h3 className="font-semibold text-lg flex items-center space-x-2">
              <Play className="w-5 h-5 text-indigo-500" />
              <span>VM Provisioning Pipeline</span>
            </h3>
            <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full font-semibold">
              {provisioningJobs.length} Jobs
            </span>
          </div>

          <div className="space-y-3 max-h-60 overflow-y-auto">
            {provisioningJobs.length === 0 ? (
              <div className="text-center py-8 text-gray-400 text-sm">
                No active provisioning jobs in pipeline.
              </div>
            ) : (
              provisioningJobs.map(job => (
                <div key={job.provisioning_id} className="p-3 rounded-lg border border-gray-200 dark:border-gray-700 text-xs">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-semibold text-blue-500">{job.hostname} ({job.provider?.toUpperCase()})</span>
                    <span className={`px-2 py-0.5 rounded-full font-medium ${
                      job.status === 'ACTIVE'
                        ? 'bg-emerald-100 text-emerald-700'
                        : job.status === 'FAILED'
                        ? 'bg-rose-100 text-rose-700'
                        : 'bg-indigo-100 text-indigo-700 animate-pulse'
                    }`}>
                      {job.status}
                    </span>
                  </div>
                  <div className="text-gray-400 mb-2">
                    ID: {job.provisioning_id} | Started: {new Date(job.started_at).toLocaleTimeString()}
                  </div>
                  {/* Step checklist */}
                  <div className="flex flex-wrap gap-1.5">
                    {job.steps?.map((st, idx) => (
                      <span key={idx} className="bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded text-[10px] text-gray-600 dark:text-gray-300">
                        {st.step}: {st.status}
                      </span>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Scaling Event History Panel */}
        <div className={`p-5 rounded-xl shadow-sm border ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <div className="flex items-center justify-between pb-3 border-b border-gray-200 dark:border-gray-700 mb-4">
            <h3 className="font-semibold text-lg flex items-center space-x-2">
              <Zap className="w-5 h-5 text-amber-500" />
              <span>Scaling Event History</span>
            </h3>
            <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full font-semibold">
              {scalingEvents.length} Events
            </span>
          </div>

          <div className="space-y-3 max-h-60 overflow-y-auto">
            {scalingEvents.length === 0 ? (
              <div className="text-center py-8 text-gray-400 text-sm">
                No scaling events recorded yet.
              </div>
            ) : (
              scalingEvents.map(ev => (
                <div key={ev.event_id} className="p-3 rounded-lg border border-gray-200 dark:border-gray-700 text-xs">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-bold text-blue-600 dark:text-blue-400 uppercase">{ev.action}</span>
                    <span className="text-gray-400 text-[11px]">{new Date(ev.timestamp).toLocaleTimeString()}</span>
                  </div>
                  <div className="text-gray-700 dark:text-gray-300 font-medium mb-1">
                    {ev.reason}
                  </div>
                  <div className="flex justify-between items-center text-[10px] text-gray-500 dark:text-gray-400">
                    <span>Host: {ev.host_id} ({ev.provider?.toUpperCase()})</span>
                    <span className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 font-mono">{ev.status}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
