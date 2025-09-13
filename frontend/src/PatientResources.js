import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL ? `${process.env.REACT_APP_BACKEND_URL}/api` : 'http://localhost:8001/api';

const PatientResources = ({ user, onNavigate, onLogoClick }) => {
  const [activeTab, setActiveTab] = useState('reports');
  const [files, setFiles] = useState([]);
  const [beforeAfterImages, setBeforeAfterImages] = useState([]);
  const [questionnaires, setQuestionnaires] = useState([]);
  const [patientFiles, setPatientFiles] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchPatientFiles();
  }, []);

  const fetchPatientFiles = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      if (token) {
        const response = await axios.get(`${API}/patient/files`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setPatientFiles(response.data);
      }
    } catch (error) {
      console.error('Error fetching patient files:', error);
    } finally {
      setLoading(false);
    }
  };

  // Organize files by category for display
  const organizeFilesByCategory = () => {
    const organized = {};
    patientFiles.forEach(file => {
      const category = file.file_category || 'general';
      if (!organized[category]) organized[category] = [];
      organized[category].push(file);
    });
    return organized;
  };

  const organizedFiles = organizeFilesByCategory();

  // Mock data for demonstration
  const mockReports = [
    {
      id: 1,
      name: 'Blood Analysis Report',
      date: '2024-01-15',
      type: 'Laboratory',
      doctor: 'Dr. Rossi',
      status: 'reviewed'
    },
    {
      id: 2,
      name: 'Hormonal Panel',
      date: '2024-01-10',
      type: 'Endocrinology',
      doctor: 'Dr. Bianchi',
      status: 'pending'
    },
    {
      id: 3,
      name: 'Oligoscan Trace Elements',
      date: '2024-01-05',
      type: 'Diagnostic',
      doctor: 'Dr. Verdi',
      status: 'reviewed'
    }
  ];

  const mockBeforeAfter = [
    {
      id: 1,
      treatment: 'Ozone Therapy',
      date: '2024-01-20',
      beforeImage: 'https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=150&h=150&fit=crop',
      afterImage: 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=150&h=150&fit=crop',
      notes: 'Significant improvement in skin texture and hydration'
    },
    {
      id: 2,
      treatment: 'IV Therapy',
      date: '2024-01-15',
      beforeImage: 'https://images.unsplash.com/photo-1559757175-0eb30cd8c063?w=150&h=150&fit=crop',
      afterImage: 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=150&h=150&fit=crop',
      notes: 'Enhanced skin radiance and reduced inflammation markers'
    }
  ];

  const mockQuestionnaires = [
    {
      id: 1,
      title: 'Lifestyle & Wellness Assessment',
      description: 'Comprehensive evaluation of sleep, stress, diet, and sun exposure',
      status: 'completed',
      completedDate: '2024-01-18'
    },
    {
      id: 2,
      title: 'Skincare Routine Analysis',
      description: 'Details about current cosmetic products and skincare habits',
      status: 'pending',
      dueDate: '2024-01-25'
    },
    {
      id: 3,
      title: 'Nutritional Habits Survey',
      description: 'Detailed analysis of dietary preferences and restrictions',
      status: 'available',
      estimatedTime: '10 minutes'
    }
  ];

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Simulate file upload
      const newFile = {
        id: Date.now(),
        name: file.name,
        date: new Date().toISOString().split('T')[0],
        type: 'Uploaded',
        status: 'processing'
      };
      setFiles([...files, newFile]);
    }
  };

  const TabButton = ({ id, label, active, onClick }) => (
    <button
      onClick={() => onClick(id)}
      className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
        active 
          ? 'pill-button' 
          : 'bg-white border border-gray-300 text-gray-600 hover:bg-gray-50'
      }`}
    >
      {label}
    </button>
  );

  return (
    <div className="min-h-screen bg-cream relative">
      {/* Kintsugi Background Lines */}
      <div className="kintsugi-lines">
        <svg viewBox="0 0 400 800" className="w-full h-full">
          <path d="M50,100 Q200,150 350,100 T600,150" className="kintsugi-gold"/>
          <path d="M0,300 Q150,250 300,300 T500,250" className="kintsugi-gold"/>
          <path d="M100,500 Q250,450 400,500 T700,450" className="kintsugi-gold"/>
          <path d="M20,700 Q180,650 340,700 T620,650" className="kintsugi-gold"/>
        </svg>
      </div>

      {/* Header */}
      <div className="app-header content-above-kintsugi">
        <div className="flex items-center space-x-4">
          <button 
            onClick={() => onNavigate('dashboard')}
            className="text-black text-xl"
          >
            ←
          </button>
          <span className="kinaura-logo-text">Patient Resources</span>
        </div>
        <button 
          onClick={() => onNavigate('menu')}
          className="hamburger-menu"
        >
          <div className="hamburger-line"></div>
          <div className="hamburger-line"></div>
          <div className="hamburger-line"></div>
        </button>
      </div>

      <div className="p-6 content-above-kintsugi">
        {/* Tab Navigation */}
        <div className="flex space-x-3 mb-6 overflow-x-auto">
          <TabButton 
            id="reports" 
            label="📄 Reports" 
            active={activeTab === 'reports'} 
            onClick={setActiveTab} 
          />
          <TabButton 
            id="images" 
            label="📸 Before/After" 
            active={activeTab === 'images'} 
            onClick={setActiveTab} 
          />
          <TabButton 
            id="questionnaires" 
            label="📝 Questionnaires" 
            active={activeTab === 'questionnaires'} 
            onClick={setActiveTab} 
          />
        </div>

        {/* Reports Tab */}
        {activeTab === 'reports' && (
          <div className="space-y-4">
            {/* Clinic Files Section */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium mb-4 kinaura-subheading">Files from Your Healthcare Provider</h3>
              
              {loading && (
                <div className="cream-card text-center py-4">
                  <div className="text-sm text-gray-500">Loading your files...</div>
                </div>
              )}

              {Object.keys(organizedFiles).length > 0 ? (
                Object.entries(organizedFiles).map(([category, categoryFiles]) => (
                  <div key={category} className="cream-card">
                    <h4 className="text-md font-medium text-gray-700 mb-3 capitalize kinaura-subheading">
                      {category.replace('_', ' ')} ({categoryFiles.length} files)
                    </h4>
                    <div className="space-y-3">
                      {categoryFiles.map((file) => (
                        <div key={file.id} className="treatment-item group hover:bg-gray-50 p-3 rounded border border-gray-100">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <div className="flex items-center space-x-2 mb-2">
                                <h5 className="font-medium text-black kinaura-body">{file.filename}</h5>
                                <span className={`px-2 py-1 text-xs rounded-full ${
                                  file.file_type === 'test_result' ? 'bg-blue-100 text-blue-800' :
                                  file.file_type === 'image' ? 'bg-green-100 text-green-800' :
                                  file.file_type === 'report' ? 'bg-purple-100 text-purple-800' :
                                  'bg-gray-100 text-gray-800'
                                }`}>
                                  {file.file_type.replace('_', ' ')}
                                </span>
                              </div>
                              {file.description && (
                                <p className="text-sm text-gray-600 mb-2 kinaura-body">{file.description}</p>
                              )}
                              {file.tags && file.tags.length > 0 && (
                                <div className="flex flex-wrap gap-1 mb-2">
                                  {file.tags.map((tag, index) => (
                                    <span key={index} className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                              )}
                              <div className="text-xs text-gold kinaura-body">
                                Uploaded: {new Date(file.upload_date).toLocaleDateString('it-IT')}
                              </div>
                            </div>
                            <button className="pill-button-small">
                              View File
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))
              ) : !loading && (
                <div className="cream-card text-center py-8">
                  <div className="text-gold text-4xl mb-3">📄</div>
                  <p className="text-gray-600 kinaura-body mb-2">No files from your healthcare provider yet.</p>
                  <p className="text-sm text-gray-500 kinaura-body">Test results, reports, and images shared by your clinic will appear here.</p>
                </div>
              )}
            </div>

            {/* Upload Section */}
            <div className="cream-card">
              <h3 className="text-lg font-medium mb-4 kinaura-subheading">Upload New Report</h3>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <input
                  type="file"
                  id="file-upload"
                  className="hidden"
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={handleFileUpload}
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  <div className="text-gold text-4xl mb-2">📎</div>
                  <p className="text-sm text-gray-600 mb-2 kinaura-body">
                    Upload medical reports, lab results, or diagnostic tests
                  </p>
                  <p className="text-xs text-gray-500 kinaura-body">
                    Supported formats: PDF, JPG, PNG
                  </p>
                </label>
              </div>
            </div>

            {/* Reports List */}
            <div className="cream-card">
              <h3 className="text-lg font-medium mb-4 kinaura-subheading">Medical Reports</h3>
              <div className="space-y-3">
                {mockReports.map((report) => (
                  <div key={report.id} className="treatment-item">
                    <div className="flex justify-between items-center">
                      <div className="flex-1">
                        <h4 className="font-medium text-sm kinaura-body">{report.name}</h4>
                        <p className="text-xs text-gray-600 kinaura-body">
                          {report.date} • {report.type} • {report.doctor}
                        </p>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          report.status === 'reviewed' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {report.status}
                        </span>
                        <button className="text-gold hover:text-yellow-600">
                          👁️
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Before/After Images Tab */}
        {activeTab === 'images' && (
          <div className="space-y-4">
            <div className="cream-card">
              <h3 className="text-lg font-medium mb-4 kinaura-subheading">Treatment Progress</h3>
              <div className="space-y-6">
                {mockBeforeAfter.map((comparison) => (
                  <div key={comparison.id} className="border-b border-gray-200 pb-6 last:border-b-0">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h4 className="font-medium text-sm kinaura-body">{comparison.treatment}</h4>
                        <p className="text-xs text-gray-600 kinaura-body">{comparison.date}</p>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 mb-3">
                      <div className="text-center">
                        <p className="text-xs text-gray-600 mb-2 kinaura-subheading">BEFORE</p>
                        <img 
                          src={comparison.beforeImage} 
                          alt="Before treatment"
                          className="w-full h-32 object-cover rounded-lg"
                        />
                      </div>
                      <div className="text-center">
                        <p className="text-xs text-gray-600 mb-2 kinaura-subheading">AFTER</p>
                        <img 
                          src={comparison.afterImage} 
                          alt="After treatment"
                          className="w-full h-32 object-cover rounded-lg"
                        />
                      </div>
                    </div>
                    
                    <p className="text-sm text-gray-700 kinaura-body italic">
                      "{comparison.notes}"
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Questionnaires Tab */}
        {activeTab === 'questionnaires' && (
          <div className="space-y-4">
            <div className="cream-card">
              <h3 className="text-lg font-medium mb-4 kinaura-subheading">Health Assessments</h3>
              <div className="space-y-4">
                {mockQuestionnaires.map((questionnaire) => (
                  <div key={questionnaire.id} className="treatment-item">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h4 className="font-medium text-sm kinaura-body">{questionnaire.title}</h4>
                        <p className="text-xs text-gray-600 mb-2 kinaura-body">
                          {questionnaire.description}
                        </p>
                        <div className="flex items-center space-x-4 text-xs text-gray-500">
                          {questionnaire.status === 'completed' && (
                            <span>Completed: {questionnaire.completedDate}</span>
                          )}
                          {questionnaire.status === 'pending' && (
                            <span>Due: {questionnaire.dueDate}</span>
                          )}
                          {questionnaire.status === 'available' && (
                            <span>Est. time: {questionnaire.estimatedTime}</span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          questionnaire.status === 'completed' 
                            ? 'bg-green-100 text-green-800'
                            : questionnaire.status === 'pending'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-blue-100 text-blue-800'
                        }`}>
                          {questionnaire.status}
                        </span>
                        {questionnaire.status !== 'completed' && (
                          <button className="text-gold hover:text-yellow-600 text-sm">
                            Start →
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Floating Action Buttons */}
      <button className="floating-action floating-chat">
        <span className="text-lg">💬</span>
      </button>
      <button className="floating-action floating-calendar">
        <span className="text-lg">📅</span>
      </button>
    </div>
  );
};

export default PatientResources;