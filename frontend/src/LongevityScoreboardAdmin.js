import React, { useState, useEffect } from 'react';

const LongevityScoreboardAdmin = ({ user, onNavigate, onLogoClick }) => {
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [cohorts, setCohorts] = useState([]);
  const [constants, setConstants] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  // Forms
  const [biologicalAgeForm, setBiologicalAgeForm] = useState({
    patient_id: '',
    method: 'epigenetic',
    biological_age_years: '',
    measured_at: '',
    source: { lab: '', test_type: '', confidence_score: '' }
  });

  const [visibilityForm, setVisibilityForm] = useState({
    patient_id: '',
    opt_in: false,
    identity: 'avatar'
  });

  const [avatarUpload, setAvatarUpload] = useState({
    patient_id: '',
    file: null
  });

  // Configuration
  const SUPABASE_URL = process.env.REACT_APP_SUPABASE_URL;

  useEffect(() => {
    if (user?.role === 'admin') {
      fetchData();
    }
  }, [user]);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchPatients(),
        fetchCohorts(),
        fetchConstants()
      ]);
    } catch (error) {
      console.error('Error fetching admin data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPatients = async () => {
    try {
      // Get patients from existing admin API
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/patients`, {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setPatients(data);
      }
    } catch (error) {
      console.error('Error fetching patients:', error);
    }
  };

  const fetchCohorts = async () => {
    try {
      const response = await fetch(`${SUPABASE_URL}/functions/v1/longevity/cohorts`, {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setCohorts(data.cohorts || []);
      }
    } catch (error) {
      console.error('Error fetching cohorts:', error);
    }
  };

  const fetchConstants = async () => {
    try {
      const response = await fetch(`${SUPABASE_URL}/functions/v1/longevity/constants`, {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setConstants(data.constants || {});
      }
    } catch (error) {
      console.error('Error fetching constants:', error);
    }
  };

  const handleAddBiologicalAge = async (e) => {
    e.preventDefault();
    try {
      const formData = {
        ...biologicalAgeForm,
        biological_age_years: parseFloat(biologicalAgeForm.biological_age_years),
        source: {
          lab: biologicalAgeForm.source.lab,
          test_type: biologicalAgeForm.source.test_type,
          confidence_score: parseFloat(biologicalAgeForm.source.confidence_score)
        }
      };

      const response = await fetch(`${SUPABASE_URL}/functions/v1/longevity/biological-age`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        const result = await response.json();
        alert('Biological age recorded and score computed successfully!');
        
        // Reset form
        setBiologicalAgeForm({
          patient_id: '',
          method: 'epigenetic',
          biological_age_years: '',
          measured_at: '',
          source: { lab: '', test_type: '', confidence_score: '' }
        });

        // Refresh data
        fetchData();
      } else {
        const error = await response.json();
        alert(`Error: ${error.error}`);
      }
    } catch (error) {
      console.error('Error adding biological age:', error);
      alert('Error recording biological age');
    }
  };

  const handleComputeScore = async (patientId) => {
    try {
      const response = await fetch(`${SUPABASE_URL}/functions/v1/longevity/compute-now`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ patient_id: patientId })
      });

      if (response.ok) {
        const result = await response.json();
        alert(`Score computed successfully: ${result.data?.score || 'N/A'}`);
        fetchData();
      } else {
        const error = await response.json();
        alert(`Error: ${error.error}`);
      }
    } catch (error) {
      console.error('Error computing score:', error);
      alert('Error computing score');
    }
  };

  const handleUpdateVisibility = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${SUPABASE_URL}/functions/v1/longevity/publish`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(visibilityForm)
      });

      if (response.ok) {
        alert('Visibility settings updated successfully!');
        
        // Reset form
        setVisibilityForm({
          patient_id: '',
          opt_in: false,
          identity: 'avatar'
        });

        fetchData();
      } else {
        const error = await response.json();
        alert(`Error: ${error.error}`);
      }
    } catch (error) {
      console.error('Error updating visibility:', error);
      alert('Error updating visibility settings');
    }
  };

  const handlePinPatient = async (patientId, pinned) => {
    try {
      const response = await fetch(`${SUPABASE_URL}/functions/v1/longevity/pin`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ patient_id: patientId, pinned })
      });

      if (response.ok) {
        alert(`Patient ${pinned ? 'pinned' : 'unpinned'} successfully!`);
        fetchData();
      } else {
        const error = await response.json();
        alert(`Error: ${error.error}`);
      }
    } catch (error) {
      console.error('Error pinning patient:', error);
      alert('Error updating pin status');
    }
  };

  const handleUpdateConstants = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${SUPABASE_URL}/functions/v1/longevity/constants`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ constants })
      });

      if (response.ok) {
        alert('Scoring constants updated successfully!');
        fetchData();
      } else {
        const error = await response.json();
        alert(`Error: ${error.error}`);
      }
    } catch (error) {
      console.error('Error updating constants:', error);
      alert('Error updating constants');
    }
  };

  const handleAvatarUpload = async (e) => {
    e.preventDefault();
    // Note: This is a simplified version. In production, you'd upload to Supabase Storage
    alert('Avatar upload functionality would be implemented here with Supabase Storage');
  };

  if (user?.role !== 'admin') {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-medium text-red-600 mb-4">Access Denied</h2>
          <p className="text-gray-600">Admin access required</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold mx-auto mb-4"></div>
          <p className="text-gray-600">Loading longevity scoreboard admin...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream">
      {/* Header */}
      <div className="app-header">
        <div className="flex items-center space-x-2 cursor-pointer" onClick={onLogoClick || (() => onNavigate('admin'))}>
          <img 
            src="/brand/kinaura-symbol.svg" 
            alt="KinAura" 
            className="ka-logo w-8 h-8"
          />
          <span className="kinaura-logo-text hover:text-gold transition-colors">KinAura</span>
        </div>
        <div className="flex items-center space-x-4">
          <button 
            onClick={() => onNavigate('admin')}
            className="pill-button text-sm"
          >
            ADMIN PANEL
          </button>
          <button 
            onClick={() => onNavigate('menu')}
            className="hamburger-menu"
          >
            <div className="hamburger-line"></div>
            <div className="hamburger-line"></div>
            <div className="hamburger-line"></div>
          </button>
        </div>
      </div>

      <div className="p-6">
        {/* Page Title */}
        <div className="text-center mb-6">
          <h1 className="text-2xl kinaura-heading mb-2">Longevity Scoreboard Admin</h1>
          <p className="text-gray-600 text-sm kinaura-body">Manage patient scores, visibility, and settings</p>
        </div>

        {/* Tabs */}
        <div className="cream-card mb-6">
          <div className="flex space-x-1 overflow-x-auto">
            {[
              { id: 'overview', label: 'Overview', icon: '📊' },
              { id: 'biological-age', label: 'Bio Age', icon: '🧬' },
              { id: 'visibility', label: 'Visibility', icon: '👁️' },
              { id: 'settings', label: 'Settings', icon: '⚙️' },
              { id: 'cohorts', label: 'Cohorts', icon: '👥' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'bg-gold text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="cream-card text-center">
                <div className="text-2xl font-bold text-gold mb-1">{patients.length}</div>
                <div className="text-sm text-gray-600">Total Patients</div>
              </div>
              <div className="cream-card text-center">
                <div className="text-2xl font-bold text-gold mb-1">{cohorts.length}</div>
                <div className="text-sm text-gray-600">Active Cohorts</div>
              </div>
              <div className="cream-card text-center">
                <div className="text-2xl font-bold text-gold mb-1">
                  {cohorts.reduce((sum, c) => sum + c.patient_count, 0)}
                </div>
                <div className="text-sm text-gray-600">Scored Patients</div>
              </div>
            </div>

            {/* Recent Patients */}
            <div className="cream-card">
              <h3 className="text-lg font-medium mb-4 kinaura-subheading">Patient Management</h3>
              <div className="space-y-3">
                {patients.slice(0, 10).map((patient) => (
                  <div key={patient.id} className="flex items-center justify-between p-3 bg-white rounded-lg border">
                    <div>
                      <div className="font-medium">{patient.full_name}</div>
                      <div className="text-sm text-gray-600">{patient.email}</div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleComputeScore(patient.id)}
                        className="text-sm bg-blue-100 text-blue-700 px-3 py-1 rounded-full hover:bg-blue-200 transition-colors"
                      >
                        Compute Score
                      </button>
                      <button
                        onClick={() => setSelectedPatient(patient)}
                        className="text-sm bg-gray-100 text-gray-700 px-3 py-1 rounded-full hover:bg-gray-200 transition-colors"
                      >
                        Manage
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Biological Age Tab */}
        {activeTab === 'biological-age' && (
          <div className="cream-card">
            <h3 className="text-lg font-medium mb-4 kinaura-subheading">Add Biological Age Measurement</h3>
            <form onSubmit={handleAddBiologicalAge} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Patient</label>
                <select
                  value={biologicalAgeForm.patient_id}
                  onChange={(e) => setBiologicalAgeForm({...biologicalAgeForm, patient_id: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-gold"
                  required
                >
                  <option value="">Select Patient</option>
                  {patients.map((patient) => (
                    <option key={patient.id} value={patient.id}>
                      {patient.full_name} ({patient.email})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Method</label>
                  <select
                    value={biologicalAgeForm.method}
                    onChange={(e) => setBiologicalAgeForm({...biologicalAgeForm, method: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-gold"
                    required
                  >
                    <option value="epigenetic">Epigenetic</option>
                    <option value="blood">Blood Panel</option>
                    <option value="saliva">Saliva Test</option>
                    <option value="device">Device Measurement</option>
                    <option value="composite">Composite Score</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Biological Age (years)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="150"
                    value={biologicalAgeForm.biological_age_years}
                    onChange={(e) => setBiologicalAgeForm({...biologicalAgeForm, biological_age_years: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-gold"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Lab/Provider</label>
                  <input
                    type="text"
                    value={biologicalAgeForm.source.lab}
                    onChange={(e) => setBiologicalAgeForm({
                      ...biologicalAgeForm,
                      source: {...biologicalAgeForm.source, lab: e.target.value}
                    })}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-gold"
                    placeholder="e.g., TruAge Labs"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Test Type</label>
                  <input
                    type="text"
                    value={biologicalAgeForm.source.test_type}
                    onChange={(e) => setBiologicalAgeForm({
                      ...biologicalAgeForm,
                      source: {...biologicalAgeForm.source, test_type: e.target.value}
                    })}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-gold"
                    placeholder="e.g., DNA Methylation Panel"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Confidence Score</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={biologicalAgeForm.source.confidence_score}
                    onChange={(e) => setBiologicalAgeForm({
                      ...biologicalAgeForm,
                      source: {...biologicalAgeForm.source, confidence_score: e.target.value}
                    })}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-gold"
                    placeholder="0-100"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Measurement Date (optional)</label>
                <input
                  type="datetime-local"
                  value={biologicalAgeForm.measured_at}
                  onChange={(e) => setBiologicalAgeForm({...biologicalAgeForm, measured_at: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-gold"
                />
              </div>

              <button
                type="submit"
                className="w-full bg-gold text-white py-3 px-4 rounded-lg hover:bg-yellow-600 transition-colors font-medium"
              >
                Record Biological Age & Compute Score
              </button>
            </form>
          </div>
        )}

        {/* Visibility Tab */}
        {activeTab === 'visibility' && (
          <div className="cream-card">
            <h3 className="text-lg font-medium mb-4 kinaura-subheading">Leaderboard Visibility Settings</h3>
            <form onSubmit={handleUpdateVisibility} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Patient</label>
                <select
                  value={visibilityForm.patient_id}
                  onChange={(e) => setVisibilityForm({...visibilityForm, patient_id: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-gold"
                  required
                >
                  <option value="">Select Patient</option>
                  {patients.map((patient) => (
                    <option key={patient.id} value={patient.id}>
                      {patient.full_name} ({patient.email})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={visibilityForm.opt_in}
                    onChange={(e) => setVisibilityForm({...visibilityForm, opt_in: e.target.checked})}
                    className="w-4 h-4 text-gold border-gray-300 rounded focus:ring-gold"
                  />
                  <span className="text-sm font-medium text-gray-700">Show on Public Leaderboard</span>
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Identity Display</label>
                <select
                  value={visibilityForm.identity}
                  onChange={(e) => setVisibilityForm({...visibilityForm, identity: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-gold"
                >
                  <option value="name">Real Name (partial)</option>
                  <option value="avatar">Avatar + First Name</option>
                  <option value="anonymous">Anonymous Handle</option>
                </select>
              </div>

              <button
                type="submit"
                className="w-full bg-gold text-white py-3 px-4 rounded-lg hover:bg-yellow-600 transition-colors font-medium"
              >
                Update Visibility Settings
              </button>
            </form>

            {/* Pin Management */}
            <div className="mt-8 pt-6 border-t border-gray-200">
              <h4 className="text-md font-medium mb-4">Featured Patients (Pinned)</h4>
              <div className="space-y-3">
                {patients.slice(0, 5).map((patient) => (
                  <div key={patient.id} className="flex items-center justify-between p-3 bg-white rounded-lg border">
                    <div>
                      <div className="font-medium">{patient.full_name}</div>
                      <div className="text-sm text-gray-600">{patient.email}</div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handlePinPatient(patient.id, true)}
                        className="text-sm bg-gold bg-opacity-20 text-gold px-3 py-1 rounded-full hover:bg-gold hover:text-white transition-colors"
                      >
                        Pin
                      </button>
                      <button
                        onClick={() => handlePinPatient(patient.id, false)}
                        className="text-sm bg-gray-100 text-gray-700 px-3 py-1 rounded-full hover:bg-gray-200 transition-colors"
                      >
                        Unpin
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Settings Tab */}
        {activeTab === 'settings' && (
          <div className="cream-card">
            <h3 className="text-lg font-medium mb-4 kinaura-subheading">Scoring Constants</h3>
            <form onSubmit={handleUpdateConstants} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Base Score
                    <span className="text-xs text-gray-500 block">Score when delta is 0</span>
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={constants.base_score || 50}
                    onChange={(e) => setConstants({...constants, base_score: parseFloat(e.target.value)})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-gold"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Delta Multiplier
                    <span className="text-xs text-gray-500 block">Points per year advantage</span>
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={constants.delta_multiplier || 4}
                    onChange={(e) => setConstants({...constants, delta_multiplier: parseFloat(e.target.value)})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-gold"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Minimum Score</label>
                  <input
                    type="number"
                    step="0.1"
                    value={constants.min_score || 0}
                    onChange={(e) => setConstants({...constants, min_score: parseFloat(e.target.value)})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-gold"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Maximum Score</label>
                  <input
                    type="number"
                    step="0.1"
                    value={constants.max_score || 100}
                    onChange={(e) => setConstants({...constants, max_score: parseFloat(e.target.value)})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-gold"
                  />
                </div>
              </div>

              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800">
                  <strong>⚠️ Warning:</strong> Changing these constants will affect all future score calculations. 
                  Existing scores will not be automatically recalculated.
                </p>
              </div>

              <button
                type="submit"
                className="w-full bg-gold text-white py-3 px-4 rounded-lg hover:bg-yellow-600 transition-colors font-medium"
              >
                Update Scoring Constants
              </button>
            </form>
          </div>
        )}

        {/* Cohorts Tab */}
        {activeTab === 'cohorts' && (
          <div className="cream-card">
            <h3 className="text-lg font-medium mb-4 kinaura-subheading">Cohort Statistics</h3>
            <div className="space-y-4">
              {cohorts.map((cohort) => (
                <div key={cohort.cohort_key} className="p-4 bg-white rounded-lg border">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h4 className="font-medium">{cohort.description}</h4>
                      <p className="text-sm text-gray-600">{cohort.cohort_key}</p>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-lg">{cohort.patient_count}</div>
                      <div className="text-sm text-gray-600">patients</div>
                    </div>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-600">Average Score:</span>
                    <span className="font-medium">{cohort.avg_score}</span>
                  </div>
                </div>
              ))}

              {cohorts.length === 0 && (
                <div className="text-center py-8">
                  <div className="text-gray-400 mb-4">
                    <svg className="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <p className="text-gray-600 text-sm">No cohorts available yet</p>
                  <p className="text-gray-500 text-xs mt-2">Cohorts are created automatically when patients have longevity scores</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LongevityScoreboardAdmin;