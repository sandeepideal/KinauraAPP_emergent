import React, { useState, useEffect } from 'react';
import { LineChart, Line, ResponsiveContainer, CartesianGrid, XAxis, YAxis, Tooltip } from './components/ui/LazyChart';
import { SkeletonLoader, SkeletonCard } from './components/ui/Skeleton';
import EmptyState, { EmptyStates } from './components/ui/EmptyState';

const HealthDashboard = ({ user, backendUrl, onNavigate }) => {
  const [connections, setConnections] = useState([]);
  const [dashboardData, setDashboardData] = useState([]);
  const [selectedMetric, setSelectedMetric] = useState(null);
  const [metricData, setMetricData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showConnectModal, setShowConnectModal] = useState(false);
  const [connectingProvider, setConnectingProvider] = useState(null);

  useEffect(() => {
    fetchHealthData();
  }, []);

  const fetchHealthData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // Fetch connections
      const connectionsResponse = await fetch(`${backendUrl}/patient/health/connections`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (connectionsResponse.ok) {
        const connectionsData = await connectionsResponse.json();
        setConnections(connectionsData.connections || []);
      }

      // Fetch dashboard data
      const dashboardResponse = await fetch(`${backendUrl}/patient/health/dashboard?days=30`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (dashboardResponse.ok) {
        const dashboardResult = await dashboardResponse.json();
        setDashboardData(dashboardResult.dashboard || []);
      }
    } catch (error) {
      console.error('Error fetching health data:', error);
    } finally {
      setLoading(false);
    }
  };

  const connectProvider = async (provider, permissions, categories) => {
    try {
      setConnectingProvider(provider);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/patient/health/connect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          provider: provider,
          permissions: permissions,
          metric_categories: categories
        })
      });

      if (response.ok) {
        await fetchHealthData();
        setShowConnectModal(false);
        alert(`${provider} connected successfully!`);
      } else {
        const error = await response.json();
        alert(`Failed to connect ${provider}: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error connecting provider:', error);
      alert(`Error connecting ${provider}`);
    } finally {
      setConnectingProvider(null);
    }
  };

  const disconnectProvider = async (provider) => {
    if (!confirm(`Are you sure you want to disconnect ${provider}?`)) return;
    
    try {
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/patient/health/connections/${provider}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        await fetchHealthData();
        alert(`${provider} disconnected successfully!`);
      } else {
        const error = await response.json();
        alert(`Failed to disconnect ${provider}: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error disconnecting provider:', error);
      alert(`Error disconnecting ${provider}`);
    }
  };

  const fetchMetricData = async (metric) => {
    try {
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/patient/health/metrics/${metric}?days=30`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const result = await response.json();
        const samples = result.samples || [];
        
        // Process data for chart
        const chartData = samples.map(sample => ({
          date: new Date(sample.start_time).toLocaleDateString(),
          value: typeof sample.value === 'number' ? sample.value : parseFloat(sample.value) || 0,
          provider: sample.provider
        }));
        
        setMetricData(chartData);
        setSelectedMetric(metric);
      }
    } catch (error) {
      console.error('Error fetching metric data:', error);
    }
  };

  const exportHealthData = async () => {
    try {
      const token = localStorage.getItem('token');
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(endDate.getDate() - 90);
      
      const response = await fetch(`${backendUrl}/patient/health/export`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          format: 'json',
          date_from: startDate.toISOString(),
          date_to: endDate.toISOString()
        })
      });

      if (response.ok) {
        const result = await response.json();
        alert(`Data exported successfully! ${result.record_count} records in ${result.filename}`);
      } else {
        const error = await response.json();
        alert(`Export failed: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error exporting data:', error);
      alert('Export failed');
    }
  };

  const getProviderIcon = (provider) => {
    switch(provider) {
      case 'HEALTHKIT':
        return (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z" fill="#007AFF"/>
          </svg>
        );
      case 'WHOOP':
        return (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" fill="#FF6B6B"/>
            <path d="M8 9l2 2 4-4" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <text x="12" y="16" textAnchor="middle" fill="white" fontSize="8" fontWeight="bold">W</text>
          </svg>
        );
      default:
        return '📱';
    }
  };

  const getMetricIcon = (metric) => {
    if (metric.includes('hr') || metric.includes('heart')) return '❤️';
    if (metric.includes('sleep')) return '😴';
    if (metric.includes('steps')) return '👟';
    if (metric.includes('strain') || metric.includes('recovery')) return '💪';
    return '📊';
  };

  const formatMetricName = (metric) => {
    return metric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        {/* Header Skeleton */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              <div className="w-24 h-6 bg-ka-muted rounded animate-pulse"></div>
            </div>
            <div className="w-10 h-10 bg-ka-muted rounded animate-pulse"></div>
          </div>
          <div className="w-64 h-8 bg-ka-muted rounded animate-pulse mb-2"></div>
          <div className="w-96 h-5 bg-ka-muted rounded animate-pulse"></div>
        </div>

        {/* Connected Devices Skeleton */}
        <SkeletonCard className="mb-8" />
        
        {/* Metrics Skeleton */}
        <div className="ka-card">
          <div className="flex justify-between items-center mb-6">
            <div className="w-48 h-6 bg-ka-muted rounded animate-pulse"></div>
            <div className="w-24 h-8 bg-ka-muted rounded animate-pulse"></div>
          </div>
          <SkeletonLoader count={6} variant="list" />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header with Navigation */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => onNavigate('dashboard')}
              className="flex items-center space-x-2 text-[#C8A25A] hover:text-[#B8925A] transition-colors"
              aria-label="Back to dashboard"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              <span className="font-medium">Back to Dashboard</span>
            </button>
          </div>
          <button
            onClick={() => onNavigate('menu')}
            className="hamburger-menu"
            aria-label="Main menu"
          >
            <div className="hamburger-line"></div>
            <div className="hamburger-line"></div>
            <div className="hamburger-line"></div>
          </button>
        </div>
        <h1 className="ka-section-title">Your Wellness Tools</h1>
        <p className="ka-body-lg">Connect your devices and track your health metrics</p>
      </div>

      {/* Provider Connections */}
      <div className="ka-card mb-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="ka-section-title">Connected Devices</h2>
          <button
            onClick={() => setShowConnectModal(true)}
            className="ka-button"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="var(--ka-gold-600)" strokeWidth="1.5" className="ka-icon ka-icon--sm mr-2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Connect Device
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {connections.length === 0 ? (
            <div className="col-span-2">
              <EmptyStates.NoConnections onConnect={() => setShowConnectModal(true)} />
            </div>
          ) : (
            connections.map((connection, index) => (
              <div key={index} className="ka-card--elevated p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{getProviderIcon(connection.provider)}</span>
                    <div>
                      <h3 className="font-medium ka-text">{connection.provider}</h3>
                      <p className="text-sm ka-text-2">
                        Status: <span className={`font-medium ${
                          connection.status === 'connected' ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {connection.status}
                        </span>
                      </p>
                      {connection.last_sync_at && (
                        <p className="text-sm ka-text-2">
                          Last sync: {new Date(connection.last_sync_at).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => disconnectProvider(connection.provider)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Disconnect
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Health Metrics Grid */}
      <div className="ka-card mb-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="ka-section-title">Recent Metrics</h2>
          <button
            onClick={exportHealthData}
            className="ka-outline"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="var(--ka-gold-600)" strokeWidth="1.5" className="ka-icon ka-icon--sm mr-2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
            </svg>
            Export Data
          </button>
        </div>

        {dashboardData.length === 0 ? (
          <EmptyStates.NoData onRetry={() => fetchHealthData()} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {dashboardData.map((metric, index) => (
              <div
                key={index}
                className="ka-card--elevated p-4 cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => fetchMetricData(metric.metric)}
              >
                <div className="flex items-center space-x-3 mb-2">
                  <span className="text-xl">{getMetricIcon(metric.metric)}</span>
                  <h3 className="font-medium ka-text">{formatMetricName(metric.metric)}</h3>
                </div>
                <div className="text-2xl font-bold text-ka-brand mb-1">
                  {typeof metric.latest_value === 'number' 
                    ? metric.latest_value.toFixed(1) 
                    : metric.latest_value
                  }
                  <span className="text-sm ka-text-2 ml-1">{metric.unit}</span>
                </div>
                <div className="text-sm ka-text-2">
                  <p>Source: {getProviderIcon(metric.provider)} {metric.provider}</p>
                  <p>{metric.samples.length} samples in 30 days</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Metric Detail Chart */}
      {selectedMetric && metricData.length > 0 && (
        <div className="ka-card">
          <h2 className="ka-section-title mb-6">
            {formatMetricName(selectedMetric)} - 30 Day Trend
          </h2>
          <div className="h-64">
            <LineChart data={metricData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="var(--ka-gold-600)" strokeWidth={2} />
            </LineChart>
          </div>
        </div>
      )}

      {/* Connect Device Modal */}
      {showConnectModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-[#222428] mb-4">Connect Health Device</h3>
            
            <div className="space-y-4">
              <button
                onClick={() => connectProvider(
                  'HEALTHKIT',
                  ['read_heart_rate', 'read_steps', 'read_sleep', 'read_body_weight'],
                  ['activity', 'sleep', 'cardiometabolic', 'body_composition']
                )}
                disabled={connectingProvider === 'HEALTHKIT'}
                className="w-full border border-gray-200 rounded-lg p-4 text-left hover:shadow-md transition-shadow disabled:opacity-50"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 flex items-center justify-center">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                      <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z" fill="#007AFF"/>
                    </svg>
                  </div>
                  <div>
                    <h4 className="font-medium text-[#222428]">Apple HealthKit</h4>
                    <p className="text-sm text-gray-500">Connect Apple Health data</p>
                  </div>
                </div>
                {connectingProvider === 'HEALTHKIT' && (
                  <div className="mt-2 text-sm text-[#C8A25A]">Connecting...</div>
                )}
              </button>

              <button
                onClick={() => connectProvider(
                  'WHOOP',
                  ['read_recovery', 'read_strain', 'read_sleep', 'read_heart_rate'],
                  ['recovery', 'activity', 'sleep', 'cardiometabolic']
                )}
                disabled={connectingProvider === 'WHOOP'}
                className="w-full border border-gray-200 rounded-lg p-4 text-left hover:shadow-md transition-shadow disabled:opacity-50"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 flex items-center justify-center">
                    <svg width="32" height="32" viewBox="0 0 100 100" fill="none">
                      <circle cx="50" cy="50" r="45" fill="#FF6B6B"/>
                      <circle cx="50" cy="50" r="35" fill="none" stroke="white" strokeWidth="3"/>
                      <circle cx="50" cy="50" r="25" fill="none" stroke="white" strokeWidth="2"/>
                      <circle cx="50" cy="50" r="15" fill="white"/>
                      <text x="50" y="55" textAnchor="middle" fill="#FF6B6B" fontSize="12" fontWeight="bold">W</text>
                    </svg>
                  </div>
                  <div>
                    <h4 className="font-medium text-[#222428]">WHOOP</h4>
                    <p className="text-sm text-gray-500">Connect WHOOP fitness tracker</p>
                  </div>
                </div>
                {connectingProvider === 'WHOOP' && (
                  <div className="mt-2 text-sm text-[#C8A25A]">Connecting...</div>
                )}
              </button>
            </div>

            <div className="mt-6 flex justify-end space-x-3">
              <button
                onClick={() => setShowConnectModal(false)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HealthDashboard;