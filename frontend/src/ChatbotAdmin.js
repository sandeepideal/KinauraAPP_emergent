import React, { useState, useEffect } from 'react';

const ChatbotAdmin = ({ backendUrl }) => {
  const [knowledgeBase, setKnowledgeBase] = useState([]);
  const [chatbotConfig, setChatbotConfig] = useState(null);
  const [configHistory, setConfigHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('knowledge-base');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  
  // Enhanced RAG monitoring state
  const [analytics, setAnalytics] = useState(null);
  const [unresolvedQueries, setUnresolvedQueries] = useState([]);
  const [knowledgeGaps, setKnowledgeGaps] = useState([]);
  const [ragTestResult, setRagTestResult] = useState(null);
  const [testQuery, setTestQuery] = useState('');
  
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    category: 'treatments',
    tags: [],
    source_type: 'admin_created'
  });
  const [configFormData, setConfigFormData] = useState({
    system_prompt: ''
  });
  const [newTag, setNewTag] = useState('');
  const [uploadPreview, setUploadPreview] = useState(null);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [pendingMarkdownCount, setPendingMarkdownCount] = useState(0);
  const [bulkApproveLoading, setBulkApproveLoading] = useState(false);

  const categories = [
    { value: 'treatments', label: 'Treatments & Services' },
    { value: 'policies', label: 'Policies & Procedures' },
    { value: 'faq', label: 'Frequently Asked Questions' },
    { value: 'general', label: 'General Information' },
    { value: 'booking', label: 'Booking & Appointments' }
  ];

  useEffect(() => {
    if (activeTab === 'knowledge-base') {
      fetchKnowledgeBase();
      fetchPendingMarkdownCount();
    } else if (activeTab === 'configuration') {
      fetchChatbotConfig();
      fetchConfigHistory();
    } else if (activeTab === 'rag-analytics') {
      fetchRagAnalytics();
    } else if (activeTab === 'unresolved-queries') {
      fetchUnresolvedQueries();
    } else if (activeTab === 'knowledge-gaps') {
      fetchKnowledgeGaps();
    }
  }, [activeTab]);

  // Enhanced fetch functions for RAG monitoring
  const fetchRagAnalytics = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${backendUrl}/admin/chat/analytics?days=30`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      }
    } catch (error) {
      console.error('Error fetching RAG analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUnresolvedQueries = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${backendUrl}/admin/chat/unresolved-queries?limit=50`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setUnresolvedQueries(data.unresolved_queries || []);
      }
    } catch (error) {
      console.error('Error fetching unresolved queries:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchKnowledgeGaps = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${backendUrl}/admin/chat/knowledge-gaps`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setKnowledgeGaps(data.knowledge_gaps || []);
      }
    } catch (error) {
      console.error('Error fetching knowledge gaps:', error);
    } finally {
      setLoading(false);
    }
  };

  const testRagSystem = async () => {
    if (!testQuery.trim()) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${backendUrl}/admin/chat/test-rag`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          test_query: testQuery,
          language: 'en'
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        setRagTestResult(result);
      }
    } catch (error) {
      console.error('Error testing RAG system:', error);
    }
  };

  const markQueryResolved = async (queryId, resolutionNotes) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${backendUrl}/admin/chat/unresolved-queries/${queryId}/resolve`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ resolution_notes: resolutionNotes })
      });
      
      if (response.ok) {
        // Refresh unresolved queries
        fetchUnresolvedQueries();
      }
    } catch (error) {
      console.error('Error marking query as resolved:', error);
    }
  };

  const fetchKnowledgeBase = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      console.log('Fetching knowledge base items from:', `${backendUrl}/admin/knowledge-base`);
      console.log('Using token:', token ? `${token.substring(0, 20)}...` : 'No token found');
      
      const response = await fetch(`${backendUrl}/admin/knowledge-base`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      console.log('Fetch response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('Knowledge base data received:', data);
        console.log('Data type:', Array.isArray(data) ? 'Array' : typeof data);
        console.log('Data length:', Array.isArray(data) ? data.length : 'N/A');
        setKnowledgeBase(data || []);
      } else {
        const errorText = await response.text();
        console.error('Failed to fetch knowledge base:', response.status, errorText);
        
        if (response.status === 403) {
          alert('Admin access required. Please ensure you are logged in as an admin user.');
        } else if (response.status === 401) {
          alert('Authentication failed. Please log in again.');
        } else {
          alert(`Failed to fetch knowledge base: ${response.status}`);
        }
        setKnowledgeBase([]);
      }
    } catch (error) {
      console.error('Error fetching knowledge base:', error);
      alert('Network error while fetching knowledge base');
      setKnowledgeBase([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchChatbotConfig = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/admin/chatbot/config`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setChatbotConfig(data.config);
        setConfigFormData({
          system_prompt: data.config?.system_prompt || ''
        });
      }
    } catch (error) {
      console.error('Error fetching chatbot config:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPendingMarkdownCount = async () => {
    try {
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/admin/knowledge-base/pending-markdown-count`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setPendingMarkdownCount(data.pending_count || 0);
      }
    } catch (error) {
      console.error('Error fetching pending markdown count:', error);
    }
  };

  const handleBulkApproveMarkdown = async () => {
    if (pendingMarkdownCount === 0) {
      alert('No pending markdown items to approve');
      return;
    }

    const confirmed = window.confirm(
      `Are you sure you want to approve all ${pendingMarkdownCount} pending markdown knowledge base items at once?`
    );
    
    if (!confirmed) return;

    try {
      setBulkApproveLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/admin/knowledge-base/bulk-approve-markdown`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const result = await response.json();
        alert(`✅ Successfully approved ${result.approved_count} markdown knowledge base items!`);
        
        // Refresh data
        await fetchKnowledgeBase();
        await fetchPendingMarkdownCount();
      } else {
        const error = await response.text();
        alert(`Failed to bulk approve items: ${error}`);
      }
    } catch (error) {
      console.error('Error bulk approving markdown items:', error);
      alert('Error bulk approving markdown items');
    } finally {
      setBulkApproveLoading(false);
    }
  };

  const fetchConfigHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/admin/chatbot/config/history`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setConfigHistory(data.configs || []);
      }
    } catch (error) {
      console.error('Error fetching config history:', error);
    }
  };

  const handleUpdateConfig = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/admin/chatbot/config`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(configFormData)
      });

      if (response.ok) {
        setShowConfigModal(false);
        await fetchChatbotConfig();
        await fetchConfigHistory();
        alert('Chatbot configuration updated successfully!');
      } else {
        const error = await response.json();
        alert(`Failed to update configuration: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error updating configuration:', error);
      alert('Error updating configuration');
    }
  };

  const handleCreateItem = async (e) => {
    e.preventDefault();
    
    // Validate form data
    if (!formData.title.trim()) {
      alert('Please enter a title');
      return;
    }
    
    if (!formData.content.trim()) {
      alert('Please enter content');
      return;
    }
    
    try {
      const token = localStorage.getItem('token');
      
      if (!token) {
        alert('You are not logged in. Please log in as an admin user.');
        return;
      }
      
      console.log('Creating knowledge base item with data:', formData);
      console.log('Backend URL:', backendUrl);
      console.log('Using token:', token.substring(0, 20) + '...');
      
      const response = await fetch(`${backendUrl}/admin/knowledge-base`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      console.log('Response status:', response.status);
      
      if (response.ok) {
        const result = await response.json();
        console.log('Success response:', result);
        setShowCreateModal(false);
        resetForm();
        await fetchKnowledgeBase();
        alert('✅ Knowledge base item created successfully!');
      } else {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        
        let errorMessage = 'Failed to create knowledge base item';
        
        try {
          const errorJson = JSON.parse(errorText);
          errorMessage = errorJson.detail || errorMessage;
        } catch {
          // Use the raw error text if it's not JSON
          errorMessage = errorText;
        }
        
        if (response.status === 403) {
          alert('❌ Admin access required. Please ensure you are logged in as an admin user.');
        } else if (response.status === 401) {
          alert('❌ Authentication failed. Please log in again as an admin.');
        } else {
          alert(`❌ ${errorMessage}`);
        }
      }
    } catch (error) {
      console.error('Error creating knowledge base item:', error);
      alert('❌ Network error while creating knowledge base item. Please check your connection.');
    }
  };

  const handleUpdateItem = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/admin/knowledge-base/${editingItem.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        setEditingItem(null);
        resetForm();
        await fetchKnowledgeBase();
      } else {
        const error = await response.json();
        alert(`Failed to update knowledge base item: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error updating knowledge base item:', error);
      alert('Error updating knowledge base item');
    }
  };

  const handleApproveItem = async (itemId) => {
    try {
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/admin/knowledge-base/${itemId}/approve`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        await fetchKnowledgeBase();
        alert('Knowledge base item approved successfully!');
      } else {
        const error = await response.json();
        alert(`Failed to approve item: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error approving item:', error);
      alert('Error approving item');
    }
  };

  const handleDeleteItem = async (itemId) => {
    if (!confirm('Are you sure you want to delete this knowledge base item?')) return;
    
    try {
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/admin/knowledge-base/${itemId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        await fetchKnowledgeBase();
        alert('Knowledge base item deleted successfully!');
      } else {
        const error = await response.json();
        alert(`Failed to delete item: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error deleting item:', error);
      alert('Error deleting item');
    }
  };

  const handleFileSelect = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    if (!file.name.endsWith('.md')) {
      alert('Please select a .md (Markdown) file');
      return;
    }
    
    setUploadFile(file);
    
    // Preview the file
    try {
      setUploadLoading(true);
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch(`${backendUrl}/admin/knowledge-base/preview-markdown`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      
      if (response.ok) {
        const previewData = await response.json();
        setUploadPreview(previewData);
      } else {
        const error = await response.text();
        alert(`Failed to preview file: ${error}`);
      }
    } catch (error) {
      console.error('Error previewing file:', error);
      alert('Error previewing file');
    } finally {
      setUploadLoading(false);
    }
  };

  const handleUploadMarkdown = async () => {
    if (!uploadFile) return;
    
    try {
      setUploadLoading(true);
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', uploadFile);
      
      const response = await fetch(`${backendUrl}/admin/knowledge-base/upload-markdown`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      
      if (response.ok) {
        const result = await response.json();
        setShowUploadModal(false);
        setUploadFile(null);
        setUploadPreview(null);
        await fetchKnowledgeBase();
        await fetchPendingMarkdownCount(); // Refresh pending count
        
        alert(`✅ Successfully imported ${result.success_count} knowledge base items from ${result.filename}!${result.error_count > 0 ? ` (${result.error_count} errors)` : ''}`);
      } else {
        const error = await response.text();
        alert(`Failed to upload file: ${error}`);
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Error uploading file');
    } finally {
      setUploadLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      content: '',
      category: 'treatments',
      tags: [],
      source_type: 'admin_created'
    });
  };

  const addTag = () => {
    if (newTag.trim() && !formData.tags.includes(newTag.trim())) {
      setFormData({
        ...formData,
        tags: [...formData.tags, newTag.trim()]
      });
      setNewTag('');
    }
  };

  const removeTag = (tagToRemove) => {
    setFormData({
      ...formData,
      tags: formData.tags.filter(tag => tag !== tagToRemove)
    });
  };

  const startEditing = (item) => {
    setEditingItem(item);
    setFormData({
      title: item.title,
      content: item.content,
      category: item.category,
      tags: item.tags || [],
      source_type: item.source_type
    });
    setShowCreateModal(true);
  };

  const getCategoryLabel = (value) => {
    const category = categories.find(cat => cat.value === value);
    return category ? category.label : value;
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
      <div className="mb-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-[#222428] mb-2">KinAura Chatbot Management</h1>
            <p className="text-gray-600">Manage the chatbot's knowledge base and approved content</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-[#C8A25A] text-white px-6 py-2 rounded-lg hover:bg-[#B8925A] transition-colors"
          >
            + Add Knowledge
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-lg shadow-md mb-6">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            <button
              onClick={() => setActiveTab('knowledge-base')}
              className={`py-4 px-2 border-b-2 font-medium text-sm ${
                activeTab === 'knowledge-base'
                  ? 'border-[#C8A25A] text-[#C8A25A]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              📚 Knowledge Base
            </button>
            <button
              onClick={() => setActiveTab('rag-analytics')}
              className={`py-4 px-2 border-b-2 font-medium text-sm ${
                activeTab === 'rag-analytics'
                  ? 'border-[#C8A25A] text-[#C8A25A]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              📊 RAG Analytics
            </button>
            <button
              onClick={() => setActiveTab('unresolved-queries')}
              className={`py-4 px-2 border-b-2 font-medium text-sm ${
                activeTab === 'unresolved-queries'
                  ? 'border-[#C8A25A] text-[#C8A25A]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              ❓ Unresolved Queries
            </button>
            <button
              onClick={() => setActiveTab('knowledge-gaps')}
              className={`py-4 px-2 border-b-2 font-medium text-sm ${
                activeTab === 'knowledge-gaps'
                  ? 'border-[#C8A25A] text-[#C8A25A]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              🔍 Knowledge Gaps
            </button>
            <button
              onClick={() => setActiveTab('configuration')}
              className={`py-4 px-2 border-b-2 font-medium text-sm ${
                activeTab === 'configuration'
                  ? 'border-[#C8A25A] text-[#C8A25A]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              ⚙️ Configuration
            </button>
          </nav>
        </div>
      </div>

      {/* Knowledge Base Management */}
      {activeTab === 'knowledge-base' && (
        <div className="space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow-md p-6 text-center">
              <div className="text-3xl font-bold text-[#C8A25A]">{knowledgeBase.length}</div>
              <div className="text-sm text-gray-500">Total Items</div>
            </div>
            <div className="bg-white rounded-lg shadow-md p-6 text-center">
              <div className="text-3xl font-bold text-green-600">
                {knowledgeBase.filter(item => item.is_approved).length}
              </div>
              <div className="text-sm text-gray-500">Approved</div>
            </div>
            <div className="bg-white rounded-lg shadow-md p-6 text-center">
              <div className="text-3xl font-bold text-orange-600">
                {knowledgeBase.filter(item => !item.is_approved).length}
              </div>
              <div className="text-sm text-gray-500">Pending Approval</div>
            </div>
            <div className="bg-white rounded-lg shadow-md p-6 text-center">
              <div className="text-3xl font-bold text-blue-600">
                {new Set(knowledgeBase.map(item => item.category)).size}
              </div>
              <div className="text-sm text-gray-500">Categories</div>
            </div>
          </div>

          {/* Knowledge Base Items */}
          <div className="bg-white rounded-lg shadow-md">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-2xl font-bold text-[#222428]">Knowledge Base Management</h2>
                <p className="text-gray-600 mt-1">Manage the information that KinAura Concierge can reference</p>
              </div>
              <div className="flex space-x-3">
                {pendingMarkdownCount > 0 && (
                  <button
                    onClick={handleBulkApproveMarkdown}
                    disabled={bulkApproveLoading}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                  >
                    {bulkApproveLoading && <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
                    <span>✅</span>
                    <span>{bulkApproveLoading ? 'Approving...' : `Approve All MD Files (${pendingMarkdownCount})`}</span>
                  </button>
                )}
                <button
                  onClick={() => setShowUploadModal(true)}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
                >
                  <span>📄</span>
                  <span>Upload .md File</span>
                </button>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="bg-[#C8A25A] text-white px-4 py-2 rounded-lg hover:bg-[#B8925A] transition-colors flex items-center space-x-2"
                >
                  <span>+</span>
                  <span>Add Knowledge</span>
                </button>
              </div>
            </div>
            <div className="divide-y divide-gray-200">
              {knowledgeBase.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <p className="text-lg mb-4">No knowledge base items found</p>
                  <button
                    onClick={() => setShowCreateModal(true)}
                    className="bg-[#C8A25A] text-white px-6 py-2 rounded-lg hover:bg-[#B8925A] transition-colors"
                  >
                    Create Your First Knowledge Item
                  </button>
                </div>
              ) : (
                knowledgeBase.map((item) => (
                  <div key={item.id} className="p-6 hover:bg-gray-50">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h3 className="text-lg font-semibold text-[#222428]">{item.title}</h3>
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                            item.is_approved 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-orange-100 text-orange-800'
                          }`}>
                            {item.is_approved ? 'Approved' : 'Pending'}
                          </span>
                          <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-xs">
                            {getCategoryLabel(item.category)}
                          </span>
                        </div>
                        
                        <p className="text-gray-600 mb-3 line-clamp-3">{item.content}</p>
                        
                        {item.tags && item.tags.length > 0 && (
                          <div className="flex flex-wrap gap-2 mb-3">
                            {item.tags.map((tag, index) => (
                              <span key={index} className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                                #{tag}
                              </span>
                            ))}
                          </div>
                        )}
                        
                        <div className="text-sm text-gray-500">
                          <span>Created: {new Date(item.created_at).toLocaleDateString()}</span>
                          {item.approval_date && (
                            <span className="ml-4">
                              Approved: {new Date(item.approval_date).toLocaleDateString()}
                            </span>
                          )}
                          <span className="ml-4">Version: {item.version}</span>
                        </div>
                      </div>
                      
                      <div className="flex space-x-2 ml-4">
                        <button
                          onClick={() => startEditing(item)}
                          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                        >
                          Edit
                        </button>
                        {!item.is_approved && (
                          <button
                            onClick={() => handleApproveItem(item.id)}
                            className="text-green-600 hover:text-green-800 text-sm font-medium"
                          >
                            Approve
                          </button>
                        )}
                        <button
                          onClick={() => handleDeleteItem(item.id)}
                          className="text-red-600 hover:text-red-800 text-sm font-medium"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* RAG Analytics */}
      {activeTab === 'rag-analytics' && (
        <div className="space-y-6">
          {/* Analytics Overview */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-[#222428] mb-4">RAG System Analytics</h2>
            
            {analytics && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-blue-600">{analytics.overview?.total_sessions || 0}</div>
                  <div className="text-sm text-blue-700">Total Sessions</div>
                </div>
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-green-600">{analytics.overview?.avg_confidence?.toFixed(2) || '0.00'}</div>
                  <div className="text-sm text-green-700">Avg Confidence</div>
                </div>
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-purple-600">{analytics.overview?.knowledge_coverage?.toFixed(1) || '0.0'}%</div>
                  <div className="text-sm text-purple-700">KB Coverage</div>
                </div>
              </div>
            )}
          </div>

          {/* RAG Test Tool */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-[#222428] mb-4">Test RAG System</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Test Query</label>
                <input
                  type="text"
                  value={testQuery}
                  onChange={(e) => setTestQuery(e.target.value)}
                  placeholder="Enter a test query to see how the RAG system responds..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-[#C8A25A] focus:border-[#C8A25A]"
                />
              </div>
              <button
                onClick={testRagSystem}
                disabled={!testQuery.trim()}
                className="bg-[#C8A25A] text-white px-4 py-2 rounded-lg hover:bg-[#B8925A] disabled:bg-gray-300 transition-colors"
              >
                Test RAG Response
              </button>
              
              {ragTestResult && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mt-4">
                  <div className="space-y-3">
                    <div>
                      <span className="font-medium">Response:</span>
                      <div className="bg-white border rounded p-3 mt-1 text-sm">{ragTestResult.response}</div>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="font-medium">Sources Found:</span> {ragTestResult.sources_found || 0}
                      </div>
                      <div>
                        <span className="font-medium">Confidence:</span> {ragTestResult.confidence?.toFixed(2) || '0.00'}
                      </div>
                      <div>
                        <span className="font-medium">Response Time:</span> {ragTestResult.response_time?.toFixed(2) || '0.00'}s
                      </div>
                    </div>
                    {ragTestResult.sources && ragTestResult.sources.length > 0 && (
                      <div>
                        <span className="font-medium">Sources:</span>
                        <div className="mt-2 space-y-2">
                          {ragTestResult.sources.map((source, idx) => (
                            <div key={idx} className="bg-white border rounded p-2 text-xs">
                              <div className="font-medium">{source.title}</div>
                              <div className="text-gray-600">{source.content_preview}</div>
                              <div className="text-[#C8A25A] mt-1">Similarity: {Math.round(source.similarity * 100)}%</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Unresolved Queries */}
      {activeTab === 'unresolved-queries' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-[#222428] mb-4">Unresolved Queries</h2>
            <p className="text-gray-600 mb-6">Review queries where the chatbot had low confidence or couldn't find relevant information.</p>
            
            {unresolvedQueries.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <div className="text-4xl mb-2">🎉</div>
                <div>No unresolved queries - great job!</div>
              </div>
            ) : (
              <div className="space-y-4">
                {unresolvedQueries.map((query) => (
                  <div key={query.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <div className="font-medium text-gray-900">"{query.query}"</div>
                        <div className="text-sm text-gray-500 mt-1">
                          Session: {query.session_id} | Language: {query.language} | 
                          Confidence: {Math.round(query.confidence * 100)}%
                        </div>
                      </div>
                      <div className="ml-4">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          query.confidence < 0.3 ? 'bg-red-100 text-red-800' :
                          query.confidence < 0.6 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-blue-100 text-blue-800'
                        }`}>
                          {query.confidence < 0.3 ? 'Very Low' : query.confidence < 0.6 ? 'Low' : 'Moderate'} Confidence
                        </span>
                      </div>
                    </div>
                    
                    <div className="text-sm text-gray-700 mb-3">
                      <span className="font-medium">Attempted Response:</span>
                      <div className="bg-gray-50 border rounded p-2 mt-1">{query.attempted_response}</div>
                    </div>
                    
                    {query.suggested_kb_topics && query.suggested_kb_topics.length > 0 && (
                      <div className="flex flex-wrap gap-2 mb-3">
                        <span className="text-sm font-medium text-gray-700">Suggested topics:</span>
                        {query.suggested_kb_topics.map((topic) => (
                          <span key={topic} className="px-2 py-1 bg-[#C8A25A] text-white text-xs rounded-full">
                            {topic.replace('_', ' ')}
                          </span>
                        ))}
                      </div>
                    )}
                    
                    <button
                      onClick={() => markQueryResolved(query.id, 'Reviewed by admin')}
                      className="text-sm bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700 transition-colors"
                    >
                      Mark as Resolved
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Knowledge Gaps */}
      {activeTab === 'knowledge-gaps' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-[#222428] mb-4">Knowledge Gaps Analysis</h2>
            <p className="text-gray-600 mb-6">Identify topics that patients ask about but aren't well covered in the knowledge base.</p>
            
            {knowledgeGaps.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <div className="text-4xl mb-2">📚</div>
                <div>No knowledge gaps identified - excellent coverage!</div>
              </div>
            ) : (
              <div className="space-y-4">
                {knowledgeGaps.map((gap) => (
                  <div key={gap.topic} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <div className="font-medium text-gray-900 capitalize">
                          {gap.topic.replace('_', ' ')}
                        </div>
                        <div className="text-sm text-gray-500 mt-1">
                          Frequency: {gap.frequency} queries | Avg Confidence: {Math.round(gap.avg_confidence * 100)}%
                        </div>
                      </div>
                      <div className="ml-4">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          gap.priority === 'high' ? 'bg-red-100 text-red-800' :
                          gap.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-blue-100 text-blue-800'
                        }`}>
                          {gap.priority} Priority
                        </span>
                      </div>
                    </div>
                    
                    <div className="text-sm text-gray-700">
                      <span className="font-medium">Sample queries:</span>
                      <ul className="list-disc list-inside mt-1 space-y-1">
                        {gap.sample_queries?.map((sampleQuery, idx) => (
                          <li key={idx} className="text-gray-600">"{sampleQuery}"</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Chatbot Configuration */}
      {activeTab === 'configuration' && (
        <div className="space-y-6">
          {/* Configuration Header */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h2 className="text-xl font-semibold text-[#222428]">Chatbot System Prompt</h2>
                <p className="text-gray-600 mt-1">Configure the personality and behavior of the KinAura Concierge chatbot</p>
              </div>
              <button
                onClick={() => setShowConfigModal(true)}
                className="bg-[#C8A25A] text-white px-4 py-2 rounded-lg hover:bg-[#B8925A] transition-colors"
              >
                Update Configuration
              </button>
            </div>

            {chatbotConfig && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-medium text-gray-800 mb-2">Current System Prompt:</h3>
                <div className="bg-white p-4 rounded border text-sm text-gray-700 max-h-60 overflow-y-auto whitespace-pre-wrap">
                  {chatbotConfig.system_prompt}
                </div>
                <div className="mt-3 text-xs text-gray-500">
                  Version: {chatbotConfig.version} | 
                  Last updated: {chatbotConfig.updated_at ? new Date(chatbotConfig.updated_at).toLocaleString() : 'Never'}
                </div>
              </div>
            )}
          </div>

          {/* Configuration History */}
          {configHistory.length > 0 && (
            <div className="bg-white rounded-lg shadow-md">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-[#222428]">Configuration History</h2>
              </div>
              <div className="divide-y divide-gray-200 max-h-64 overflow-y-auto">
                {configHistory.map((config, index) => (
                  <div key={config.id || index} className="p-4">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <span className="text-sm font-medium text-gray-900">Version {config.version}</span>
                          {config.is_active && (
                            <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">
                              Active
                            </span>
                          )}
                        </div>
                        <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded max-h-20 overflow-y-auto">
                          {config.system_prompt?.substring(0, 200)}...
                        </div>
                        <div className="text-xs text-gray-500 mt-2">
                          Updated: {new Date(config.created_at).toLocaleString()}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Markdown Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-[#222428]">
                Upload Markdown File
              </h2>
              <p className="text-gray-600 mt-2">
                Import knowledge base items from a .md (Markdown) file. The file will be parsed automatically and sections will be converted to individual knowledge items.
              </p>
            </div>

            <div className="p-6">
              {/* File Upload Section */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Markdown File (.md)
                </label>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                  <input
                    type="file"
                    accept=".md"
                    onChange={handleFileSelect}
                    className="hidden"
                    id="markdown-upload"
                  />
                  <label 
                    htmlFor="markdown-upload" 
                    className="cursor-pointer flex flex-col items-center space-y-2"
                  >
                    <span className="text-4xl">📄</span>
                    <span className="text-lg font-medium text-gray-700">
                      {uploadFile ? uploadFile.name : 'Click to select a markdown file'}
                    </span>
                    <span className="text-sm text-gray-500">
                      Supports .md files with headers, frontmatter, and sections
                    </span>
                  </label>
                </div>
              </div>

              {/* Preview Section */}
              {uploadPreview && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-3">
                    Preview: {uploadPreview.item_count} items will be created
                  </h3>
                  <div className="bg-gray-50 rounded-lg p-4 max-h-60 overflow-y-auto">
                    {uploadPreview.parsed_items.map((item, index) => (
                      <div key={index} className="mb-4 p-3 bg-white rounded border">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium text-gray-800">{item.title}</h4>
                          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                            {item.category}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 line-clamp-2">
                          {item.content.substring(0, 150)}...
                        </p>
                        {item.tags.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {item.tags.slice(0, 4).map((tag, tagIndex) => (
                              <span key={tagIndex} className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">
                                #{tag}
                              </span>
                            ))}
                            {item.tags.length > 4 && (
                              <span className="text-xs text-gray-500">+{item.tags.length - 4} more</span>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Upload Instructions */}
              <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-medium text-blue-800 mb-2">📋 How Markdown Parsing Works:</h4>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• <strong>Headers (# ## ###)</strong> become individual knowledge items</li>
                  <li>• <strong>Categories</strong> are auto-detected from content and filename</li>
                  <li>• <strong>Tags</strong> are extracted from content and frontmatter</li>
                  <li>• <strong>Frontmatter</strong> (YAML at top of file) provides metadata</li>
                  <li>• Each section needs substantial content (50+ characters) to be included</li>
                </ul>
              </div>
            </div>

            {/* Modal Actions */}
            <div className="flex justify-end space-x-3 p-6 border-t border-gray-200 bg-gray-50">
              <button
                type="button"
                onClick={() => {
                  setShowUploadModal(false);
                  setUploadFile(null);
                  setUploadPreview(null);
                }}
                className="px-6 py-2 text-gray-600 hover:text-gray-800"
                disabled={uploadLoading}
              >
                Cancel
              </button>
              <button
                onClick={handleUploadMarkdown}
                disabled={!uploadFile || !uploadPreview || uploadLoading}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {uploadLoading && <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
                <span>{uploadLoading ? 'Processing...' : `Import ${uploadPreview?.item_count || 0} Items`}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Configuration Modal */}
      {showConfigModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-[#222428]">
                Update Chatbot Configuration
              </h2>
              <p className="text-gray-600 mt-2">
                Configure how the KinAura Concierge chatbot behaves, responds, and interacts with patients.
              </p>
            </div>

            <form onSubmit={handleUpdateConfig} className="p-6">
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  System Prompt *
                </label>
                <div className="text-sm text-gray-600 mb-3">
                  <p>Define the chatbot's personality, tone, and behavior rules. Include:</p>
                  <ul className="list-disc list-inside mt-1 text-xs text-gray-500">
                    <li>Tone and personality (elegant, calm, concise, expert)</li>
                    <li>Language preferences (bilingual Italian/English)</li>
                    <li>Response rules and limitations</li>
                    <li>Safety disclaimers and medical advice guidelines</li>
                    <li>KinAura focus areas and specialties</li>
                  </ul>
                </div>
                <textarea
                  value={configFormData.system_prompt}
                  onChange={(e) => setConfigFormData({...configFormData, system_prompt: e.target.value})}
                  rows={20}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:border-[#C8A25A] font-mono text-sm"
                  placeholder="Enter the system prompt that defines how the chatbot should behave..."
                  required
                />
              </div>

              <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
                <button
                  type="button"
                  onClick={() => {
                    setShowConfigModal(false);
                    setConfigFormData({
                      system_prompt: chatbotConfig?.system_prompt || ''
                    });
                  }}
                  className="px-6 py-2 text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-6 py-2 bg-[#C8A25A] text-white rounded-lg hover:bg-[#B8925A]"
                >
                  Update Configuration
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create/Edit Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-[#222428]">
                {editingItem ? 'Edit Knowledge Item' : 'Add Knowledge Item'}
              </h2>
            </div>

            <form onSubmit={editingItem ? handleUpdateItem : handleCreateItem} className="p-6 space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Title *
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({...formData, title: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:border-[#C8A25A]"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category *
                </label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({...formData, category: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:border-[#C8A25A]"
                >
                  {categories.map((category) => (
                    <option key={category.value} value={category.value}>
                      {category.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Content *
                </label>
                <textarea
                  value={formData.content}
                  onChange={(e) => setFormData({...formData, content: e.target.value})}
                  rows={10}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:border-[#C8A25A]"
                  placeholder="Enter the information that the chatbot should know about this topic..."
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tags
                </label>
                <div className="space-y-2">
                  <div className="flex flex-wrap gap-2">
                    {formData.tags.map((tag, index) => (
                      <span key={index} className="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                        #{tag}
                        <button
                          type="button"
                          onClick={() => removeTag(tag)}
                          className="ml-2 text-blue-500 hover:text-blue-700"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={newTag}
                      onChange={(e) => setNewTag(e.target.value)}
                      className="flex-1 p-2 border border-gray-300 rounded focus:outline-none focus:border-[#C8A25A]"
                      placeholder="Add a tag..."
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                    />
                    <button
                      type="button"
                      onClick={addTag}
                      className="px-3 py-2 bg-[#C8A25A] text-white rounded hover:bg-[#B8925A]"
                    >
                      Add
                    </button>
                  </div>
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setEditingItem(null);
                    resetForm();
                  }}
                  className="px-6 py-2 text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-6 py-2 bg-[#C8A25A] text-white rounded-lg hover:bg-[#B8925A]"
                >
                  {editingItem ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatbotAdmin;