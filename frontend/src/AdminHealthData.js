import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

const AdminHealthData = ({ backendUrl, onNavigate }) => {
  const [patients, setPatients] = useState([]);
  const [connections, setConnections] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [patientTimeline, setPatientTimeline] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchHealthData();
  }, []);

  const fetchHealthData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // Fetch patients
      const patientsResponse = await fetch(`${backendUrl}/admin/patients`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (patientsResponse.ok) {
        const patientsData = await patientsResponse.json();
        setPatients(patientsData.patients || []);
      }

      // Fetch all health connections
      const connectionsResponse = await fetch(`${backendUrl}/admin/health/connections`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (connectionsResponse.ok) {
        const connectionsData = await connectionsResponse.json();
        setConnections(connectionsData.connections || []);
      }
    } catch (error) {
      console.error('Error fetching health data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPatientTimeline = async (patientId) => {
    try {
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/admin/health/patients/${patientId}/timeline?days=90`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const result = await response.json();
        setPatientTimeline(result.timeline || []);
        setSelectedPatient(patientId);
        setActiveTab('timeline');
      }
    } catch (error) {
      console.error('Error fetching patient timeline:', error);
    }
  };

  const exportPatientData = async (patientId) => {
    try {
      const token = localStorage.getItem('token');
      
      // Call the patient health export endpoint on behalf of the patient
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(endDate.getDate() - 365); // Export 1 year of data
      
      const response = await fetch(`${backendUrl}/engine/patients/${patientId}/metrics?date_from=${startDate.toISOString()}&date_to=${endDate.toISOString()}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const result = await response.json();
        
        // Create downloadable file
        const dataStr = JSON.stringify(result, null, 2);
        const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
        
        const exportFileDefaultName = `patient_${patientId}_health_data_${new Date().toISOString().split('T')[0]}.json`;
        
        const linkElement = document.createElement('a');
        linkElement.setAttribute('href', dataUri);
        linkElement.setAttribute('download', exportFileDefaultName);
        linkElement.click();
        
        alert('Patient health data exported successfully!');
      } else {
        const error = await response.json();
        alert(`Export failed: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error exporting patient data:', error);
      alert('Export failed');
    }
  };

  const getProviderIcon = (provider) => {
    switch(provider) {
      case 'HEALTHKIT':
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z" fill="#007AFF"/>
          </svg>
        );
      case 'WHOOP':
        return (
          <svg width="20" height="20" viewBox="0 0 100 100" fill="none">
            <circle cx="50" cy="50" r="45" fill="#FF6B6B"/>
            <circle cx="50" cy="50" r="35" fill="none" stroke="white" strokeWidth="3"/>
            <circle cx="50" cy="50" r="25" fill="none" stroke="white" strokeWidth="2"/>
            <circle cx="50" cy="50" r="15" fill="white"/>
            <text x="50" y="55" textAnchor="middle" fill="#FF6B6B" fontSize="12" fontWeight="bold">W</text>
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

  const getConnectionsByProvider = () => {
    const providerStats = connections.reduce((acc, conn) => {
      acc[conn.provider] = (acc[conn.provider] || 0) + 1;
      return acc;
    }, {});
    
    return Object.entries(providerStats).map(([provider, count]) => ({
      provider,
      count
    }));
  };

  const getMetricStats = () => {
    const metricStats = patientTimeline.reduce((acc, sample) => {
      acc[sample.metric] = (acc[sample.metric] || 0) + 1;
      return acc;
    }, {});
    
    return Object.entries(metricStats)
      .map(([metric, count]) => ({ metric, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#C8A25A]"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header with Navigation */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => onNavigate('admin')}
              className="flex items-center space-x-2 text-[#C8A25A] hover:text-[#B8925A] transition-colors"
              aria-label="Back to admin dashboard"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              <span className="font-medium">Back to Admin Dashboard</span>
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
        <h1 className="text-3xl font-bold text-[#222428] mb-2">Health Data Management</h1>
        <p className="text-gray-600">Monitor and manage patient health data integrations</p>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-lg shadow-md mb-6">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            <button
              onClick={() => setActiveTab('overview')}
              className={`py-4 px-2 border-b-2 font-medium text-sm ${
                activeTab === 'overview'
                  ? 'border-[#C8A25A] text-[#C8A25A]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab('connections')}
              className={`py-4 px-2 border-b-2 font-medium text-sm ${
                activeTab === 'connections'
                  ? 'border-[#C8A25A] text-[#C8A25A]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Connections
            </button>
            <button
              onClick={() => setActiveTab('timeline')}
              className={`py-4 px-2 border-b-2 font-medium text-sm ${
                activeTab === 'timeline'
                  ? 'border-[#C8A25A] text-[#C8A25A]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Patient Timeline
            </button>
          </nav>
        </div>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Connection Stats */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-[#222428] mb-4">Provider Connections</h2>
            <div className="space-y-4">
              {getConnectionsByProvider().map((stat, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{getProviderIcon(stat.provider)}</span>
                    <span className="font-medium text-[#222428]">{stat.provider}</span>
                  </div>
                  <span className="bg-[#C8A25A] text-white px-3 py-1 rounded-full text-sm">
                    {stat.count} patients
                  </span>
                </div>
              ))}
              {getConnectionsByProvider().length === 0 && (
                <p className="text-gray-500 text-center py-4">No connections found</p>
              )}
            </div>
          </div>

          {/* Quick Stats */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-[#222428] mb-4">System Stats</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <div className="text-3xl font-bold text-[#C8A25A]">{patients.length}</div>
                <div className="text-sm text-gray-500">Total Patients</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-[#C8A25A]">{connections.length}</div>
                <div className="text-sm text-gray-500">Active Connections</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-[#C8A25A]">
                  {connections.filter(c => c.status === 'connected').length}
                </div>
                <div className="text-sm text-gray-500">Connected</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-red-600">
                  {connections.filter(c => c.status !== 'connected').length}
                </div>
                <div className="text-sm text-gray-500">Issues</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Connections Tab */}
      {activeTab === 'connections' && (
        <div className="bg-white rounded-lg shadow-md">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-[#222428]">All Patient Connections</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Patient
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Provider
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Sync
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {connections.map((connection, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-[#222428]">
                          {connection.patient_name || 'Unknown Patient'}
                        </div>
                        <div className="text-sm text-gray-500">
                          {connection.patient_email}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        <span className="text-lg">{getProviderIcon(connection.provider)}</span>
                        <span className="text-sm text-[#222428]">{connection.provider}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        connection.status === 'connected'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {connection.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {connection.last_sync_at 
                        ? new Date(connection.last_sync_at).toLocaleDateString()
                        : 'Never'
                      }
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                      <button
                        onClick={() => fetchPatientTimeline(connection.patient_id)}
                        className="text-[#C8A25A] hover:text-[#B8925A]"
                      >
                        View Timeline
                      </button>
                      <button
                        onClick={() => exportPatientData(connection.patient_id)}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        Export
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {connections.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <p>No health connections found</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Timeline Tab */}
      {activeTab === 'timeline' && (
        <div className="space-y-6">
          {!selectedPatient ? (
            <div className="bg-white rounded-lg shadow-md p-8 text-center">
              <p className="text-gray-500 mb-4">Select a patient to view their health timeline</p>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {patients.map((patient, index) => (
                  <button
                    key={index}
                    onClick={() => fetchPatientTimeline(patient.id)}
                    className="border border-gray-200 rounded-lg p-4 text-left hover:shadow-md transition-shadow"
                  >
                    <div className="font-medium text-[#222428]">{patient.full_name}</div>
                    <div className="text-sm text-gray-500">{patient.email}</div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {/* Timeline Header */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex justify-between items-center">
                  <div>
                    <h2 className="text-xl font-semibold text-[#222428]">Patient Health Timeline</h2>
                    <p className="text-gray-600">
                      {patientTimeline.length} health data points in the last 90 days
                    </p>
                  </div>
                  <button
                    onClick={() => exportPatientData(selectedPatient)}
                    className="bg-[#C8A25A] text-white px-4 py-2 rounded-lg hover:bg-[#B8925A] transition-colors"
                  >
                    Export Data
                  </button>
                </div>
              </div>

              {/* Metric Distribution Chart */}
              {patientTimeline.length > 0 && (
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h3 className="text-lg font-semibold text-[#222428] mb-4">
                    Most Tracked Metrics
                  </h3>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={getMetricStats()}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis 
                          dataKey="metric" 
                          angle={-45}
                          textAnchor="end"
                          height={100}
                          tickFormatter={formatMetricName}
                        />
                        <YAxis />
                        <Tooltip 
                          labelFormatter={(value) => formatMetricName(value)}
                        />
                        <Bar dataKey="count" fill="#C8A25A" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {/* Timeline Data */}
              <div className="bg-white rounded-lg shadow-md">
                <div className="p-6 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-[#222428]">Recent Health Data</h3>
                </div>
                <div className="max-h-96 overflow-y-auto">
                  {patientTimeline.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <p>No health data found for this patient</p>
                    </div>
                  ) : (
                    <div className="divide-y divide-gray-200">
                      {patientTimeline.slice(0, 50).map((sample, index) => (
                        <div key={index} className="p-4 hover:bg-gray-50">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <span className="text-xl">{getMetricIcon(sample.metric)}</span>
                              <div>
                                <div className="font-medium text-[#222428]">
                                  {formatMetricName(sample.metric)}
                                </div>
                                <div className="text-sm text-gray-500">
                                  {getProviderIcon(sample.provider)} {sample.provider}
                                </div>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-lg font-semibold text-[#C8A25A]">
                                {typeof sample.value === 'number' 
                                  ? sample.value.toFixed(1) 
                                  : sample.value
                                } {sample.unit}
                              </div>
                              <div className="text-sm text-gray-500">
                                {new Date(sample.start_time).toLocaleDateString()}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default AdminHealthData;