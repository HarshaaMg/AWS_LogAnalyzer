import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Activity, AlertTriangle, AlertCircle, LogOut, Moon, Sun, Download, RefreshCw, Search, Upload, X, Server } from 'lucide-react';
import { Pie, Line } from 'react-chartjs-2';
import LinuxObservability from './LinuxObservability';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title
} from 'chart.js';

ChartJS.register(
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title
);

function Dashboard({ onLogout, isDarkMode, toggleDarkMode }) {
  const [activeTab, setActiveTab] = useState('observability'); // 'observability' | 'logs'
  const [stats, setStats] = useState(null);
  const [logs, setLogs] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterSeverity, setFilterSeverity] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000); // Auto-refresh every 10 seconds
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterSeverity]);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const [statsRes, logsRes, alertsRes] = await Promise.all([
        axios.get('/api/stats', { headers }),
        axios.get(`/api/logs?limit=50&severity=${filterSeverity}`, { headers }),
        axios.get('/api/alerts', { headers })
      ]);

      setStats(statsRes.data.stats);
      setLogs(logsRes.data.logs);
      setAlerts(alertsRes.data.alerts);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setLoading(true);
    await axios.post('/api/stats/refresh', {}, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    });
    await fetchData();
  };

  const downloadLogs = () => {
    const csvContent = [
      ['Timestamp', 'Level', 'Message', 'Source'].join(','),
      ...logs.map(log => [log.timestamp, log.level, `"${log.message}"`, log.source].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'logs.csv';
    a.click();
  };

  const handleFileUpload = async () => {
    if (!uploadFile) {
      setUploadResult({ error: 'Please select a file' });
      return;
    }

    setUploading(true);
    setUploadResult(null);

    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', uploadFile);

      const response = await axios.post('/api/upload', formData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      setUploadResult(response.data);
      await fetchData(); // Refresh data after upload
      setUploadFile(null);
      
      // Close modal after successful upload
      setTimeout(() => {
        setShowUploadModal(false);
        setUploadResult(null);
      }, 2000);
    } catch (error) {
      setUploadResult({ error: error.response?.data?.error || 'Upload failed' });
    } finally {
      setUploading(false);
    }
  };

  const filteredLogs = logs.filter(log =>
    log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.level.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const pieData = {
    labels: ['Errors', 'Warnings', 'Critical', 'Info'],
    datasets: [{
      data: [
        stats?.total_errors || 0,
        stats?.total_warnings || 0,
        stats?.critical_count || 0,
        (stats?.total_logs || 0) - (stats?.total_errors || 0) - (stats?.total_warnings || 0) - (stats?.critical_count || 0)
      ],
      backgroundColor: ['#ef4444', '#f59e0b', '#dc2626', '#10b981'],
      borderWidth: 0
    }]
  };

  const lineData = {
    labels: ['1h ago', '45m ago', '30m ago', '15m ago', 'Now'],
    datasets: [{
      label: 'Errors',
      data: [5, 8, 3, 10, stats?.total_errors || 0],
      borderColor: '#ef4444',
      tension: 0.4,
      fill: false
    }]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: isDarkMode ? '#f3f4f6' : '#1f2937'
        }
      }
    }
  };

  if (loading && !stats) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${isDarkMode ? 'bg-darker' : 'bg-gray-100'}`}>
        <div className="text-center">
          <Activity className="w-12 h-12 animate-spin mx-auto text-primary" />
          <p className={`mt-4 ${isDarkMode ? 'text-white' : 'text-gray-700'}`}>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen ${isDarkMode ? 'bg-darker' : 'bg-gray-100'}`}>
      {/* Header */}
      <header className={`p-4 ${isDarkMode ? 'bg-dark' : 'bg-white'} shadow-md`}>
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Activity className="w-8 h-8 text-primary" />
            <div>
              <h1 className={`text-xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-800'}`}>
                Linux Observability & Scaling Platform
              </h1>
              <p className="text-[10px] text-gray-400">AWS Cloud Log Analyzer</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center bg-gray-100 dark:bg-gray-700/60 p-1 rounded-xl gap-1">
            <button
              onClick={() => setActiveTab('observability')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                activeTab === 'observability'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : isDarkMode ? 'text-gray-300 hover:text-white' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Server className="w-3.5 h-3.5" />
              <span>Observability & Auto-Scaling</span>
            </button>
            <button
              onClick={() => setActiveTab('logs')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                activeTab === 'logs'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : isDarkMode ? 'text-gray-300 hover:text-white' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              <span>Log Analytics & Alerts</span>
            </button>
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={toggleDarkMode}
              className={`p-2 rounded-full ${isDarkMode ? 'bg-gray-700' : 'bg-gray-200'}`}
            >
              {isDarkMode ? <Sun className="w-5 h-5 text-white" /> : <Moon className="w-5 h-5" />}
            </button>
            <button
              onClick={onLogout}
              className="flex items-center gap-2 px-4 py-2 bg-danger text-white rounded-lg hover:bg-red-600 transition"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-4">
        {activeTab === 'observability' ? (
          <LinuxObservability isDarkMode={isDarkMode} />
        ) : (
          <>
            {/* Stats Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <StatCard
            icon={<Activity className="w-6 h-6" />}
            title="Total Logs"
            value={stats?.total_logs || 0}
            color="primary"
            isDarkMode={isDarkMode}
          />
          <StatCard
            icon={<AlertCircle className="w-6 h-6" />}
            title="Errors"
            value={stats?.total_errors || 0}
            color="danger"
            isDarkMode={isDarkMode}
          />
          <StatCard
            icon={<AlertTriangle className="w-6 h-6" />}
            title="Warnings"
            value={stats?.total_warnings || 0}
            color="warning"
            isDarkMode={isDarkMode}
          />
          <StatCard
            icon={<AlertCircle className="w-6 h-6" />}
            title="Critical"
            value={stats?.critical_count || 0}
            color="danger"
            isDarkMode={isDarkMode}
          />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className={`p-4 rounded-lg ${isDarkMode ? 'bg-dark' : 'bg-white'} shadow`}>
            <h3 className={`text-lg font-semibold mb-4 ${isDarkMode ? 'text-white' : 'text-gray-800'}`}>
              Log Distribution
            </h3>
            <div className="h-64">
              <Pie data={pieData} options={chartOptions} />
            </div>
          </div>
          <div className={`p-4 rounded-lg ${isDarkMode ? 'bg-dark' : 'bg-white'} shadow`}>
            <h3 className={`text-lg font-semibold mb-4 ${isDarkMode ? 'text-white' : 'text-gray-800'}`}>
              Error Trends
            </h3>
            <div className="h-64">
              <Line data={lineData} options={chartOptions} />
            </div>
          </div>
        </div>

        {/* Server Health */}
        <div className={`p-4 rounded-lg ${isDarkMode ? 'bg-dark' : 'bg-white'} shadow mb-6`}>
          <h3 className={`text-lg font-semibold mb-4 ${isDarkMode ? 'text-white' : 'text-gray-800'}`}>
            Server Health
          </h3>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
            <span className={isDarkMode ? 'text-green-400' : 'text-green-600'}>All Systems Operational</span>
          </div>
        </div>

        {/* Controls */}
        <div className={`p-4 rounded-lg ${isDarkMode ? 'bg-dark' : 'bg-white'} shadow mb-6`}>
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`} />
                <input
                  type="text"
                  placeholder="Search logs..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className={`w-full pl-10 pr-4 py-2 rounded-lg border ${
                    isDarkMode 
                      ? 'bg-gray-700 border-gray-600 text-white' 
                      : 'bg-white border-gray-300'
                  }`}
                />
              </div>
            </div>
            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
              className={`px-4 py-2 rounded-lg border ${
                isDarkMode 
                  ? 'bg-gray-700 border-gray-600 text-white' 
                  : 'bg-white border-gray-300'
              }`}
            >
              <option value="">All Levels</option>
              <option value="INFO">INFO</option>
              <option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
            <button
              onClick={handleRefresh}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-blue-600 transition"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
            <button
              onClick={downloadLogs}
              className="flex items-center gap-2 px-4 py-2 bg-success text-white rounded-lg hover:bg-green-600 transition"
            >
              <Download className="w-4 h-4" />
              Download CSV
            </button>
            <button
              onClick={() => setShowUploadModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
            >
              <Upload className="w-4 h-4" />
              Upload Log File
            </button>
          </div>
        </div>

        {/* Recent Logs */}
        <div className={`p-4 rounded-lg ${isDarkMode ? 'bg-dark' : 'bg-white'} shadow mb-6`}>
          <h3 className={`text-lg font-semibold mb-4 ${isDarkMode ? 'text-white' : 'text-gray-800'}`}>
            Recent Logs
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className={`border-b ${isDarkMode ? 'border-gray-700' : 'border-gray-200'}`}>
                  <th className={`text-left p-3 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>Timestamp</th>
                  <th className={`text-left p-3 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>Level</th>
                  <th className={`text-left p-3 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>Message</th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.slice(0, 10).map((log) => (
                  <tr key={log.log_id} className={`border-b ${isDarkMode ? 'border-gray-700' : 'border-gray-100'}`}>
                    <td className={`p-3 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="p-3">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${getLevelColor(log.level)}`}>
                        {log.level}
                      </span>
                    </td>
                    <td className={`p-3 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>{log.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Recent Alerts */}
        {alerts.length > 0 && (
          <div className={`p-4 rounded-lg ${isDarkMode ? 'bg-dark' : 'bg-white'} shadow`}>
            <h3 className={`text-lg font-semibold mb-4 ${isDarkMode ? 'text-white' : 'text-gray-800'}`}>
              Recent Alerts
            </h3>
            <div className="space-y-3">
              {alerts.slice(0, 5).map((alert) => (
                <div key={alert.alert_id} className="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-center gap-2 text-red-700 font-semibold">
                    <AlertCircle className="w-5 h-5" />
                    <span>CRITICAL ALERT</span>
                  </div>
                  <p className="text-red-600 mt-1">{alert.message}</p>
                  <p className="text-red-500 text-sm mt-1">
                    {new Date(alert.timestamp).toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
          </>
        )}
      </main>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className={`p-6 rounded-lg ${isDarkMode ? 'bg-dark' : 'bg-white'} shadow-xl max-w-md w-full mx-4`}>
            <div className="flex justify-between items-center mb-4">
              <h3 className={`text-lg font-semibold ${isDarkMode ? 'text-white' : 'text-gray-800'}`}>
                Upload Log File
              </h3>
              <button
                onClick={() => {
                  setShowUploadModal(false);
                  setUploadFile(null);
                  setUploadResult(null);
                }}
                className={`p-2 rounded-full ${isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}
              >
                <X className={`w-5 h-5 ${isDarkMode ? 'text-white' : 'text-gray-600'}`} />
              </button>
            </div>

            <div className="mb-4">
              <label className={`block mb-2 text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                Select Log File (.log, .txt, .json)
              </label>
              <input
                type="file"
                accept=".log,.txt,.json"
                onChange={(e) => setUploadFile(e.target.files[0])}
                className={`w-full p-2 rounded-lg border ${
                  isDarkMode 
                    ? 'bg-gray-700 border-gray-600 text-white' 
                    : 'bg-white border-gray-300'
                }`}
              />
            </div>

            {uploadFile && (
              <div className={`mb-4 p-3 rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-gray-100'}`}>
                <p className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                  Selected: {uploadFile.name}
                </p>
                <p className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                  Size: {(uploadFile.size / 1024).toFixed(2)} KB
                </p>
              </div>
            )}

            {uploadResult && (
              <div className={`mb-4 p-3 rounded-lg ${
                uploadResult.error 
                  ? 'bg-red-50 border border-red-200' 
                  : 'bg-green-50 border border-green-200'
              }`}>
                <p className={`text-sm ${
                  uploadResult.error ? 'text-red-600' : 'text-green-600'
                }`}>
                  {uploadResult.error || uploadResult.message}
                </p>
                {!uploadResult.error && uploadResult.logs_parsed && (
                  <div className="mt-2 text-xs text-green-600">
                    <p>Logs parsed: {uploadResult.logs_parsed}</p>
                    <p>Critical errors: {uploadResult.critical_errors}</p>
                    <p>Errors: {uploadResult.errors}</p>
                  </div>
                )}
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={handleFileUpload}
                disabled={!uploadFile || uploading}
                className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploading ? 'Uploading...' : 'Upload'}
              </button>
              <button
                onClick={() => {
                  setShowUploadModal(false);
                  setUploadFile(null);
                  setUploadResult(null);
                }}
                className={`px-4 py-2 rounded-lg border ${
                  isDarkMode 
                    ? 'border-gray-600 text-white hover:bg-gray-700' 
                    : 'border-gray-300 text-gray-700 hover:bg-gray-100'
                } transition`}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ icon, title, value, color, isDarkMode }) {
  const colorClasses = {
    primary: 'bg-blue-500',
    danger: 'bg-red-500',
    warning: 'bg-yellow-500',
    success: 'bg-green-500'
  };

  return (
    <div className={`p-4 rounded-lg ${isDarkMode ? 'bg-dark' : 'bg-white'} shadow`}>
      <div className="flex items-center gap-3">
        <div className={`p-3 rounded-lg ${colorClasses[color]} text-white`}>
          {icon}
        </div>
        <div>
          <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>{title}</p>
          <p className={`text-2xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-800'}`}>{value}</p>
        </div>
      </div>
    </div>
  );
}

function getLevelColor(level) {
  switch (level) {
    case 'CRITICAL':
      return 'bg-red-600 text-white';
    case 'ERROR':
      return 'bg-red-500 text-white';
    case 'WARNING':
      return 'bg-yellow-500 text-white';
    case 'INFO':
      return 'bg-green-500 text-white';
    default:
      return 'bg-gray-500 text-white';
  }
}

export default Dashboard;
