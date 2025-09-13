import React, { useState, useEffect } from 'react';
import { supabase, supabaseApi } from './lib/supabase';
import AdminHealthData from './AdminHealthData';
import ServiceGroupsAdmin from './ServiceGroupsAdmin';
import ChatbotAdmin from './ChatbotAdmin';
import ServiceCard from './ServiceCard';
import ServiceModal from './ServiceModal';
import CRMFunnelDashboard from './components/CRMFunnelDashboard';
import BoutiqueAdmin from './components/BoutiqueAdmin';

// Configuration - Check if we should use Supabase or FastAPI
const USE_SUPABASE = process.env.REACT_APP_USE_SUPABASE === 'true' || false;
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = USE_SUPABASE ? null : `${BACKEND_URL}/api`;

// Admin API Helper - Use Supabase or FastAPI based on configuration  
const adminApi = {
  getDashboard: async (token) => {
    if (USE_SUPABASE) {
      return await supabaseApi.admin.getDashboard(token);
    } else {
      const axios = (await import('axios')).default;
      const response = await axios.get(`${API}/admin/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    }
  },

  getPatients: async (token) => {
    if (USE_SUPABASE) {
      return await supabaseApi.admin.getPatients(token);
    } else {
      const axios = (await import('axios')).default;
      const response = await axios.get(`${API}/admin/patients`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    }
  },

  createPatient: async (token, patientData) => {
    if (USE_SUPABASE) {
      return await supabaseApi.admin.createPatient(token, patientData);
    } else {
      const axios = (await import('axios')).default;
      const response = await axios.post(`${API}/admin/patients`, patientData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    }
  },

  getServices: async (token) => {
    if (USE_SUPABASE) {
      return await supabaseApi.services.getAll();
    } else {
      const axios = (await import('axios')).default;
      const response = await axios.get(`${API}/services`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    }
  },

  getMetrics: async (token) => {
    if (USE_SUPABASE) {
      return await supabaseApi.admin.getMetrics(token);
    } else {
      const axios = (await import('axios')).default;
      const response = await axios.get(`${API}/admin/metrics`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    }
  },

  getAuditLogs: async (token) => {
    if (USE_SUPABASE) {
      return await supabaseApi.admin.getAuditLogs(token);
    } else {
      const axios = (await import('axios')).default;
      const response = await axios.get(`${API}/admin/audit-logs`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    }
  },

  sendNotification: async (token, notificationData) => {
    if (USE_SUPABASE) {
      return await supabaseApi.admin.sendNotification(token, notificationData);
    } else {
      const axios = (await import('axios')).default;
      const response = await axios.post(`${API}/admin/notifications/send`, notificationData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    }
  },

  getNotificationLogs: async (token) => {
    if (USE_SUPABASE) {
      return await supabaseApi.admin.getNotificationLogs(token);
    } else {
      const axios = (await import('axios')).default;
      const response = await axios.get(`${API}/admin/notifications`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    }
  },

  // Additional functions for other operations
  getPatientNotes: async (token, patientId) => {
    if (USE_SUPABASE) {
      // Add Supabase implementation when available
      throw new Error('Patient notes not yet implemented in Supabase');
    } else {
      const axios = (await import('axios')).default;
      const response = await axios.get(`${API}/admin/patients/${patientId}/notes`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    }
  },

  createPatientNote: async (token, noteData) => {
    if (USE_SUPABASE) {
      // Add Supabase implementation when available
      throw new Error('Patient notes not yet implemented in Supabase');
    } else {
      const axios = (await import('axios')).default;
      const response = await axios.post(`${API}/admin/patients/${noteData.patient_id}/notes`, noteData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    }
  },

  getPatientFiles: async (token, patientId) => {
    if (USE_SUPABASE) {
      // Add Supabase implementation when available
      throw new Error('Patient files not yet implemented in Supabase');
    } else {
      const axios = (await import('axios')).default;
      const response = await axios.get(`${API}/admin/patients/${patientId}/files`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    }
  },

  getPatientFolder: async (token, patientId) => {
    if (USE_SUPABASE) {
      // Add Supabase implementation when available
      throw new Error('Patient folder not yet implemented in Supabase');
    } else {
      const axios = (await import('axios')).default;
      const response = await axios.get(`${API}/admin/patients/${patientId}/folder`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    }
  },

  uploadPatientFile: async (token, fileData) => {
    if (USE_SUPABASE) {
      // Add Supabase implementation when available  
      throw new Error('File upload not yet implemented in Supabase');
    } else {
      const axios = (await import('axios')).default;
      const response = await axios.post(`${API}/admin/patients/${fileData.patient_id}/files/upload`, {
        file_type: fileData.file_type,
        file_category: fileData.file_category,
        visible_to_patient: fileData.visible_to_patient,
        description: fileData.description,
        notes: fileData.notes,
        tags: fileData.tags.split(',').map(tag => tag.trim()).filter(tag => tag),
        file_name: fileData.file_name || 'uploaded_file.pdf'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    }
  },

  updateFileVisibility: async (token, fileId, visibility) => {
    if (USE_SUPABASE) {
      // Add Supabase implementation when available
      throw new Error('File update not yet implemented in Supabase');
    } else {
      const axios = (await import('axios')).default;
      await axios.put(`${API}/admin/files/${fileId}`, {
        visible_to_patient: visibility
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
    }
  },

  deleteFile: async (token, fileId) => {
    if (USE_SUPABASE) {
      // Add Supabase implementation when available
      throw new Error('File deletion not yet implemented in Supabase');
    } else {
      const axios = (await import('axios')).default;
      await axios.delete(`${API}/admin/files/${fileId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
    }
  },

  createService: async (token, serviceData) => {
    if (USE_SUPABASE) {
      // Add Supabase implementation when available
      throw new Error('Service creation not yet implemented in Supabase');
    } else {
      const axios = (await import('axios')).default;
      const response = await axios.post(`${API}/services`, serviceData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    }
  },

  filterPatients: async (token, params) => {
    if (USE_SUPABASE) {
      // Add Supabase implementation when available
      throw new Error('Patient filtering not yet implemented in Supabase');
    } else {
      const axios = (await import('axios')).default;
      const response = await axios.get(`${API}/admin/patients/filter?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    }
  },

  // Questionnaire Management
  getQuestionnaires: async (token) => {
    if (USE_SUPABASE) {
      throw new Error('Questionnaires not yet implemented in Supabase');
    } else {
      const axios = (await import('axios')).default;
      const response = await axios.get(`${API}/admin/questionnaires`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    }
  },

  createQuestionnaire: async (token, questionnaireData) => {
    if (USE_SUPABASE) {
      throw new Error('Questionnaire creation not yet implemented in Supabase');
    } else {
      const axios = (await import('axios')).default;
      const response = await axios.post(`${API}/admin/questionnaires`, questionnaireData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    }
  },

  addQuestion: async (token, questionnaireId, questionData) => {
    if (USE_SUPABASE) {
      throw new Error('Question creation not yet implemented in Supabase');
    } else {
      const axios = (await import('axios')).default;
      const response = await axios.post(`${API}/admin/questionnaires/${questionnaireId}/questions`, questionData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    }
  },

  assignQuestionnaire: async (token, assignmentData) => {
    if (USE_SUPABASE) {
      throw new Error('Questionnaire assignment not yet implemented in Supabase');
    } else {
      const axios = (await import('axios')).default;
      const response = await axios.post(`${API}/admin/questionnaires/assign`, assignmentData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    }
  },

  // Patient Inquiry Management
  getPatientInquiries: async (token, params = {}) => {
    if (USE_SUPABASE) {
      throw new Error('Patient inquiries not yet implemented in Supabase');
    } else {
      const axios = (await import('axios')).default;
      const queryString = new URLSearchParams(params).toString();
      const response = await axios.get(`${API}/admin/inquiries${queryString ? `?${queryString}` : ''}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    }
  },

  getInquiryDetails: async (token, inquiryId) => {
    if (USE_SUPABASE) {
      throw new Error('Inquiry details not yet implemented in Supabase');
    } else {
      const axios = (await import('axios')).default;
      const response = await axios.get(`${API}/admin/inquiries/${inquiryId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    }
  },

  updateInquiryStatus: async (token, inquiryId, updateData) => {
    if (USE_SUPABASE) {
      throw new Error('Inquiry updates not yet implemented in Supabase');
    } else {
      const axios = (await import('axios')).default;
      const response = await axios.put(`${API}/admin/inquiries/${inquiryId}`, updateData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    }
  },

  sendBookingRequest: async (token, inquiryId, bookingData) => {
    if (USE_SUPABASE) {
      throw new Error('Booking requests not yet implemented in Supabase');
    } else {
      const axios = (await import('axios')).default;
      const response = await axios.post(`${API}/admin/inquiries/${inquiryId}/send-booking-request`, bookingData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    }
  },

  getAdminNotifications: async (token, params = {}) => {
    if (USE_SUPABASE) {
      throw new Error('Admin notifications not yet implemented in Supabase');
    } else {
      const axios = (await import('axios')).default;
      const queryString = new URLSearchParams(params).toString();
      const response = await axios.get(`${API}/admin/notifications${queryString ? `?${queryString}` : ''}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    }
  },

  getInquiryStats: async (token, days = 7) => {
    if (USE_SUPABASE) {
      throw new Error('Inquiry stats not yet implemented in Supabase');
    } else {
      const axios = (await import('axios')).default;
      const response = await axios.get(`${API}/admin/inquiries/stats?days=${days}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    }
  }
};

const AdminDashboard = ({ user, onNavigate, onLogoClick }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [dashboardData, setDashboardData] = useState({});
  const [patients, setPatients] = useState([]);
  const [services, setServices] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [formulas, setFormulas] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [patientNotes, setPatientNotes] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [filteredPatients, setFilteredPatients] = useState([]);
  const [patientFiles, setPatientFiles] = useState([]);
  const [patientFolder, setPatientFolder] = useState(null);
  const [questionnaires, setQuestionnaires] = useState([]);
  const [serviceGroups, setServiceGroups] = useState([]);
  
  // Service management states
  const [showCreateServiceModal, setShowCreateServiceModal] = useState(false);
  const [editingService, setEditingService] = useState(null);

  // Form states for creating new items
  const [newPatient, setNewPatient] = useState({
    full_name: '',
    email: '',
    phone: '',
    dob: '',
    gender: 'female',
    tags: ''
  });

  const [newService, setNewService] = useState({
    name: '',
    category: 'regenerative',
    description: '',
    duration_min: 60,
    base_price_cents: 0
  });

  const [newFormula, setNewFormula] = useState({
    patient_id: '',
    name: '',
    price_cents: 15000,
    packaging: 'jar'
  });

  const [newNote, setNewNote] = useState({
    patient_id: '',
    title: '',
    content: '',
    category: 'general',
    is_important: false
  });

  const [notificationForm, setNotificationForm] = useState({
    title: '',
    message: '',
    target_type: 'single',
    target_patient_id: '',
    target_tags: '',
    target_membership: ''
  });

  const [newFile, setNewFile] = useState({
    patient_id: '',
    file_type: 'test_result',
    file_category: 'general',
    visible_to_patient: false,
    description: '',
    notes: '',
    tags: ''
  });

  const [newQuestionnaire, setNewQuestionnaire] = useState({
    title: '',
    description: '',
    category: 'medical_history',
    is_required: false,
    instructions: ''
  });

  const [newQuestion, setNewQuestion] = useState({
    questionnaire_id: '',
    question_text: '',
    question_type: 'text',
    is_required: false,
    order_index: 0,
    options: {},
    help_text: ''
  });

  const [assignmentForm, setAssignmentForm] = useState({
    questionnaire_id: '',
    patient_id: '',
    due_date: ''
  });

  // Patient Inquiry Management State
  const [inquiries, setInquiries] = useState([]);
  const [selectedInquiry, setSelectedInquiry] = useState(null);
  const [inquiryFilter, setInquiryFilter] = useState({
    status: '',
    inquiry_type: '',
    patient_id: ''
  });
  const [adminNotifications, setAdminNotifications] = useState([]);
  const [inquiryStats, setInquiryStats] = useState(null);
  const [bookingRequest, setBookingRequest] = useState({
    treatments: [],
    message: '',
    suggested_times: []
  });

  useEffect(() => {
    if (activeTab === 'overview') {
      fetchDashboardData();
    } else if (activeTab === 'patients') {
      fetchPatients();
    } else if (activeTab === 'inquiries') {
      fetchInquiries();
    } else if (activeTab === 'services') {
      fetchServices();
      fetchServiceGroups(); // Fetch service groups for assignment
    } else if (activeTab === 'service-groups') {
      fetchServiceGroups();
    } else if (activeTab === 'appointments') {
      fetchAppointments();
    } else if (activeTab === 'formulas') {
      fetchFormulas();
    } else if (activeTab === 'audit') {
      fetchAuditLogs();
    } else if (activeTab === 'notifications') {
      fetchNotifications();
    } else if (activeTab === 'patient-notes') {
      if (selectedPatient) {
        fetchPatientNotes(selectedPatient.id);
      } else {
        fetchPatients(); // Show patient selection first
      }
    } else if (activeTab === 'patient-files') {
      if (selectedPatient) {
        fetchPatientFiles(selectedPatient.id);
      } else {
        fetchPatients(); // Show patient selection first
      }
    } else if (activeTab === 'questionnaires') {
      fetchQuestionnaires();
    } else if (activeTab === 'appointments') {
      // Appointments are handled by the AdminAppointments component
    }
  }, [activeTab]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const data = await adminApi.getDashboard(token);
      setDashboardData(data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPatients = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const patientsData = await adminApi.getPatients(token);
      setPatients(patientsData);
      setFilteredPatients(patientsData);
    } catch (error) {
      console.error('Error fetching patients:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchServices = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const servicesData = await adminApi.getServices(token);
      setServices(servicesData);
    } catch (error) {
      console.error('Error fetching services:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAppointments = async () => {
    setLoading(true);
    try {
      // Mock appointment data
      setAppointments([
        {
          id: '1',
          patient_name: 'Elena Verdi',
          service_name: 'Ozone Therapy',
          appointment_date: '2024-01-24T11:00:00Z',
          status: 'scheduled',
          practitioner: 'Dr. Marco Rossi'
        },
        {
          id: '2',
          patient_name: 'Francesco Neri',
          service_name: 'NAD+ IV Therapy',
          appointment_date: '2024-01-26T14:00:00Z',
          status: 'confirmed',
          practitioner: 'Dr. Sofia Bianchi'
        }
      ]);
    } catch (error) {
      console.error('Error fetching appointments:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchFormulas = async () => {
    setLoading(true);
    try {
      // Mock formula data
      setFormulas([
        {
          id: '1',
          name: 'Elena Custom Anti-Aging Serum',
          patient_name: 'Elena Verdi',
          price: 185,
          status: 'finalized',
          created_at: '2024-01-15T10:00:00Z'
        },
        {
          id: '2',
          name: 'Francesco Performance Recovery Cream',
          patient_name: 'Francesco Neri',
          price: 220,
          status: 'finalized',
          created_at: '2024-01-16T14:30:00Z'
        }
      ]);
    } catch (error) {
      console.error('Error fetching formulas:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAuditLogs = async () => {
    setLoading(true);
    try {
      // Mock audit log data
      setAuditLogs([
        {
          id: '1',
          action: 'create_patient',
          actor_name: 'Dr. Marco Rossi',
          entity_table: 'patients',
          created_at: '2024-01-20T10:00:00Z',
          details: 'Created new patient: Elena Verdi'
        },
        {
          id: '2',
          action: 'finalize_formula',
          actor_name: 'Dr. Sofia Bianchi',
          entity_table: 'formulas',
          created_at: '2024-01-20T14:30:00Z',
          details: 'Finalized formula for Francesco Neri'
        }
      ]);
    } catch (error) {
      console.error('Error fetching audit logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const notificationsData = await adminApi.getNotificationLogs(token);
      setNotifications(notificationsData);
    } catch (error) {
      console.error('Error fetching notifications:', error);
      // Mock data fallback
      setNotifications([
        {
          id: '1',
          title: 'Appointment Reminder',
          message: 'Your appointment is tomorrow',
          target_type: 'single',
          sent_count: 1,
          created_at: '2024-01-20T10:00:00Z',
          status: 'sent'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const fetchPatientNotes = async (patientId) => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const notesData = await adminApi.getPatientNotes(token, patientId);
      setPatientNotes(notesData);
    } catch (error) {
      console.error('Error fetching patient notes:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchFilteredPatients = async (tags, membership) => {
    try {
      const params = new URLSearchParams();
      if (tags) params.append('tags', tags);
      if (membership) params.append('membership', membership);
      
      const token = localStorage.getItem('token');
      const response = await adminApi.filterPatients(token, params.toString());
      setFilteredPatients(response.patients);
      return response;
    } catch (error) {
      console.error('Error fetching filtered patients:', error);
      return { patients: [], total_count: 0 };
    }
  };

  const fetchQuestionnaires = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const questionnairesData = await adminApi.getQuestionnaires(token);
      setQuestionnaires(questionnairesData);
    } catch (error) {
      console.error('Error fetching questionnaires:', error);
      // Mock data fallback
      setQuestionnaires([
        {
          _id: '1',
          title: 'Medical History Questionnaire',
          description: 'Comprehensive medical history assessment',
          category: 'medical_history',
          question_count: 15,
          assignments: { total: 5, completed: 3, pending: 2 },
          created_at: '2024-01-15T10:00:00Z'
        },
        {
          _id: '2',  
          title: 'Treatment Consent Form',
          description: 'Consent form for regenerative therapy',
          category: 'treatment_consent',
          question_count: 8,
          assignments: { total: 10, completed: 8, pending: 2 },
          created_at: '2024-01-10T14:30:00Z'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const fetchPatientFiles = async (patientId) => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // Fetch both files and folder info
      const [filesData, folderData] = await Promise.all([
        adminApi.getPatientFiles(token, patientId),
        adminApi.getPatientFolder(token, patientId)
      ]);
      
      setPatientFiles(filesData);
      setPatientFolder(folderData);
    } catch (error) {
      console.error('Error fetching patient files:', error);
    } finally {
      setLoading(false);
    }
  };

  const uploadPatientFile = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      await adminApi.uploadPatientFile(token, {
        ...newFile,
        tags: newFile.tags,
        file_name: newFile.file_name || 'uploaded_file.pdf'
      });
      
      // Clear form
      setNewFile({
        patient_id: '',
        file_type: 'test_result',
        file_category: 'general',
        visible_to_patient: false,
        description: '',
        notes: '',
        tags: ''
      });
      
      // Refresh the patient files list
      if (selectedPatient) {
        fetchPatientFiles(selectedPatient.id);
      }
      
      alert('File uploaded successfully!');
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Error uploading file. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const toggleFileVisibility = async (fileId, currentVisibility) => {
    try {
      const token = localStorage.getItem('token');
      const newVisibility = !currentVisibility;
      
      await adminApi.updateFileVisibility(token, fileId, newVisibility);
      
      // Refresh the files list
      if (selectedPatient) {
        fetchPatientFiles(selectedPatient.id);
      }
      
      alert(`File ${newVisibility ? 'shared with' : 'hidden from'} patient successfully!`);
    } catch (error) {
      console.error('Error updating file visibility:', error);
      alert('Error updating file visibility. Please try again.');
    }
  };

  const deletePatientFile = async (fileId) => {
    if (!confirm('Are you sure you want to delete this file? This action cannot be undone.')) {
      return;
    }
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await adminApi.deleteFile(token, fileId);
      
      // Refresh files list
      if (selectedPatient) {
        fetchPatientFiles(selectedPatient.id);
      }
      
      alert('File deleted successfully');
    } catch (error) {
      console.error('Error deleting file:', error);
      alert('Error deleting file');
    } finally {
      setLoading(false);
    }
  };

  const createPatient = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      // Mock creation - in real implementation, would call API
      const patient = {
        id: Date.now().toString(),
        ...newPatient,
        tags: newPatient.tags.split(',').map(tag => tag.trim()),
        membership_tier: 'standard',
        created_at: new Date().toISOString()
      };
      setPatients([...patients, patient]);
      setNewPatient({
        full_name: '',
        email: '',
        phone: '',
        dob: '',
        gender: 'female',
        tags: ''
      });
      alert('Patient created successfully!');
    } catch (error) {
      console.error('Error creating patient:', error);
      alert('Error creating patient');
    } finally {
      setLoading(false);
    }
  };

  const createService = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const serviceData = {
        ...newService,
        price: newService.base_price_cents / 100,
        duration: newService.duration_min,
        benefits: [],
        is_active: true
      };
      
      // Try to create via API
      const token = localStorage.getItem('token');
      const response = await adminApi.createService(token, serviceData);
      setServices([...services, response]);
      setNewService({
        name: '',
        category: 'regenerative',
        description: '',
        duration_min: 60,
        base_price_cents: 0
      });
      alert('Service created successfully!');
    } catch (error) {
      console.error('Error creating service:', error);
      alert('Error creating service');
    } finally {
      setLoading(false);
    }
  };

  // Enhanced service management functions
  const handleCreateService = async (serviceData) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/services`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(serviceData)
      });

      if (response.ok) {
        const newService = await response.json();
        setServices([...services, newService]);
        // Refresh service groups to update counts
        await fetchServiceGroups();
      } else {
        throw new Error('Failed to create service');
      }
    } catch (error) {
      console.error('Error creating service:', error);
      throw error;
    }
  };

  const handleUpdateService = async (serviceData) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/services/${editingService.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(serviceData)
      });

      if (response.ok) {
        const updatedService = await response.json();
        setServices(services.map(s => s.id === editingService.id ? updatedService : s));
        // Refresh service groups to update counts
        await fetchServiceGroups();
      } else {
        throw new Error('Failed to update service');
      }
    } catch (error) {
      console.error('Error updating service:', error);
      throw error;
    }
  };

  const handleDeleteService = async (serviceId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/services/${serviceId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        setServices(services.filter(s => s.id !== serviceId));
        // Refresh service groups to update counts
        await fetchServiceGroups();
        alert('Service deleted successfully');
      } else {
        throw new Error('Failed to delete service');
      }
    } catch (error) {
      console.error('Error deleting service:', error);
      alert('Error deleting service');
    }
  };

  const handleAssignServiceToGroup = async (serviceId, groupId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/services/${serviceId}/group`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ group_id: groupId })
      });

      if (response.ok) {
        // Update the service in the local state
        setServices(services.map(s => 
          s.id === serviceId ? { ...s, group_id: groupId } : s
        ));
        // Refresh service groups to update counts
        await fetchServiceGroups();
      } else {
        throw new Error('Failed to assign service to group');
      }
    } catch (error) {
      console.error('Error assigning service to group:', error);
      throw error;
    }
  };

  const fetchServiceGroups = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/service-groups`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setServiceGroups(data.service_groups || []);
      }
    } catch (error) {
      console.error('Error fetching service groups:', error);
    }
  };

  const createFormula = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      // Mock creation
      const formula = {
        id: Date.now().toString(),
        ...newFormula,
        price: newFormula.price_cents / 100,
        patient_name: patients.find(p => p.id === newFormula.patient_id)?.full_name || 'Unknown',
        status: 'draft',
        created_at: new Date().toISOString()
      };
      setFormulas([...formulas, formula]);
      setNewFormula({
        patient_id: '',
        name: '',
        price_cents: 15000,
        packaging: 'jar'
      });
      alert('Formula created successfully!');
    } catch (error) {
      console.error('Error creating formula:', error);
      alert('Error creating formula');
    } finally {
      setLoading(false);
    }
  };

  const createPatientNote = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await adminApi.createPatientNote(token, newNote);
      setPatientNotes([response, ...patientNotes]);
      setNewNote({
        patient_id: '',
        title: '',
        content: '',
        category: 'general',
        is_important: false
      });
      alert('Patient note created successfully!');
    } catch (error) {
      console.error('Error creating patient note:', error);
      alert('Error creating patient note');
    } finally {
      setLoading(false);
    }
  };

  const sendNotification = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await adminApi.sendNotification(token, notificationForm);
      alert(`Notification sent successfully to ${response.target_count} patients!`);
      setNotificationForm({
        title: '',
        message: '',
        target_type: 'single',
        target_patient_id: '',
        target_tags: '',
        target_membership: ''
      });
      fetchNotifications(); // Refresh notifications list
    } catch (error) {
      console.error('Error sending notification:', error);
      alert('Error sending notification');
    } finally {
      setLoading(false);
    }
  };

  const previewNotificationTargets = async () => {
    if (notificationForm.target_type === 'single') {
      if (!notificationForm.target_patient_id) {
        alert('Please select a patient');
        return;
      }
      const patient = patients.find(p => p.id === notificationForm.target_patient_id);
      alert(`Will send to: ${patient?.full_name || 'Unknown Patient'}`);
      return;
    }

    let tags = null;
    let membership = null;

    if (notificationForm.target_type === 'tags') {
      tags = notificationForm.target_tags;
    } else if (notificationForm.target_type === 'membership') {
      membership = notificationForm.target_membership;
    }

    const result = await fetchFilteredPatients(tags, membership);
    alert(`Will send to ${result.total_count} patients matching the criteria`);
  };

  const createQuestionnaire = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await adminApi.createQuestionnaire(token, newQuestionnaire);
      alert('Questionnaire created successfully!');
      setNewQuestionnaire({
        title: '',
        description: '',
        category: 'medical_history',
        is_required: false,
        instructions: ''
      });
      fetchQuestionnaires(); // Refresh questionnaires list
    } catch (error) {
      console.error('Error creating questionnaire:', error);
      alert('Error creating questionnaire');
    } finally {
      setLoading(false);
    }
  };

  const assignQuestionnaire = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const assignmentData = {
        questionnaire_id: assignmentForm.questionnaire_id,
        patient_id: assignmentForm.patient_id,
        due_date: assignmentForm.due_date ? new Date(assignmentForm.due_date).toISOString() : null
      };
      
      const response = await adminApi.assignQuestionnaire(token, assignmentData);
      alert('Questionnaire assigned successfully!');
      setAssignmentForm({questionnaire_id: '', patient_id: '', due_date: ''});
      fetchQuestionnaires(); // Refresh questionnaires list to update assignment counts
    } catch (error) {
      console.error('Error assigning questionnaire:', error);
      alert('Error assigning questionnaire');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Patient Inquiry Management Functions
  const fetchInquiries = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = {};
      
      if (inquiryFilter.status) params.status = inquiryFilter.status;
      if (inquiryFilter.inquiry_type) params.inquiry_type = inquiryFilter.inquiry_type;
      if (inquiryFilter.patient_id) params.patient_id = inquiryFilter.patient_id;
      
      const response = await adminApi.getPatientInquiries(token, params);
      setInquiries(response.inquiries || []);
      
      // Also fetch inquiry stats
      const statsResponse = await adminApi.getInquiryStats(token, 7);
      setInquiryStats(statsResponse);
      
    } catch (error) {
      console.error('Error fetching inquiries:', error);
      setInquiries([]);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateInquiryStatus = async (inquiryId, status, notes) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const updateData = { status };
      if (notes) updateData.admin_notes = notes;
      
      await adminApi.updateInquiryStatus(token, inquiryId, updateData);
      
      // Refresh inquiries list
      await fetchInquiries();
      
      alert('Inquiry status updated successfully!');
    } catch (error) {
      console.error('Error updating inquiry:', error);
      alert('Error updating inquiry status');
    } finally {
      setLoading(false);
    }
  };

  const handleSendBookingRequest = async (inquiryId) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await adminApi.sendBookingRequest(token, inquiryId, bookingRequest);
      
      // Refresh inquiries list
      await fetchInquiries();
      
      alert('Booking request sent successfully!');
      setSelectedInquiry(null);
    } catch (error) {
      console.error('Error sending booking request:', error);
      alert('Error sending booking request');
    } finally {
      setLoading(false);
    }
  };

  const fetchAdminNotifications = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await adminApi.getAdminNotifications(token, { type: 'inquiry_alert' });
      setAdminNotifications(response.notifications || []);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  const getInquiryPriorityColor = (priority) => {
    switch (priority) {
      case 5: return 'text-red-600 bg-red-50 border-red-200';
      case 4: return 'text-orange-600 bg-orange-50 border-orange-200';
      case 3: return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 2: return 'text-blue-600 bg-blue-50 border-blue-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getInquiryTypeIcon = (type) => {
    switch (type) {
      case 'treatment': return '💊';
      case 'condition': return '🏥';
      case 'wellness_goal': return '🎯';
      default: return '💬';
    }
  };

  const formatCurrency = (cents) => {
    return `€${(cents / 100).toFixed(2)}`;
  };

  const tabs = [
    { id: 'overview', name: 'Dashboard', icon: '📊' },
    { id: 'crm-funnel', name: 'CRM Funnel', icon: '🎯' },
    { id: 'boutique', name: 'Boutique', icon: '🛍️' },
    { id: 'patients', name: 'Patients', icon: '👥' },
    { id: 'inquiries', name: 'Patient Inquiries', icon: '💬' },
    { id: 'patient-notes', name: 'Patient Notes', icon: '📝' },
    { id: 'patient-files', name: 'Patient Files', icon: '📁' },
    { id: 'health-data', name: 'Health Data', icon: '💚' },
    { id: 'service-groups', name: 'Service Groups', icon: '🏷️' },
    { id: 'questionnaires', name: 'Questionnaires', icon: '📋' },
    { id: 'appointments', name: 'Appointments', icon: '📅' },
    { id: 'services', name: 'Services', icon: '🏥' },
    { id: 'formulas', name: 'Formulas', icon: '🧪' },
    { id: 'chatbot', name: 'Chatbot', icon: '🤖' },
    { id: 'notifications', name: 'Notifications', icon: '🔔' },
    { id: 'campaigns', name: 'Campaigns', icon: '📢' },
    { id: 'audit', name: 'Audit Logs', icon: '📋' },
  ];

  if (loading && Object.keys(dashboardData).length === 0) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold mx-auto mb-4"></div>
          <p className="kinaura-body text-gray-600">Loading admin dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-100">
        <div className="flex justify-between items-center px-6 py-4">
          <div className="flex items-center space-x-4">
            <button 
              onClick={() => onNavigate('dashboard')}
              className="text-black text-xl hover:text-gold transition-colors"
            >
              ←
            </button>
            <div className="flex items-center space-x-2 cursor-pointer" onClick={onLogoClick || (() => onNavigate('admin'))}>
              <img 
                src="/brand/kinaura-symbol.svg" 
                alt="KinAura" 
                className="ka-logo w-8 h-8"
              />
              <span className="text-xl font-light tracking-widest text-black hover:text-gold transition-colors">KinAura Admin</span>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-600">Welcome, {user?.full_name}</span>
            <button 
              onClick={() => onNavigate('menu')}
              className="text-black"
            >
              <div className="space-y-1">
                <div className="w-6 h-0.5 bg-black"></div>
                <div className="w-6 h-0.5 bg-black"></div>
                <div className="w-6 h-0.5 bg-black"></div>
              </div>
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex overflow-x-auto border-t border-gray-100">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 px-6 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-gold text-gold bg-gold bg-opacity-5'
                  : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Total Patients</p>
                    <p className="text-3xl font-light text-black">{dashboardData.totalPatients}</p>
                  </div>
                  <div className="text-gold text-2xl">👥</div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Active Members</p>
                    <p className="text-3xl font-light text-black">{dashboardData.activeMembers}</p>
                  </div>
                  <div className="text-gold text-2xl">⭐</div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Monthly Revenue</p>
                    <p className="text-3xl font-light text-black">€{dashboardData.monthlyRevenue?.toLocaleString()}</p>
                  </div>
                  <div className="text-gold text-2xl">💰</div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Avg. Longevity Score</p>
                    <p className="text-3xl font-light text-black">{dashboardData.averageLongevityScore}</p>
                  </div>
                  <div className="text-gold text-2xl">📈</div>
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-medium text-black mb-4">Recent Activity</h3>
              <div className="space-y-4">
                {dashboardData.recentActivity?.map((activity, index) => (
                  <div key={index} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                    <div>
                      <p className="text-sm text-black">{activity.action}</p>
                      <p className="text-xs text-gray-500">{activity.user}</p>
                    </div>
                    <span className="text-xs text-gray-400">{activity.time}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'crm-funnel' && (
          <CRMFunnelDashboard backendUrl={BACKEND_URL} />
        )}

        {activeTab === 'boutique' && (
          <BoutiqueAdmin backendUrl={BACKEND_URL} />
        )}

        {activeTab === 'patients' && (
          <div className="space-y-6">
            {/* Create Patient Form */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-medium text-black mb-4">Create New Patient</h3>
              <form onSubmit={createPatient} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <input
                  type="text"
                  placeholder="Full Name"
                  value={newPatient.full_name}
                  onChange={(e) => setNewPatient({...newPatient, full_name: e.target.value})}
                  className="p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                  required
                />
                <input
                  type="email"
                  placeholder="Email"
                  value={newPatient.email}
                  onChange={(e) => setNewPatient({...newPatient, email: e.target.value})}
                  className="p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                  required
                />
                <input
                  type="tel"
                  placeholder="Phone"
                  value={newPatient.phone}
                  onChange={(e) => setNewPatient({...newPatient, phone: e.target.value})}
                  className="p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                />
                <input
                  type="date"
                  placeholder="Date of Birth"
                  value={newPatient.dob}
                  onChange={(e) => setNewPatient({...newPatient, dob: e.target.value})}
                  className="p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                />
                <select
                  value={newPatient.gender}
                  onChange={(e) => setNewPatient({...newPatient, gender: e.target.value})}
                  className="p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                >
                  <option value="female">Female</option>
                  <option value="male">Male</option>
                  <option value="other">Other</option>
                </select>
                <input
                  type="text"
                  placeholder="Tags (comma separated)"
                  value={newPatient.tags}
                  onChange={(e) => setNewPatient({...newPatient, tags: e.target.value})}
                  className="p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                />
                <div className="md:col-span-2">
                  <button
                    type="submit"
                    disabled={loading}
                    className="pill-button disabled:opacity-50"
                  >
                    {loading ? 'Creating...' : 'Create Patient'}
                  </button>
                </div>
              </form>
            </div>

            {/* Patients List */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-black">Patients ({patients.length})</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Phone</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Membership</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tags</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {patients.map((patient) => (
                      <tr key={patient.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-black">{patient.full_name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{patient.email}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{patient.phone}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            patient.membership_tier === 'elite' ? 'bg-gold bg-opacity-20 text-gold' :
                            patient.membership_tier === 'platinum' ? 'bg-purple-100 text-purple-800' :
                            patient.membership_tier === 'gold' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {patient.membership_tier}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {patient.tags?.join(', ')}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {formatDate(patient.created_at)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'services' && (
          <div className="space-y-6">
            {/* Services Management Header */}
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-2xl font-bold text-[#222428]">Services Management</h2>
                <p className="text-gray-600">Manage your treatment services with text, images, and group assignments</p>
              </div>
              <button
                onClick={() => setShowCreateServiceModal(true)}
                className="bg-[#C8A25A] text-white px-6 py-2 rounded-lg hover:bg-[#B8925A] transition-colors"
              >
                + Create Service
              </button>
            </div>

            {/* Services Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {services.map((service) => (
                <ServiceCard
                  key={service.id}
                  service={service}
                  serviceGroups={serviceGroups}
                  onEdit={(service) => setEditingService(service)}
                  onDelete={(serviceId) => handleDeleteService(serviceId)}
                  onAssignGroup={(serviceId, groupId) => handleAssignServiceToGroup(serviceId, groupId)}
                  backendUrl={`${BACKEND_URL}/api`}
                />
              ))}
            </div>

            {services.length === 0 && (
              <div className="text-center py-12 bg-white rounded-lg">
                <p className="text-gray-500 text-lg mb-4">No services found</p>
                <button
                  onClick={() => setShowCreateServiceModal(true)}
                  className="bg-[#C8A25A] text-white px-6 py-2 rounded-lg hover:bg-[#B8925A] transition-colors"
                >
                  Create Your First Service
                </button>
              </div>
            )}

            {/* Create/Edit Service Modal */}
            {(showCreateServiceModal || editingService) && (
              <ServiceModal
                service={editingService}
                serviceGroups={serviceGroups}
                onClose={() => {
                  setShowCreateServiceModal(false);
                  setEditingService(null);
                }}
                onSave={editingService ? handleUpdateService : handleCreateService}
                backendUrl={`${BACKEND_URL}/api`}
              />
            )}
          </div>
        )}

        {activeTab === 'health-data' && (
          <AdminHealthData backendUrl={`${BACKEND_URL}/api`} />
        )}

        {activeTab === 'chatbot' && (
          <ChatbotAdmin backendUrl={`${BACKEND_URL}/api`} />
        )}

        {activeTab === 'appointments' && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-black">Appointments ({appointments.length})</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Patient</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Service</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date & Time</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Practitioner</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {appointments.map((appointment) => (
                    <tr key={appointment.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-black">{appointment.patient_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{appointment.service_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {formatDate(appointment.appointment_date)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{appointment.practitioner}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          appointment.status === 'completed' ? 'bg-green-100 text-green-800' :
                          appointment.status === 'confirmed' ? 'bg-blue-100 text-blue-800' :
                          appointment.status === 'scheduled' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {appointment.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'formulas' && (
          <div className="space-y-6">
            {/* Create Formula Form */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-medium text-black mb-4">Create New Formula</h3>
              <form onSubmit={createFormula} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <select
                  value={newFormula.patient_id}
                  onChange={(e) => setNewFormula({...newFormula, patient_id: e.target.value})}
                  className="p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                  required
                >
                  <option value="">Select Patient</option>
                  {patients.map((patient) => (
                    <option key={patient.id} value={patient.id}>{patient.full_name}</option>
                  ))}
                </select>
                <input
                  type="text"
                  placeholder="Formula Name"
                  value={newFormula.name}
                  onChange={(e) => setNewFormula({...newFormula, name: e.target.value})}
                  className="p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                  required
                />
                <input
                  type="number"
                  placeholder="Price (cents)"
                  value={newFormula.price_cents}
                  onChange={(e) => setNewFormula({...newFormula, price_cents: parseInt(e.target.value)})}
                  className="p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                  min="15000"
                  required
                />
                <select
                  value={newFormula.packaging}
                  onChange={(e) => setNewFormula({...newFormula, packaging: e.target.value})}
                  className="p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                >
                  <option value="jar">Jar</option>
                  <option value="tube">Tube</option>
                  <option value="bottle">Bottle</option>
                  <option value="serum_bottle">Serum Bottle</option>
                </select>
                <div className="md:col-span-2">
                  <button
                    type="submit"
                    disabled={loading}
                    className="pill-button disabled:opacity-50"
                  >
                    {loading ? 'Creating...' : 'Create Formula'}
                  </button>
                </div>
              </form>
            </div>

            {/* Formulas List */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-black">Formulas ({formulas.length})</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Patient</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Price</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {formulas.map((formula) => (
                      <tr key={formula.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-black">{formula.name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{formula.patient_name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">€{formula.price}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            formula.status === 'finalized' ? 'bg-green-100 text-green-800' :
                            'bg-yellow-100 text-yellow-800'
                          }`}>
                            {formula.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {formatDate(formula.created_at)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'patient-notes' && (
          <div className="space-y-6">
            {!selectedPatient ? (
              /* Patient Selection for Notes */
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-medium text-black mb-4">Select Patient for Notes</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {patients.map((patient) => (
                    <div 
                      key={patient.id}
                      onClick={() => setSelectedPatient(patient)}
                      className="border border-gray-200 rounded-lg p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                    >
                      <h4 className="font-medium text-black">{patient.full_name}</h4>
                      <p className="text-sm text-gray-600">{patient.email}</p>
                      <span className={`inline-block px-2 py-1 mt-2 text-xs rounded-full ${
                        patient.membership_tier === 'elite' ? 'bg-gold bg-opacity-20 text-gold' :
                        patient.membership_tier === 'platinum' ? 'bg-purple-100 text-purple-800' :
                        patient.membership_tier === 'gold' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {patient.membership_tier}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              /* Patient Notes Management */
              <div className="space-y-6">
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-medium text-black">
                      Notes for {selectedPatient.full_name}
                    </h3>
                    <button
                      onClick={() => setSelectedPatient(null)}
                      className="text-gray-500 hover:text-gray-700"
                    >
                      ← Back to Patient List
                    </button>
                  </div>

                  {/* Create New Note Form */}
                  <form onSubmit={createPatientNote} className="space-y-4 mb-6 p-4 bg-gray-50 rounded-lg">
                    <h4 className="font-medium text-black">Add New Note</h4>
                    <input
                      type="text"
                      placeholder="Note Title"
                      value={newNote.title}
                      onChange={(e) => setNewNote({...newNote, title: e.target.value, patient_id: selectedPatient.id})}
                      className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                      required
                    />
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <select
                        value={newNote.category}
                        onChange={(e) => setNewNote({...newNote, category: e.target.value})}
                        className="p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                      >
                        <option value="general">General</option>
                        <option value="medical">Medical</option>
                        <option value="behavior">Behavior</option>
                        <option value="treatment">Treatment</option>
                        <option value="follow_up">Follow Up</option>
                      </select>
                      <label className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={newNote.is_important}
                          onChange={(e) => setNewNote({...newNote, is_important: e.target.checked})}
                          className="rounded"
                        />
                        <span className="text-sm">Mark as Important</span>
                      </label>
                    </div>
                    <textarea
                      placeholder="Note Content"
                      value={newNote.content}
                      onChange={(e) => setNewNote({...newNote, content: e.target.value})}
                      rows={4}
                      className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                      required
                    />
                    <button
                      type="submit"
                      disabled={loading}
                      className="pill-button disabled:opacity-50"
                    >
                      {loading ? 'Creating...' : 'Add Note'}
                    </button>
                  </form>

                  {/* Notes List */}
                  <div className="space-y-4">
                    {patientNotes.map((note) => (
                      <div key={note.id} className={`border rounded-lg p-4 ${note.is_important ? 'border-red-300 bg-red-50' : 'border-gray-200'}`}>
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex items-center space-x-2">
                            <h5 className="font-medium text-black">{note.title}</h5>
                            {note.is_important && <span className="text-red-500 text-sm">⚠️ Important</span>}
                          </div>
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            note.category === 'medical' ? 'bg-red-100 text-red-800' :
                            note.category === 'treatment' ? 'bg-blue-100 text-blue-800' :
                            note.category === 'follow_up' ? 'bg-green-100 text-green-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {note.category}
                          </span>
                        </div>
                        <p className="text-gray-700 mb-2">{note.content}</p>
                        <div className="text-xs text-gray-500 flex justify-between">
                          <span>By: {note.author_name}</span>
                          <span>{formatDate(note.created_at)}</span>
                        </div>
                      </div>
                    ))}
                    {patientNotes.length === 0 && (
                      <p className="text-gray-500 text-center py-8">No notes found for this patient.</p>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'patient-files' && (
          <div className="space-y-6">
            {!selectedPatient ? (
              /* Patient Selection for Files */
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-medium text-black mb-4">Select Patient for File Management</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {patients.map((patient) => (
                    <div 
                      key={patient.id}
                      onClick={() => setSelectedPatient(patient)}
                      className="border border-gray-200 rounded-lg p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                    >
                      <h4 className="font-medium text-black">{patient.full_name}</h4>
                      <p className="text-sm text-gray-600">{patient.email}</p>
                      <span className={`inline-block px-2 py-1 mt-2 text-xs rounded-full ${
                        patient.membership_tier === 'elite' ? 'bg-gold bg-opacity-20 text-gold' :
                        patient.membership_tier === 'platinum' ? 'bg-purple-100 text-purple-800' :
                        patient.membership_tier === 'gold' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {patient.membership_tier}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              /* Patient File Management */
              <div className="space-y-6">
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-medium text-black">
                      Files for {selectedPatient.full_name}
                    </h3>
                    <button
                      onClick={() => setSelectedPatient(null)}
                      className="text-gray-500 hover:text-gray-700"
                    >
                      ← Back to Patient List
                    </button>
                  </div>

                  {/* Patient Folder Statistics */}
                  {patientFolder && (
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-black">{patientFolder.total_files}</div>
                        <div className="text-sm text-gray-600">Total Files</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">{patientFolder.visible_files}</div>
                        <div className="text-sm text-gray-600">Visible to Patient</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-orange-600">{patientFolder.private_files}</div>
                        <div className="text-sm text-gray-600">Admin Only</div>
                      </div>
                      <div className="text-center">
                        <div className="text-sm text-gray-600">Last Updated</div>
                        <div className="text-sm font-medium">{formatDate(patientFolder.last_updated)}</div>
                      </div>
                    </div>
                  )}

                  {/* Upload New File Form */}
                  <form onSubmit={uploadPatientFile} className="space-y-4 mb-6 p-4 bg-blue-50 rounded-lg">
                    <h4 className="font-medium text-black">Upload New File</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <select
                        value={newFile.file_type}
                        onChange={(e) => setNewFile({...newFile, file_type: e.target.value, patient_id: selectedPatient.id})}
                        className="p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                      >
                        <option value="test_result">Test Result</option>
                        <option value="image">Image</option>
                        <option value="report">Report</option>
                        <option value="scan">Scan</option>
                        <option value="other">Other</option>
                      </select>
                      <select
                        value={newFile.file_category}
                        onChange={(e) => setNewFile({...newFile, file_category: e.target.value})}
                        className="p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                      >
                        <option value="general">General</option>
                        <option value="blood_work">Blood Work</option>
                        <option value="imaging">Imaging</option>
                        <option value="consultation">Consultation</option>
                        <option value="treatment">Treatment</option>
                        <option value="progress">Progress</option>
                      </select>
                    </div>
                    <input
                      type="text"
                      placeholder="File Description"
                      value={newFile.description}
                      onChange={(e) => setNewFile({...newFile, description: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                      required
                    />
                    <textarea
                      placeholder="Admin Notes (not visible to patient)"
                      value={newFile.notes}
                      onChange={(e) => setNewFile({...newFile, notes: e.target.value})}
                      rows={2}
                      className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                    />
                    <input
                      type="text"
                      placeholder="Tags (comma separated)"
                      value={newFile.tags}
                      onChange={(e) => setNewFile({...newFile, tags: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                    />
                    <div className="flex items-center space-x-4">
                      <label className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={newFile.visible_to_patient}
                          onChange={(e) => setNewFile({...newFile, visible_to_patient: e.target.checked})}
                          className="rounded"
                        />
                        <span className="text-sm font-medium">📱 Visible to Patient</span>
                      </label>
                      <button
                        type="submit"
                        disabled={loading}
                        className="pill-button disabled:opacity-50"
                      >
                        {loading ? 'Uploading...' : 'Upload File'}
                      </button>
                    </div>
                  </form>

                  {/* Files List */}
                  <div className="space-y-4">
                    <h4 className="font-medium text-black">Patient Files ({patientFiles.length})</h4>
                    {patientFiles.map((file) => (
                      <div key={file.id} className="border rounded-lg p-4 hover:bg-gray-50">
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-1">
                              <h5 className="font-medium text-black">{file.original_filename}</h5>
                              <span className={`px-2 py-1 text-xs rounded-full ${
                                file.file_type === 'test_result' ? 'bg-blue-100 text-blue-800' :
                                file.file_type === 'image' ? 'bg-green-100 text-green-800' :
                                file.file_type === 'report' ? 'bg-purple-100 text-purple-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                                {file.file_type}
                              </span>
                              <span className={`px-2 py-1 text-xs rounded-full ${
                                file.file_category === 'blood_work' ? 'bg-red-100 text-red-800' :
                                file.file_category === 'imaging' ? 'bg-indigo-100 text-indigo-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                                {file.file_category}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600 mb-1">{file.description}</p>
                            {file.notes && (
                              <p className="text-xs text-gray-500 bg-gray-100 p-2 rounded">
                                <strong>Admin Notes:</strong> {file.notes}
                              </p>
                            )}
                            {file.tags && file.tags.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-2">
                                {file.tags.map((tag, index) => (
                                  <span key={index} className="px-2 py-1 bg-gray-200 text-gray-700 text-xs rounded">
                                    {tag}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                          <div className="flex items-center space-x-2 ml-4">
                            <button
                              onClick={() => toggleFileVisibility(file.id, file.visible_to_patient)}
                              className={`px-3 py-1 text-xs rounded-full transition-colors ${
                                file.visible_to_patient
                                  ? 'bg-green-100 text-green-800 hover:bg-green-200'
                                  : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                              }`}
                            >
                              {file.visible_to_patient ? '📱 Visible' : '🔒 Private'}
                            </button>
                            <button
                              onClick={() => deletePatientFile(file.id)}
                              className="px-3 py-1 text-xs bg-red-100 text-red-800 rounded-full hover:bg-red-200 transition-colors"
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                        <div className="text-xs text-gray-500">
                          Uploaded: {formatDate(file.upload_date)}
                        </div>
                      </div>
                    ))}
                    {patientFiles.length === 0 && (
                      <p className="text-gray-500 text-center py-8">No files found for this patient.</p>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'service-groups' && (
          <ServiceGroupsAdmin backendUrl={`${BACKEND_URL}/api`} />
        )}

        {activeTab === 'questionnaires' && (
          <div className="space-y-6">
            {/* Create New Questionnaire Form */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-medium text-black mb-4">Create New Questionnaire</h3>
              <form onSubmit={createQuestionnaire} className="space-y-4">
                <input
                  type="text"
                  placeholder="Questionnaire Title"
                  value={newQuestionnaire.title}
                  onChange={(e) => setNewQuestionnaire({...newQuestionnaire, title: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                  required
                />
                <textarea
                  placeholder="Description"
                  value={newQuestionnaire.description}
                  onChange={(e) => setNewQuestionnaire({...newQuestionnaire, description: e.target.value})}
                  rows={3}
                  className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <select
                    value={newQuestionnaire.category}
                    onChange={(e) => setNewQuestionnaire({...newQuestionnaire, category: e.target.value})}
                    className="p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                  >
                    <option value="medical_history">Medical History</option>
                    <option value="privacy_disclosure">Privacy Disclosure</option>
                    <option value="treatment_consent">Treatment Consent</option>
                    <option value="pre_treatment">Pre-Treatment</option>
                    <option value="post_treatment">Post-Treatment</option>
                    <option value="wellness_assessment">Wellness Assessment</option>
                    <option value="lifestyle">Lifestyle</option>
                    <option value="symptoms">Symptoms</option>
                    <option value="preferences">Preferences</option>
                    <option value="other">Other</option>
                  </select>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={newQuestionnaire.is_required}
                      onChange={(e) => setNewQuestionnaire({...newQuestionnaire, is_required: e.target.checked})}
                      className="w-4 h-4 text-gold border-gray-300 rounded focus:ring-gold"
                    />
                    <span className="text-sm text-gray-700">Required for all patients</span>
                  </label>
                </div>
                <textarea
                  placeholder="Instructions for patients"
                  value={newQuestionnaire.instructions}
                  onChange={(e) => setNewQuestionnaire({...newQuestionnaire, instructions: e.target.value})}
                  rows={2}
                  className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-gold text-white px-6 py-2 rounded hover:bg-yellow-600 disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Create Questionnaire'}
                </button>
              </form>
            </div>

            {/* Existing Questionnaires */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-medium text-black mb-4">Questionnaires</h3>
              <div className="space-y-4">
                {questionnaires.map((questionnaire) => (
                  <div key={questionnaire._id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h4 className="font-medium text-black">{questionnaire.title}</h4>
                        <p className="text-sm text-gray-600">{questionnaire.description}</p>
                      </div>
                      <div className="flex space-x-2">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          questionnaire.category === 'medical_history' ? 'bg-blue-100 text-blue-800' :
                          questionnaire.category === 'treatment_consent' ? 'bg-green-100 text-green-800' :
                          questionnaire.category === 'privacy_disclosure' ? 'bg-purple-100 text-purple-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {questionnaire.category.replace('_', ' ')}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <div className="flex space-x-4">
                        <span>📝 {questionnaire.question_count} questions</span>
                        <span>📊 {questionnaire.assignments?.total || 0} assigned</span>
                        <span>✅ {questionnaire.assignments?.completed || 0} completed</span>
                        <span>⏳ {questionnaire.assignments?.pending || 0} pending</span>
                      </div>
                      <div className="flex space-x-2">
                        <button 
                          onClick={() => {/* TODO: Edit questionnaire */}}
                          className="text-blue-600 hover:text-blue-800"
                        >
                          Edit
                        </button>
                        <button 
                          onClick={() => {
                            setAssignmentForm({...assignmentForm, questionnaire_id: questionnaire._id});
                          }}
                          className="text-green-600 hover:text-green-800"
                        >
                          Assign
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
                {questionnaires.length === 0 && (
                  <p className="text-gray-500 text-center py-8">No questionnaires found. Create your first questionnaire above.</p>
                )}
              </div>
            </div>

            {/* Assignment Form */}
            {assignmentForm.questionnaire_id && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-medium text-black mb-4">Assign Questionnaire</h3>
                <form onSubmit={assignQuestionnaire} className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <select
                      value={assignmentForm.patient_id}
                      onChange={(e) => setAssignmentForm({...assignmentForm, patient_id: e.target.value})}
                      className="p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                      required
                    >
                      <option value="">Select Patient</option>
                      {patients.map((patient) => (
                        <option key={patient.id} value={patient.id}>{patient.full_name}</option>
                      ))}
                    </select>
                    <input
                      type="datetime-local"
                      value={assignmentForm.due_date}
                      onChange={(e) => setAssignmentForm({...assignmentForm, due_date: e.target.value})}
                      className="p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                      placeholder="Due Date (optional)"
                    />
                  </div>
                  <div className="flex space-x-3">
                    <button
                      type="submit"
                      disabled={loading}
                      className="bg-gold text-white px-6 py-2 rounded hover:bg-yellow-600 disabled:opacity-50"
                    >
                      {loading ? 'Assigning...' : 'Assign Questionnaire'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setAssignmentForm({questionnaire_id: '', patient_id: '', due_date: ''})}
                      className="bg-gray-300 text-gray-700 px-6 py-2 rounded hover:bg-gray-400"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            )}
          </div>
        )}

        {activeTab === 'appointments' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-black">Appointment Management</h3>
                <button
                  onClick={() => onNavigate('admin-appointments')}
                  className="bg-gold text-white px-4 py-2 rounded hover:bg-yellow-600"
                >
                  Manage Appointments
                </button>
              </div>
              <p className="text-gray-600 mb-4">
                Manage service availability, appointment slots, bookings, and payment processing. 
                Set up service schedules, block time slots, and monitor booking analytics.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-cream rounded-lg p-4 text-center">
                  <div className="text-2xl mb-2">🗓️</div>
                  <h4 className="font-medium text-charcoal">Service Availability</h4>
                  <p className="text-sm text-gray-600 mt-1">Set up weekly schedules for each service</p>
                </div>
                
                <div className="bg-cream rounded-lg p-4 text-center">
                  <div className="text-2xl mb-2">📅</div>
                  <h4 className="font-medium text-charcoal">Slot Management</h4>
                  <p className="text-sm text-gray-600 mt-1">Generate and manage appointment slots</p>
                </div>
                
                <div className="bg-cream rounded-lg p-4 text-center">
                  <div className="text-2xl mb-2">💳</div>
                  <h4 className="font-medium text-charcoal">Payment Processing</h4>
                  <p className="text-sm text-gray-600 mt-1">Stripe integration for secure payments</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'notifications' && (
          <div className="space-y-6">
            {/* Send Notification Form */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-medium text-black mb-4">Send Notification</h3>
              <form onSubmit={sendNotification} className="space-y-4">
                <input
                  type="text"
                  placeholder="Notification Title"
                  value={notificationForm.title}
                  onChange={(e) => setNotificationForm({...notificationForm, title: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                  required
                />
                <textarea
                  placeholder="Notification Message"
                  value={notificationForm.message}
                  onChange={(e) => setNotificationForm({...notificationForm, message: e.target.value})}
                  rows={3}
                  className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                  required
                />
                
                {/* Target Type Selection */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <select
                    value={notificationForm.target_type}
                    onChange={(e) => setNotificationForm({...notificationForm, target_type: e.target.value})}
                    className="p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                  >
                    <option value="single">Single Patient</option>
                    <option value="tags">By Tags</option>
                    <option value="membership">By Membership</option>
                    <option value="all">All Patients</option>
                  </select>

                  {/* Conditional Target Fields */}
                  {notificationForm.target_type === 'single' && (
                    <select
                      value={notificationForm.target_patient_id}
                      onChange={(e) => setNotificationForm({...notificationForm, target_patient_id: e.target.value})}
                      className="p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                      required
                    >
                      <option value="">Select Patient</option>
                      {patients.map((patient) => (
                        <option key={patient.id} value={patient.id}>{patient.full_name}</option>
                      ))}
                    </select>
                  )}

                  {notificationForm.target_type === 'tags' && (
                    <input
                      type="text"
                      placeholder="Tags (comma separated)"
                      value={notificationForm.target_tags}
                      onChange={(e) => setNotificationForm({...notificationForm, target_tags: e.target.value})}
                      className="p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                      required
                    />
                  )}

                  {notificationForm.target_type === 'membership' && (
                    <select
                      value={notificationForm.target_membership}
                      onChange={(e) => setNotificationForm({...notificationForm, target_membership: e.target.value})}
                      className="p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                      required
                    >
                      <option value="">Select Membership</option>
                      <option value="not_member">Not Member</option>
                      <option value="gold">Gold</option>
                      <option value="platinum">Platinum</option>
                      <option value="elite">Elite</option>
                    </select>
                  )}
                </div>

                <div className="flex space-x-4">
                  <button
                    type="button"
                    onClick={previewNotificationTargets}
                    className="px-4 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50"
                  >
                    Preview Recipients
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="pill-button disabled:opacity-50"
                  >
                    {loading ? 'Sending...' : 'Send Notification'}
                  </button>
                </div>
              </form>
            </div>

            {/* Notification History */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-black">Notification History</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Title</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Message</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Target</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Recipients</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sent</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {notifications.map((notification) => (
                      <tr key={notification.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-black">{notification.title}</td>
                        <td className="px-6 py-4 text-sm text-gray-600 max-w-xs truncate">{notification.message}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{notification.target_type}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{notification.sent_count}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            notification.status === 'sent' ? 'bg-green-100 text-green-800' :
                            notification.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {notification.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {notification.sent_at ? formatDate(notification.sent_at) : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {notifications.length === 0 && (
                  <div className="px-6 py-8 text-center text-gray-500">
                    No notifications sent yet.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'inquiries' && (
          <div>
            {/* Inquiries Stats Summary */}
            {inquiryStats && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Total Inquiries</p>
                      <p className="text-2xl font-bold text-black">{inquiryStats.total_inquiries}</p>
                    </div>
                    <div className="text-3xl">💬</div>
                  </div>
                </div>
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Treatment Interests</p>
                      <p className="text-2xl font-bold text-blue-600">{inquiryStats.by_type.treatment}</p>
                    </div>
                    <div className="text-3xl">💊</div>
                  </div>
                </div>
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Health Concerns</p>
                      <p className="text-2xl font-bold text-red-600">{inquiryStats.by_type.condition}</p>
                    </div>
                    <div className="text-3xl">🏥</div>
                  </div>
                </div>
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Wellness Goals</p>
                      <p className="text-2xl font-bold text-green-600">{inquiryStats.by_type.wellness_goal}</p>
                    </div>
                    <div className="text-3xl">🎯</div>
                  </div>
                </div>
              </div>
            )}

            {/* Inquiry Filters */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-4">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                  <select
                    value={inquiryFilter.status}
                    onChange={(e) => setInquiryFilter({...inquiryFilter, status: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                  >
                    <option value="">All Statuses</option>
                    <option value="new">New</option>
                    <option value="contacted">Contacted</option>
                    <option value="converted">Converted</option>
                    <option value="dismissed">Dismissed</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                  <select
                    value={inquiryFilter.inquiry_type}
                    onChange={(e) => setInquiryFilter({...inquiryFilter, inquiry_type: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                  >
                    <option value="">All Types</option>
                    <option value="treatment">Treatment Interest</option>
                    <option value="condition">Health Concern</option>
                    <option value="wellness_goal">Wellness Goal</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Patient</label>
                  <select
                    value={inquiryFilter.patient_id}
                    onChange={(e) => setInquiryFilter({...inquiryFilter, patient_id: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2"
                  >
                    <option value="">All Patients</option>
                    {patients.map((patient) => (
                      <option key={patient.id} value={patient.id}>{patient.full_name}</option>
                    ))}
                  </select>
                </div>
                <div className="flex items-end">
                  <button
                    onClick={fetchInquiries}
                    className="w-full bg-gold text-white px-4 py-2 rounded-md hover:bg-gold-dark"
                  >
                    Filter Inquiries
                  </button>
                </div>
              </div>
            </div>

            {/* Inquiries List */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-black">Patient Inquiries ({inquiries.length})</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Patient</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Interest</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Priority</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {inquiries.map((inquiry) => (
                      <tr key={inquiry.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-black">{inquiry.patient_info?.full_name || 'Unknown'}</div>
                          <div className="text-sm text-gray-500">{inquiry.patient_info?.email}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="flex items-center text-sm text-gray-600">
                            <span className="mr-2">{getInquiryTypeIcon(inquiry.inquiry_type)}</span>
                            {inquiry.inquiry_type.replace('_', ' ')}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-sm text-black">{inquiry.detected_items.join(', ')}</div>
                          <div className="text-xs text-gray-500 mt-1 max-w-xs truncate">{inquiry.original_message}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs rounded-full border ${getInquiryPriorityColor(inquiry.priority_score)}`}>
                            Priority {inquiry.priority_score}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            inquiry.status === 'new' ? 'bg-blue-100 text-blue-800' :
                            inquiry.status === 'contacted' ? 'bg-yellow-100 text-yellow-800' :
                            inquiry.status === 'converted' ? 'bg-green-100 text-green-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {inquiry.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(inquiry.timestamp).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <div className="flex space-x-2">
                            <button
                              onClick={() => setSelectedInquiry(inquiry)}
                              className="text-gold hover:text-gold-dark"
                            >
                              View Details
                            </button>
                            {inquiry.status === 'new' && (
                              <button
                                onClick={() => handleUpdateInquiryStatus(inquiry.id, 'contacted', 'Admin viewed inquiry')}
                                className="text-green-600 hover:text-green-900"
                              >
                                Mark Contacted
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {inquiries.length === 0 && (
                  <div className="px-6 py-8 text-center text-gray-500">
                    No inquiries found.
                  </div>
                )}
              </div>
            </div>

            {/* Inquiry Details Modal */}
            {selectedInquiry && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                <div className="bg-white rounded-2xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                  <div className="flex justify-between items-start mb-4">
                    <h2 className="text-xl font-bold text-black">Inquiry Details</h2>
                    <button
                      onClick={() => setSelectedInquiry(null)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <h3 className="font-medium text-gray-700">Patient</h3>
                        <p className="text-black">{selectedInquiry.patient_info?.full_name}</p>
                        <p className="text-sm text-gray-500">{selectedInquiry.patient_info?.email}</p>
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-700">Type & Priority</h3>
                        <p className="text-black">{selectedInquiry.inquiry_type.replace('_', ' ')} (Priority {selectedInquiry.priority_score})</p>
                      </div>
                    </div>
                    
                    <div>
                      <h3 className="font-medium text-gray-700">Interests/Concerns</h3>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {selectedInquiry.detected_items.map((item, index) => (
                          <span key={index} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                            {item}
                          </span>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <h3 className="font-medium text-gray-700">Original Message</h3>
                      <p className="text-gray-600 bg-gray-50 p-3 rounded-md">{selectedInquiry.original_message}</p>
                    </div>
                    
                    <div>
                      <h3 className="font-medium text-gray-700">Context</h3>
                      <p className="text-gray-600">{selectedInquiry.context}</p>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <h3 className="font-medium text-gray-700">Status</h3>
                        <select
                          value={selectedInquiry.status}
                          onChange={(e) => handleUpdateInquiryStatus(selectedInquiry.id, e.target.value, 'Status updated by admin')}
                          className="w-full border border-gray-300 rounded-md px-3 py-2 mt-1"
                        >
                          <option value="new">New</option>
                          <option value="contacted">Contacted</option>
                          <option value="converted">Converted</option>
                          <option value="dismissed">Dismissed</option>
                        </select>
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-700">Date</h3>
                        <p className="text-gray-600 mt-1">{new Date(selectedInquiry.timestamp).toLocaleString()}</p>
                      </div>
                    </div>

                    {/* Send Booking Request */}
                    <div className="border-t pt-4">
                      <h3 className="font-medium text-gray-700 mb-2">Send Booking Request</h3>
                      <div className="space-y-3">
                        <div>
                          <label className="block text-sm text-gray-600">Message</label>
                          <textarea
                            value={bookingRequest.message}
                            onChange={(e) => setBookingRequest({...bookingRequest, message: e.target.value})}
                            placeholder={`Hi ${selectedInquiry.patient_info?.full_name}, based on your interest in ${selectedInquiry.detected_items.join(', ')}, we'd love to schedule a consultation...`}
                            className="w-full border border-gray-300 rounded-md px-3 py-2"
                            rows="3"
                          />
                        </div>
                        <div className="flex space-x-3">
                          <button
                            onClick={() => handleSendBookingRequest(selectedInquiry.id)}
                            className="bg-gold text-white px-4 py-2 rounded-md hover:bg-gold-dark"
                            disabled={loading}
                          >
                            {loading ? 'Sending...' : 'Send Booking Request'}
                          </button>
                          {selectedInquiry.booking_sent && (
                            <span className="text-green-600 flex items-center">
                              ✓ Booking request already sent
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'campaigns' && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-medium text-black mb-4">Marketing Campaigns</h3>
            <p className="text-gray-600">Campaign management coming soon...</p>
          </div>
        )}

        {activeTab === 'audit' && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-black">Audit Logs ({auditLogs.length})</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actor</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Entity</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Details</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {auditLogs.map((log) => (
                    <tr key={log.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-black">{log.action}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{log.actor_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{log.entity_table}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{log.details}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {formatDate(log.created_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;