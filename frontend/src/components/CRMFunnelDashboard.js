import React, { useState, useEffect } from 'react';

const CRMFunnelDashboard = ({ backendUrl }) => {
  const [funnelData, setFunnelData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedStage, setSelectedStage] = useState(null);
  const [exportFormat, setExportFormat] = useState('json');

  const API = `${backendUrl}/api`;

  useEffect(() => {
    loadFunnelData();
  }, []);

  const loadFunnelData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const axios = (await import('axios')).default;
      
      const response = await axios.get(`${API}/admin/patients/funnel`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.data.success) {
        setFunnelData(response.data.data);
      } else {
        setError('Failed to load funnel data');
      }
    } catch (err) {
      console.error('Error loading funnel data:', err);
      setError(err.response?.data?.detail || 'Failed to load funnel data');
    } finally {
      setLoading(false);
    }
  };

  const exportFunnelData = async (format = 'csv') => {
    try {
      const token = localStorage.getItem('token');
      const axios = (await import('axios')).default;
      
      const response = await axios.get(`${API}/admin/patients/funnel?export_format=${format}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        responseType: format === 'csv' ? 'blob' : 'json'
      });

      if (format === 'csv') {
        // Create download link for CSV
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'kinaura_funnel_export.csv');
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      } else {
        // Download JSON data
        const dataStr = JSON.stringify(response.data, null, 2);
        const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
        const exportFileDefaultName = 'kinaura_funnel_export.json';
        const linkElement = document.createElement('a');
        linkElement.setAttribute('href', dataUri);
        linkElement.setAttribute('download', exportFileDefaultName);
        linkElement.click();
      }
    } catch (err) {
      console.error('Error exporting funnel data:', err);
      setError('Failed to export data');
    }
  };

  const getStageIcon = (stage) => {
    const icons = {
      leads: '🌱',
      active: '⚡',
      lapsed: '😴'
    };
    return icons[stage] || '📊';
  };

  const getStageColor = (stage) => {
    const colors = {
      leads: 'from-blue-500 to-blue-600',
      active: 'from-green-500 to-green-600', 
      lapsed: 'from-orange-500 to-orange-600'
    };
    return colors[stage] || 'from-gray-500 to-gray-600';
  };

  const formatTrendPercentage = (trend) => {
    if (trend > 0) return `+${trend}%`;
    return `${trend}%`;
  };

  const getTrendColor = (trend) => {
    if (trend > 0) return 'text-green-600';
    if (trend < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  if (loading) {
    return (
      <div className="ka-card p-6 animate-pulse">
        <div className="h-6 bg-gray-200 rounded mb-4"></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-32 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="ka-card p-6">
        <div className="text-center">
          <div className="text-red-500 mb-4">
            <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.464 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={loadFunnelData}
            className="ka-button-primary"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">CRM Patient Funnel</h2>
          <p className="text-gray-600">Track patient lifecycle stages and engagement metrics</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => exportFunnelData('csv')}
            className="ka-button-secondary flex items-center space-x-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span>Export CSV</span>
          </button>
          <button
            onClick={loadFunnelData}
            className="ka-button-primary flex items-center space-x-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Main Funnel KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Leads Card */}
        <div className="ka-card p-6 hover:shadow-lg transition-shadow cursor-pointer" onClick={() => setSelectedStage('leads')}>
          <div className={`bg-gradient-to-r ${getStageColor('leads')} rounded-lg p-4 text-white mb-4`}>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold">Leads</h3>
                <p className="text-2xl font-bold">{funnelData?.leads?.count || 0}</p>
              </div>
              <div className="text-3xl">{getStageIcon('leads')}</div>
            </div>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Trend (30d)</span>
            <span className={getTrendColor(funnelData?.trends?.leads_trend || 0)}>
              {formatTrendPercentage(funnelData?.trends?.leads_trend || 0)}
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-2">No bookings yet • Potential patients</p>
        </div>

        {/* Active Card */}
        <div className="ka-card p-6 hover:shadow-lg transition-shadow cursor-pointer" onClick={() => setSelectedStage('active')}>
          <div className={`bg-gradient-to-r ${getStageColor('active')} rounded-lg p-4 text-white mb-4`}>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold">Active</h3>
                <p className="text-2xl font-bold">{funnelData?.active?.count || 0}</p>
              </div>
              <div className="text-3xl">{getStageIcon('active')}</div>
            </div>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Trend (30d)</span>
            <span className={getTrendColor(funnelData?.trends?.active_trend || 0)}>
              {formatTrendPercentage(funnelData?.trends?.active_trend || 0)}
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-2">Booked &lt;60 days • Engaged patients</p>
        </div>

        {/* Lapsed Card */}
        <div className="ka-card p-6 hover:shadow-lg transition-shadow cursor-pointer" onClick={() => setSelectedStage('lapsed')}>
          <div className={`bg-gradient-to-r ${getStageColor('lapsed')} rounded-lg p-4 text-white mb-4`}>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold">Lapsed</h3>
                <p className="text-2xl font-bold">{funnelData?.lapsed?.count || 0}</p>
              </div>
              <div className="text-3xl">{getStageIcon('lapsed')}</div>
            </div>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Trend (30d)</span>
            <span className={getTrendColor(funnelData?.trends?.lapsed_trend || 0)}>
              {formatTrendPercentage(funnelData?.trends?.lapsed_trend || 0)}
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-2">≥60 days • Needs reactivation</p>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="ka-card p-6">
        <h3 className="text-lg font-semibold mb-4">Funnel Analytics</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-[#C8A25A]">{funnelData?.totals?.total_patients || 0}</p>
            <p className="text-sm text-gray-600">Total Patients</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">{funnelData?.totals?.conversion_rate || 0}%</p>
            <p className="text-sm text-gray-600">Conversion Rate</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-orange-600">{funnelData?.totals?.lapse_rate || 0}%</p>
            <p className="text-sm text-gray-600">Lapse Rate</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-600">
              {Math.round(((funnelData?.active?.count || 0) / Math.max(1, (funnelData?.totals?.total_patients || 1))) * 100)}%
            </p>
            <p className="text-sm text-gray-600">Active Rate</p>
          </div>
        </div>
      </div>

      {/* Patient Details Modal */}
      {selectedStage && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[80vh] overflow-hidden">
            <div className="bg-gradient-to-r from-[#C8A25A] to-[#E6C78A] p-6 text-white">
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="text-xl font-bold capitalize">{selectedStage} Patients</h3>
                  <p className="opacity-90">
                    {funnelData?.[selectedStage]?.count || 0} patients in this stage
                  </p>
                </div>
                <button
                  onClick={() => setSelectedStage(null)}
                  className="text-white hover:text-gray-200 transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="p-6 overflow-y-auto max-h-96">
              {funnelData?.[selectedStage]?.patients?.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-4xl mb-4">{getStageIcon(selectedStage)}</div>
                  <p className="text-gray-600">No patients in this stage</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {funnelData?.[selectedStage]?.patients?.map((patient) => (
                    <div key={patient.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="font-semibold text-gray-900">{patient.full_name}</h4>
                          <p className="text-gray-600">{patient.email}</p>
                          <div className="flex space-x-4 mt-2 text-sm text-gray-500">
                            <span>Bookings: {patient.total_bookings || 0}</span>
                            <span>Score: {patient.engagement_score || 0}/100</span>
                            {patient.last_login && (
                              <span>Last login: {new Date(patient.last_login).toLocaleDateString()}</span>
                            )}
                          </div>
                        </div>
                        <div className="text-right">
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            patient.lifecycle_stage === 'active' ? 'bg-green-100 text-green-800' :
                            patient.lifecycle_stage === 'lapsed' ? 'bg-orange-100 text-orange-800' :
                            'bg-blue-100 text-blue-800'
                          }`}>
                            {patient.lifecycle_stage || 'lead'}
                          </span>
                          {patient.membership_tier && (
                            <p className="text-xs text-gray-500 mt-1">{patient.membership_tier}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CRMFunnelDashboard;