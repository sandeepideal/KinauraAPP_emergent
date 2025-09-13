import React, { useState, useEffect } from 'react';

const PatientQuestionnaires = ({ user, onNavigate, onLogoClick }) => {
  const [questionnaires, setQuestionnaires] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [pendingTasks, setPendingTasks] = useState([]);
  const [activeQuestionnaire, setActiveQuestionnaire] = useState(null);
  const [activeDocument, setActiveDocument] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentView, setCurrentView] = useState('tasks'); // tasks, questionnaire, document, upload
  const [uploadFiles, setUploadFiles] = useState([]);
  const [uploadingFiles, setUploadingFiles] = useState(false);

  const API_BASE = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    if (user) {
      fetchPendingTasks();
      fetchQuestionnaires();
      fetchDocuments();
    }
  }, [user]);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  const fetchPendingTasks = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/patient/pending-tasks`, {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setPendingTasks(data.tasks || []);
      }
    } catch (error) {
      console.error('Error fetching pending tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchQuestionnaires = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/patient/questionnaires`, {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setQuestionnaires(data);
      }
    } catch (error) {
      console.error('Error fetching questionnaires:', error);
    }
  };

  const fetchDocuments = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/patient/documents`, {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setDocuments(data);
      }
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'urgent': return 'text-red-600 bg-red-50 border-red-200';
      case 'high': return 'text-orange-600 bg-orange-50 border-orange-200';
      default: return 'text-blue-600 bg-blue-50 border-blue-200';
    }
  };

  const getPriorityIcon = (priority) => {
    switch (priority) {
      case 'urgent': return '🚨';
      case 'high': return '⚡';
      default: return '📋';
    }
  };

  const handleTaskClick = async (task) => {
    if (task.task_type === 'questionnaire') {
      try {
        const response = await fetch(`${API_BASE}/api/patient/questionnaires/${task.task_id}`, {
          headers: getAuthHeaders()
        });

        if (response.ok) {
          const data = await response.json();
          setActiveQuestionnaire(data);
          setCurrentView('questionnaire');
        }
      } catch (error) {
        console.error('Error fetching questionnaire:', error);
      }
    } else if (task.task_type === 'document') {
      const document = documents.find(d => d.assignment_id === task.task_id);
      if (document) {
        setActiveDocument(document);
        setCurrentView('document');
        
        // Mark as viewed
        if (document.status === 'assigned') {
          await markDocumentViewed(task.task_id);
        }
      }
    }
  };

  const markDocumentViewed = async (assignmentId) => {
    try {
      await fetch(`${API_BASE}/api/patient/documents/${assignmentId}/view`, {
        method: 'POST',
        headers: getAuthHeaders()
      });
      fetchDocuments(); // Refresh
    } catch (error) {
      console.error('Error marking document as viewed:', error);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'No due date';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' at ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
  };

  // File upload functionality
  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    const validFiles = files.filter(file => {
      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        alert(`File ${file.name} is too large. Maximum size is 10MB.`);
        return false;
      }
      
      // Validate file type (common document types)
      const allowedTypes = [
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      ];
      
      if (!allowedTypes.includes(file.type)) {
        alert(`File ${file.name} is not a supported format.`);
        return false;
      }
      
      return true;
    });

    setUploadFiles(prev => [...prev, ...validFiles.map(file => ({
      file,
      id: Date.now() + Math.random(),
      category: 'medical_history',
      description: '',
      uploading: false,
      uploaded: false
    }))]);
  };

  const removeFile = (fileId) => {
    setUploadFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const updateFileDetails = (fileId, updates) => {
    setUploadFiles(prev => prev.map(f => 
      f.id === fileId ? { ...f, ...updates } : f
    ));
  };

  const uploadSelectedFiles = async () => {
    const filesToUpload = uploadFiles.filter(f => !f.uploaded);
    if (filesToUpload.length === 0) return;

    setUploadingFiles(true);

    for (const fileData of filesToUpload) {
      try {
        updateFileDetails(fileData.id, { uploading: true });

        const formData = new FormData();
        formData.append('file', fileData.file);
        formData.append('category', fileData.category);
        formData.append('description', fileData.description || fileData.file.name);

        const response = await fetch(`${API_BASE}/api/patient/upload-document`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: formData
        });

        if (response.ok) {
          updateFileDetails(fileData.id, { uploading: false, uploaded: true });
        } else {
          throw new Error('Upload failed');
        }
      } catch (error) {
        console.error('Error uploading file:', error);
        updateFileDetails(fileData.id, { uploading: false, uploaded: false });
        alert(`Failed to upload ${fileData.file.name}`);
      }
    }

    setUploadingFiles(false);
    
    // Refresh documents list
    await fetchDocuments();
    
    // Show success message
    const successCount = uploadFiles.filter(f => f.uploaded).length;
    if (successCount > 0) {
      alert(`Successfully uploaded ${successCount} file(s)!`);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your tasks...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream">
      {/* Header */}
      <div className="app-header">
        <div className="flex items-center space-x-2 cursor-pointer" onClick={onLogoClick || (() => onNavigate('dashboard'))}>
          <img 
            src="/brand/kinaura-symbol.svg" 
            alt="KinAura" 
            className="ka-logo w-8 h-8"
          />
          <span className="kinaura-logo-text hover:text-gold transition-colors">KinAura</span>
        </div>
        <div className="flex items-center space-x-4">
          {currentView !== 'tasks' && (
            <button 
              onClick={() => setCurrentView('tasks')}
              className="pill-button text-sm"
            >
              ← BACK TO TASKS
            </button>
          )}
          <button 
            onClick={() => setCurrentView('upload')}
            className="bg-ka-gold-500 text-white px-4 py-2 rounded-lg hover:bg-ka-gold-600 transition-colors text-sm font-medium"
          >
            📤 Upload Documents
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
        {currentView === 'tasks' && (
          <>
            {/* Page Title */}
            <div className="text-center mb-6">
              <h1 className="text-2xl kinaura-heading mb-2">Pending Tasks</h1>
              <p className="text-gray-600 text-sm kinaura-body">Complete your questionnaires and review documents</p>
            </div>

            {/* Tasks List */}
            <div className="space-y-4">
              {pendingTasks.length === 0 ? (
                <div className="cream-card text-center py-8">
                  <div className="text-gray-400 mb-4">
                    <svg className="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium mb-2 kinaura-subheading">All Caught Up!</h3>
                  <p className="text-gray-600 text-sm kinaura-body">
                    You have no pending questionnaires or documents to complete.
                  </p>
                </div>
              ) : (
                pendingTasks.map((task, index) => (
                  <div
                    key={index}
                    className={`cream-card cursor-pointer hover:shadow-lg transition-shadow border-l-4 ${getPriorityColor(task.priority)}`}
                    onClick={() => handleTaskClick(task)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-4 flex-1">
                        <div className="text-2xl mt-1">
                          {getPriorityIcon(task.priority)}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <h3 className="font-medium kinaura-body">{task.title}</h3>
                            <span className={`text-xs px-2 py-1 rounded-full ${getPriorityColor(task.priority)}`}>
                              {task.priority.toUpperCase()}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600 kinaura-body mb-2">{task.description}</p>
                          <div className="flex items-center space-x-4 text-xs text-gray-500">
                            <span>📅 Assigned: {new Date(task.assigned_at).toLocaleDateString()}</span>
                            {task.due_date && (
                              <span>⏰ Due: {formatDate(task.due_date)}</span>
                            )}
                            <span>⏱️ {task.estimated_duration} min</span>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`px-3 py-1 rounded-full text-sm ${
                          task.task_type === 'questionnaire' 
                            ? 'bg-blue-100 text-blue-700' 
                            : 'bg-green-100 text-green-700'
                        }`}>
                          {task.task_type === 'questionnaire' ? '📝 Questionnaire' : '📄 Document'}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </>
        )}

        {currentView === 'questionnaire' && activeQuestionnaire && (
          <QuestionnaireView 
            questionnaire={activeQuestionnaire}
            onComplete={() => {
              setCurrentView('tasks');
              fetchPendingTasks();
            }}
            apiBase={API_BASE}
            getAuthHeaders={getAuthHeaders}
          />
        )}

        {currentView === 'document' && activeDocument && (
          <DocumentView 
            document={activeDocument}
            onComplete={() => {
              setCurrentView('tasks');
              fetchPendingTasks();
              fetchDocuments();
            }}
            apiBase={API_BASE}
            getAuthHeaders={getAuthHeaders}
          />
        )}

        {currentView === 'upload' && (
          <DocumentUploadView 
            uploadFiles={uploadFiles}
            onFileSelect={handleFileSelect}
            onRemoveFile={removeFile}
            onUpdateFileDetails={updateFileDetails}
            onUploadFiles={uploadSelectedFiles}
            uploading={uploadingFiles}
          />
        )}
      </div>
    </div>
  );
};

// Questionnaire completion component
const QuestionnaireView = ({ questionnaire, onComplete, apiBase, getAuthHeaders }) => {
  const [answers, setAnswers] = useState({});
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [isStarted, setIsStarted] = useState(questionnaire.status === 'in_progress');
  const [saving, setSaving] = useState(false);

  const currentQuestion = questionnaire.questions[currentQuestionIndex];
  const isLastQuestion = currentQuestionIndex === questionnaire.questions.length - 1;

  useEffect(() => {
    // Pre-populate existing answers
    const existingAnswers = {};
    questionnaire.questions.forEach(q => {
      if (q.current_answer) {
        existingAnswers[q.id] = q.current_answer;
      }
    });
    setAnswers(existingAnswers);
  }, [questionnaire]);

  const startQuestionnaire = async () => {
    if (!isStarted) {
      try {
        await fetch(`${apiBase}/api/patient/questionnaires/${questionnaire.assignment_id}/start`, {
          method: 'POST',
          headers: getAuthHeaders()
        });
        setIsStarted(true);
      } catch (error) {
        console.error('Error starting questionnaire:', error);
      }
    }
  };

  const handleAnswerChange = (questionId, value) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: { ...prev[questionId], ...value }
    }));
  };

  const saveAnswers = async () => {
    setSaving(true);
    try {
      const answersToSubmit = Object.entries(answers).map(([questionId, answer]) => ({
        question_id: questionId,
        answer_text: answer.text,
        answer_choices: answer.choices || [],
        answer_number: answer.number,
        answer_date: answer.date
      }));

      await fetch(`${apiBase}/api/patient/questionnaires/${questionnaire.assignment_id}/answers`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          patient_questionnaire_id: questionnaire.assignment_id,
          answers: answersToSubmit
        })
      });
    } catch (error) {
      console.error('Error saving answers:', error);
    } finally {
      setSaving(false);
    }
  };

  const completeQuestionnaire = async () => {
    await saveAnswers();
    
    try {
      await fetch(`${apiBase}/api/patient/questionnaires/${questionnaire.assignment_id}/complete`, {
        method: 'POST',
        headers: getAuthHeaders()
      });
      
      alert('Questionnaire completed successfully!');
      onComplete();
    } catch (error) {
      console.error('Error completing questionnaire:', error);
      alert('Error completing questionnaire');
    }
  };

  const renderQuestionInput = (question) => {
    const answer = answers[question.id] || {};

    switch (question.type) {
      case 'text':
        return (
          <input
            type="text"
            value={answer.text || ''}
            onChange={(e) => handleAnswerChange(question.id, { text: e.target.value })}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-gold"
            placeholder="Your answer..."
          />
        );

      case 'long_text':
        return (
          <textarea
            value={answer.text || ''}
            onChange={(e) => handleAnswerChange(question.id, { text: e.target.value })}
            rows={4}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-gold"
            placeholder="Your answer..."
          />
        );

      case 'multiple_choice':
        return (
          <div className="space-y-2">
            {question.options?.choices?.map((choice, index) => (
              <label key={index} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={answer.choices?.includes(choice) || false}
                  onChange={(e) => {
                    const currentChoices = answer.choices || [];
                    const newChoices = e.target.checked
                      ? [...currentChoices, choice]
                      : currentChoices.filter(c => c !== choice);
                    handleAnswerChange(question.id, { choices: newChoices });
                  }}
                  className="w-4 h-4 text-gold border-gray-300 rounded focus:ring-gold"
                />
                <span className="text-sm">{choice}</span>
              </label>
            ))}
          </div>
        );

      case 'single_choice':
        return (
          <div className="space-y-2">
            {question.options?.choices?.map((choice, index) => (
              <label key={index} className="flex items-center space-x-2">
                <input
                  type="radio"
                  name={`question_${question.id}`}
                  checked={answer.text === choice}
                  onChange={() => handleAnswerChange(question.id, { text: choice })}
                  className="w-4 h-4 text-gold border-gray-300 focus:ring-gold"
                />
                <span className="text-sm">{choice}</span>
              </label>
            ))}
          </div>
        );

      case 'yes_no':
        return (
          <div className="flex space-x-4">
            <label className="flex items-center space-x-2">
              <input
                type="radio"
                name={`question_${question.id}`}
                checked={answer.text === 'Yes'}
                onChange={() => handleAnswerChange(question.id, { text: 'Yes' })}
                className="w-4 h-4 text-gold border-gray-300 focus:ring-gold"
              />
              <span className="text-sm">Yes</span>
            </label>
            <label className="flex items-center space-x-2">
              <input
                type="radio"
                name={`question_${question.id}`}
                checked={answer.text === 'No'}
                onChange={() => handleAnswerChange(question.id, { text: 'No' })}
                className="w-4 h-4 text-gold border-gray-300 focus:ring-gold"
              />
              <span className="text-sm">No</span>
            </label>
          </div>
        );

      case 'number':
        return (
          <input
            type="number"
            value={answer.number || ''}
            onChange={(e) => handleAnswerChange(question.id, { number: parseFloat(e.target.value) })}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-gold"
            placeholder="Enter a number..."
          />
        );

      case 'date':
        return (
          <input
            type="date"
            value={answer.date || ''}
            onChange={(e) => handleAnswerChange(question.id, { date: e.target.value })}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-gold"
          />
        );

      case 'rating_scale':
        const min = question.options?.min || 1;
        const max = question.options?.max || 10;
        return (
          <div className="space-y-4">
            <input
              type="range"
              min={min}
              max={max}
              value={answer.number || min}
              onChange={(e) => handleAnswerChange(question.id, { number: parseInt(e.target.value) })}
              className="w-full"
            />
            <div className="flex justify-between text-sm text-gray-600">
              <span>{min}</span>
              <span className="font-medium">{answer.number || min}</span>
              <span>{max}</span>
            </div>
          </div>
        );

      case 'file_upload':
        return (
          <div className="space-y-4">
            <input
              type="file"
              multiple={question.options?.multiple || false}
              accept={question.options?.accept || "image/*,application/pdf,.doc,.docx"}
              onChange={(e) => {
                const files = Array.from(e.target.files);
                handleAnswerChange(question.id, { files: files });
              }}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-gold"
            />
            {answer.files && answer.files.length > 0 && (
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-700">Selected files:</p>
                {answer.files.map((file, index) => (
                  <div key={index} className="flex items-center space-x-2 text-sm bg-gray-50 p-2 rounded">
                    <span>📎</span>
                    <span className="flex-1">{file.name}</span>
                    <span className="text-gray-500">({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
                  </div>
                ))}
              </div>
            )}
            <p className="text-xs text-gray-500">
              {question.options?.help_text || "Upload relevant documents (max 10MB each)"}
            </p>
          </div>
        );

      default:
        return (
          <input
            type="text"
            value={answer.text || ''}
            onChange={(e) => handleAnswerChange(question.id, { text: e.target.value })}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-gold"
          />
        );
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      {!isStarted ? (
        <div className="cream-card text-center">
          <h2 className="text-2xl kinaura-heading mb-4">{questionnaire.questionnaire.title}</h2>
          {questionnaire.questionnaire.description && (
            <p className="text-gray-600 mb-6 kinaura-body">{questionnaire.questionnaire.description}</p>
          )}
          {questionnaire.questionnaire.instructions && (
            <div className="bg-blue-50 p-4 rounded-lg mb-6">
              <h3 className="font-medium mb-2">Instructions:</h3>
              <p className="text-sm text-gray-700">{questionnaire.questionnaire.instructions}</p>
            </div>
          )}
          <div className="space-y-2 mb-6 text-sm text-gray-600">
            <p>📝 {questionnaire.questions.length} questions</p>
            <p>⏱️ Estimated time: 10-15 minutes</p>
          </div>
          <button
            onClick={startQuestionnaire}
            className="bg-gold text-white px-8 py-3 rounded-lg hover:bg-yellow-600 transition-colors font-medium"
          >
            Start Questionnaire
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Progress */}
          <div className="cream-card">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl kinaura-heading">{questionnaire.questionnaire.title}</h2>
              <span className="text-sm text-gray-600">
                Question {currentQuestionIndex + 1} of {questionnaire.questions.length}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-gold h-2 rounded-full transition-all duration-300" 
                style={{ width: `${((currentQuestionIndex + 1) / questionnaire.questions.length) * 100}%` }}
              ></div>
            </div>
          </div>

          {/* Current Question */}
          <div className="cream-card">
            <div className="mb-6">
              <div className="flex items-start justify-between mb-4">
                <h3 className="text-lg font-medium kinaura-subheading flex-1 pr-4">
                  {currentQuestion.text}
                  {currentQuestion.required && <span className="text-red-500 ml-1">*</span>}
                </h3>
                <span className="text-xs bg-gray-100 px-2 py-1 rounded-full">
                  {currentQuestion.type.replace('_', ' ')}
                </span>
              </div>
              
              {currentQuestion.help_text && (
                <p className="text-sm text-gray-600 mb-4 italic">{currentQuestion.help_text}</p>
              )}

              {renderQuestionInput(currentQuestion)}
            </div>

            {/* Navigation */}
            <div className="flex justify-between items-center pt-6 border-t border-gray-200">
              <button
                onClick={() => setCurrentQuestionIndex(Math.max(0, currentQuestionIndex - 1))}
                disabled={currentQuestionIndex === 0}
                className={`px-6 py-2 rounded-lg ${
                  currentQuestionIndex === 0 
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Previous
              </button>

              <div className="flex space-x-3">
                <button
                  onClick={saveAnswers}
                  disabled={saving}
                  className="px-6 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 disabled:opacity-50"
                >
                  {saving ? 'Saving...' : 'Save Progress'}
                </button>

                {isLastQuestion ? (
                  <button
                    onClick={completeQuestionnaire}
                    className="px-6 py-2 bg-gold text-white rounded-lg hover:bg-yellow-600"
                  >
                    Complete Questionnaire
                  </button>
                ) : (
                  <button
                    onClick={() => {
                      saveAnswers();
                      setCurrentQuestionIndex(Math.min(questionnaire.questions.length - 1, currentQuestionIndex + 1));
                    }}
                    className="px-6 py-2 bg-gold text-white rounded-lg hover:bg-yellow-600"
                  >
                    Next Question
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Document viewing and signing component
const DocumentView = ({ document, onComplete, apiBase, getAuthHeaders }) => {
  const [signature, setSignature] = useState('');
  const [signatureType, setSignatureType] = useState('typed');
  const [signing, setSigning] = useState(false);

  const handleSign = async () => {
    if (!signature.trim()) {
      alert('Please provide a signature');
      return;
    }

    setSigning(true);
    try {
      await fetch(`${apiBase}/api/patient/documents/${document.assignment_id}/sign`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          signature_data: signature,
          signature_type: signatureType
        })
      });

      alert('Document signed successfully!');
      onComplete();
    } catch (error) {
      console.error('Error signing document:', error);
      alert('Error signing document');
    } finally {
      setSigning(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Document Header */}
      <div className="cream-card">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-2xl kinaura-heading mb-2">{document.document.title}</h2>
            <div className="flex items-center space-x-4 text-sm text-gray-600">
              <span>📄 {document.document.document_type.replace('_', ' ')}</span>
              <span>Version {document.document.version}</span>
              {document.expires_at && (
                <span>⏰ Expires: {new Date(document.expires_at).toLocaleDateString()}</span>
              )}
            </div>
          </div>
          <div className={`px-3 py-1 rounded-full text-sm ${
            document.document.requires_signature 
              ? 'bg-orange-100 text-orange-700' 
              : 'bg-green-100 text-green-700'
          }`}>
            {document.document.requires_signature ? 'Signature Required' : 'Review Only'}
          </div>
        </div>
      </div>

      {/* Document Content */}
      <div className="cream-card">
        <div 
          className="prose max-w-none"
          dangerouslySetInnerHTML={{ __html: document.document.content }}
        />
      </div>

      {/* Signature Section */}
      {document.document.requires_signature && document.status !== 'signed' && (
        <div className="cream-card">
          <h3 className="text-lg font-medium mb-4 kinaura-subheading">Digital Signature</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Signature Type:
              </label>
              <select
                value={signatureType}
                onChange={(e) => setSignatureType(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-gold"
              >
                <option value="typed">Typed Signature</option>
                <option value="electronic">Electronic Signature</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your Signature:
              </label>
              <input
                type="text"
                value={signature}
                onChange={(e) => setSignature(e.target.value)}
                placeholder="Type your full name"
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold focus:border-gold"
              />
              <p className="text-xs text-gray-500 mt-1">
                By signing, you acknowledge that you have read and agree to this document.
              </p>
            </div>

            <div className="flex justify-between items-center pt-4 border-t border-gray-200">
              <div className="text-xs text-gray-500">
                <p>📍 Your IP address and timestamp will be recorded for legal purposes</p>
              </div>
              <button
                onClick={handleSign}
                disabled={signing || !signature.trim()}
                className="px-8 py-3 bg-gold text-white rounded-lg hover:bg-yellow-600 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                {signing ? 'Signing...' : 'Sign Document'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Already Signed */}
      {document.status === 'signed' && (
        <div className="cream-card bg-green-50 border border-green-200">
          <div className="flex items-center space-x-3">
            <span className="text-green-600 text-2xl">✅</span>
            <div>
              <h3 className="font-medium text-green-800">Document Signed</h3>
              <p className="text-sm text-green-600">
                Signed on {new Date(document.signed_at).toLocaleDateString()} at {new Date(document.signed_at).toLocaleTimeString()}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Document upload component
const DocumentUploadView = ({ 
  uploadFiles, 
  onFileSelect, 
  onRemoveFile, 
  onUpdateFileDetails, 
  onUploadFiles, 
  uploading 
}) => {
  const fileCategories = [
    { value: 'medical_history', label: 'Medical History' },
    { value: 'lab_results', label: 'Lab Results' },
    { value: 'imaging', label: 'Imaging/Scans' },
    { value: 'prescriptions', label: 'Prescriptions' },
    { value: 'insurance', label: 'Insurance Documents' },
    { value: 'lifestyle', label: 'Lifestyle Information' },
    { value: 'other', label: 'Other' }
  ];

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (fileType) => {
    if (fileType.includes('image')) return '🖼️';
    if (fileType.includes('pdf')) return '📄';
    if (fileType.includes('word')) return '📝';
    if (fileType.includes('excel')) return '📊';
    return '📎';
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Upload Header */}
      <div className="cream-card text-center">
        <h2 className="text-2xl kinaura-heading mb-2">Upload Medical Documents</h2>
        <p className="text-gray-600 kinaura-body mb-6">
          Upload your medical history, lab results, imaging, and other health-related documents
        </p>
        
        {/* File Drop Zone */}
        <div className="border-2 border-dashed border-ka-gold-300 rounded-xl p-8 mb-6 bg-ka-gold-50 hover:bg-ka-gold-100 transition-colors">
          <input
            type="file"
            multiple
            onChange={onFileSelect}
            className="hidden"
            id="file-upload"
            accept="image/*,application/pdf,.doc,.docx,.txt,.xls,.xlsx"
          />
          <label 
            htmlFor="file-upload" 
            className="cursor-pointer block"
          >
            <div className="text-4xl text-ka-gold-500 mb-4">📤</div>
            <h3 className="text-lg font-medium text-ka-gold-700 mb-2">Drop files here or click to upload</h3>
            <p className="text-sm text-ka-gold-600">
              Supported formats: Images, PDF, Word, Excel, Text files (Max 10MB each)
            </p>
          </label>
        </div>

        {/* Upload Guidelines */}
        <div className="bg-blue-50 rounded-lg p-4 text-left">
          <h4 className="font-medium text-blue-800 mb-2">📋 Upload Guidelines:</h4>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• Ensure documents are clear and readable</li>
            <li>• Remove any personal information you don't want to share</li>
            <li>• Organize files by category for easier review</li>
            <li>• Add descriptions to help your healthcare provider understand the context</li>
          </ul>
        </div>
      </div>

      {/* Selected Files */}
      {uploadFiles.length > 0 && (
        <div className="cream-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium kinaura-subheading">
              Selected Files ({uploadFiles.length})
            </h3>
            <button
              onClick={onUploadFiles}
              disabled={uploading || uploadFiles.filter(f => !f.uploaded).length === 0}
              className="bg-ka-gold-500 text-white px-6 py-2 rounded-lg hover:bg-ka-gold-600 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {uploading ? 'Uploading...' : `Upload ${uploadFiles.filter(f => !f.uploaded).length} Files`}
            </button>
          </div>

          <div className="space-y-4">
            {uploadFiles.map((fileData) => (
              <div 
                key={fileData.id} 
                className={`border rounded-lg p-4 ${
                  fileData.uploaded 
                    ? 'border-green-200 bg-green-50' 
                    : fileData.uploading 
                      ? 'border-blue-200 bg-blue-50' 
                      : 'border-gray-200 bg-white'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1">
                    <div className="text-2xl mt-1">
                      {fileData.uploaded ? '✅' : fileData.uploading ? '⏳' : getFileIcon(fileData.file.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-2">
                        <h4 className="font-medium text-gray-900 truncate">
                          {fileData.file.name}
                        </h4>
                        <span className="text-xs text-gray-500">
                          {formatFileSize(fileData.file.size)}
                        </span>
                        {fileData.uploaded && (
                          <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
                            Uploaded
                          </span>
                        )}
                        {fileData.uploading && (
                          <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
                            Uploading...
                          </span>
                        )}
                      </div>

                      {/* Category Selection */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">
                            Category
                          </label>
                          <select
                            value={fileData.category}
                            onChange={(e) => onUpdateFileDetails(fileData.id, { category: e.target.value })}
                            disabled={fileData.uploaded || fileData.uploading}
                            className="w-full text-sm p-2 border border-gray-300 rounded focus:ring-2 focus:ring-ka-gold-500 focus:border-ka-gold-500 disabled:bg-gray-50"
                          >
                            {fileCategories.map(cat => (
                              <option key={cat.value} value={cat.value}>
                                {cat.label}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>

                      {/* Description */}
                      <div className="mb-2">
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          Description (Optional)
                        </label>
                        <input
                          type="text"
                          value={fileData.description}
                          onChange={(e) => onUpdateFileDetails(fileData.id, { description: e.target.value })}
                          disabled={fileData.uploaded || fileData.uploading}
                          placeholder="Brief description of this document..."
                          className="w-full text-sm p-2 border border-gray-300 rounded focus:ring-2 focus:ring-ka-gold-500 focus:border-ka-gold-500 disabled:bg-gray-50"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Remove Button */}
                  {!fileData.uploaded && !fileData.uploading && (
                    <button
                      onClick={() => onRemoveFile(fileData.id)}
                      className="ml-3 text-red-500 hover:text-red-700 p-1"
                      title="Remove file"
                    >
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                    </button>
                  )}
                </div>

                {/* Progress Bar for Uploading Files */}
                {fileData.uploading && (
                  <div className="mt-3">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className="bg-blue-500 h-2 rounded-full animate-pulse" style={{width: '70%'}}></div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Uploads */}
      <div className="cream-card">
        <h3 className="text-lg font-medium kinaura-subheading mb-4">Recent Document History</h3>
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-2">📋</div>
          <p>Your recently uploaded documents will appear here</p>
          <p className="text-sm mt-1">Documents are securely stored and accessible to your healthcare provider</p>
        </div>
      </div>

      {/* Help Section */}
      <div className="cream-card bg-amber-50 border border-amber-200">
        <h3 className="text-lg font-medium text-amber-800 mb-3">💡 Need Help?</h3>
        <div className="text-sm text-amber-700 space-y-2">
          <p><strong>Medical History:</strong> Previous diagnoses, surgeries, hospitalizations</p>
          <p><strong>Lab Results:</strong> Blood work, urine tests, biopsies</p>
          <p><strong>Imaging:</strong> X-rays, MRIs, CT scans, ultrasounds</p>
          <p><strong>Prescriptions:</strong> Current and past medications</p>
          <p><strong>Lifestyle:</strong> Diet logs, exercise records, sleep patterns</p>
        </div>
      </div>
    </div>
  );
};

export default PatientQuestionnaires;