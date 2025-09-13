import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from './contexts/LanguageContext';

const PatientChatbot = ({ backendUrl, isOpen, onClose }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [userInfo, setUserInfo] = useState(null);
  const [suggestedQuestions, setSuggestedQuestions] = useState([]);
  const [showSources, setShowSources] = useState({});
  const messagesEndRef = useRef(null);
  const { t, language } = useTranslation();

  // Initialize session and load welcome message
  useEffect(() => {
    if (isOpen && !sessionId) {
      const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      setSessionId(newSessionId);
      
      // Add welcome message
      const welcomeMessage = {
        id: 'welcome',
        role: 'assistant',
        content: language === 'it' 
          ? t('rag.welcomeMessage')
          : t('rag.welcomeMessage'),
        timestamp: new Date(),
        confidence: 1.0,
        sources: [],
        medical_disclaimer: '',
        suggested_questions: language === 'it' ? [
          'Quali trattamenti offrite per l\'anti-aging?',
          'Come funziona la terapia NAD+ IV?',
          'Cosa include il protocollo personalizzato?',
          'Come posso prenotare una consulenza?'
        ] : [
          'What treatments do you offer for anti-aging?',
          'How does NAD+ IV therapy work?',
          'What\'s included in the personalized protocol?',
          'How can I book a consultation?'
        ]
      };
      
      setMessages([welcomeMessage]);
      setSuggestedQuestions(welcomeMessage.suggested_questions);
    }
  }, [isOpen, sessionId, language]);

  // Load user info on component mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');
    if (user) {
      setUserInfo(JSON.parse(user));
    }
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || loading) return;

    try {
      const userMessage = {
        id: Date.now(),
        role: 'user',
        content: inputMessage.trim(),
        timestamp: new Date(),
        language: language
      };

      // Add user message to chat
      setMessages(prev => [...prev, userMessage]);
      setLoading(true);
      
      const messageToSend = inputMessage.trim();
      setInputMessage('');

      // Get backend URL from environment
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || backendUrl || 'http://localhost:8001';

      // Prepare enhanced chat request
      const requestBody = {
        message: messageToSend,
        session_id: sessionId,
        language: language,
        context: {
          user_id: userInfo?.id,
          user_name: userInfo?.full_name,
          membership_tier: userInfo?.membership_tier
        }
      };

      console.log('🤖 Sending enhanced chat request:', requestBody);

      const response = await fetch(`${BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(localStorage.getItem('token') && {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          })
        },
        body: JSON.stringify(requestBody)
      });

      if (response.ok) {
        const chatResponse = await response.json();
        console.log('🤖 Enhanced chat response received:', chatResponse);

        // Create enhanced assistant message
        const assistantMessage = {
          id: chatResponse.message_id || Date.now() + 1,
          role: 'assistant',
          content: chatResponse.message,
          timestamp: new Date(),
          language: chatResponse.language,
          
          // RAG-specific fields
          sources: chatResponse.sources || [],
          confidence: chatResponse.confidence || 0,
          response_time: chatResponse.response_time || 0,
          
          // UI enhancements
          medical_disclaimer: chatResponse.medical_disclaimer || '',
          requires_consultation: chatResponse.requires_consultation || false,
          has_protocol_recommendation: chatResponse.has_protocol_recommendation || false,
          protocol_name: chatResponse.protocol_name || null
        };

        // Update messages
        setMessages(prev => [...prev, assistantMessage]);
        
        // Update suggested questions
        if (chatResponse.suggested_questions && chatResponse.suggested_questions.length > 0) {
          setSuggestedQuestions(chatResponse.suggested_questions);
        }

        // Update session ID if returned
        if (chatResponse.session_id && !sessionId) {
          setSessionId(chatResponse.session_id);
        }

      } else {
        console.error('❌ Enhanced chat request failed:', response.status);
        
        // Fallback error message
        const errorMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: language === 'it' 
            ? 'Mi dispiace, sto avendo difficoltà tecniche. Ti prego di riprovare tra poco o contattare il nostro team direttamente.'
            : 'I apologize, I\'m experiencing technical difficulties. Please try again shortly or contact our team directly.',
          timestamp: new Date(),
          isError: true
        };
        setMessages(prev => [...prev, errorMessage]);
      }

    } catch (error) {
      console.error('❌ Chat error:', error);
      
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: language === 'it'
          ? 'Mi dispiace, si è verificato un errore. Ti prego di riprovare.'
          : 'I apologize, an error occurred. Please try again.',
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const sendSuggestedQuestion = async (question) => {
    setInputMessage(question);
    // Small delay to ensure state update
    setTimeout(() => {
      sendMessage();
    }, 100);
  };

  const toggleSources = (messageId) => {
    setShowSources(prev => ({
      ...prev,
      [messageId]: !prev[messageId]
    }));
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl w-full max-w-2xl h-[80vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-[#C8A25A] to-[#B8925A] rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                      d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">KinAura AI Concierge</h3>
              <p className="text-sm text-gray-500">
                {language === 'it' ? 'Medicina Rigenerativa' : 'Regenerative Medicine Expert'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] ${
                message.role === 'user' 
                  ? 'bg-[#C8A25A] text-white' 
                  : message.isError 
                    ? 'bg-red-50 text-red-800 border border-red-200'
                    : 'bg-gray-50 text-gray-900'
              } rounded-2xl px-4 py-3`}>
                
                {/* Message Content */}
                <div className="whitespace-pre-wrap text-sm leading-relaxed">
                  {message.content}
                </div>
                
                {/* Assistant Message Enhancements */}
                {message.role === 'assistant' && !message.isError && (
                  <div className="mt-3 space-y-2">
                    
                    {/* Sources and Citations */}
                    {message.sources && message.sources.length > 0 && (
                      <div className="border-t border-gray-200 pt-2">
                        <button 
                          onClick={() => toggleSources(message.id)}
                          className="text-xs text-[#C8A25A] hover:text-[#B8925A] font-medium flex items-center space-x-1"
                        >
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                          </svg>
                          <span>
                            {showSources[message.id] 
                              ? language === 'it' ? 'Nascondi fonti' : 'Hide sources'
                              : language === 'it' ? `Mostra ${message.sources.length} fonti` : `Show ${message.sources.length} sources`
                            }
                          </span>
                        </button>
                        
                        {showSources[message.id] && (
                          <div className="mt-2 space-y-1">
                            {message.sources.map((source, idx) => (
                              <div key={idx} className="text-xs bg-white border border-gray-200 rounded-lg p-2">
                                <div className="font-medium text-gray-700">{source.title}</div>
                                <div className="text-gray-500 mt-1">{source.content_preview}</div>
                                <div className="flex justify-between items-center mt-1">
                                  <span className="text-[#C8A25A] font-mono">{source.id}</span>
                                  <span className="text-gray-400">
                                    {Math.round(source.similarity * 100)}% {language === 'it' ? 'simile' : 'match'}
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                    
                    {/* Confidence and Response Time */}
                    {(message.confidence !== undefined || message.response_time !== undefined) && (
                      <div className="flex items-center space-x-3 text-xs text-gray-500">
                        {message.confidence !== undefined && (
                          <span className="flex items-center space-x-1">
                            <span>🎯</span>
                            <span>{Math.round(message.confidence * 100)}% {language === 'it' ? 'affidabile' : 'confident'}</span>
                          </span>
                        )}
                        {message.response_time !== undefined && (
                          <span className="flex items-center space-x-1">
                            <span>⚡</span>
                            <span>{message.response_time.toFixed(2)}s</span>
                          </span>
                        )}
                      </div>
                    )}
                    
                    {/* Protocol Recommendation */}
                    {message.has_protocol_recommendation && message.protocol_name && (
                      <div className="bg-gradient-to-r from-[#C8A25A] to-[#B8925A] text-white rounded-lg p-3 mt-2">
                        <div className="flex items-center space-x-2">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <span className="font-semibold text-sm">
                            {language === 'it' ? 'Protocollo Consigliato' : 'Recommended Protocol'}
                          </span>
                        </div>
                        <div className="text-sm mt-1">{message.protocol_name}</div>
                      </div>
                    )}
                    
                    {/* Medical Disclaimer */}
                    {message.medical_disclaimer && (
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-2 mt-2">
                        <div className="flex items-start space-x-2">
                          <svg className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <span className="text-xs text-blue-700">{message.medical_disclaimer}</span>
                        </div>
                      </div>
                    )}
                    
                    {/* Consultation Recommendation */}
                    {message.requires_consultation && (
                      <div className="bg-amber-50 border border-amber-200 rounded-lg p-2 mt-2">
                        <div className="flex items-center space-x-2">
                          <svg className="w-4 h-4 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v3m0 0v3m0-3h3m-3 0H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <span className="text-xs text-amber-700 font-medium">
                            {language === 'it' 
                              ? 'Consulenza personalizzata consigliata'
                              : 'Personalized consultation recommended'
                            }
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                )}
                
                {/* Timestamp */}
                <div className="text-xs text-gray-400 mt-2">
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
          
          {/* Loading Indicator */}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-50 rounded-2xl px-4 py-3">
                <div className="flex items-center space-x-2">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-[#C8A25A] rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-[#C8A25A] rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                    <div className="w-2 h-2 bg-[#C8A25A] rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                  </div>
                  <span className="text-sm text-gray-600">
                    {language === 'it' ? 'KinAura sta pensando...' : 'KinAura is thinking...'}
                  </span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Suggested Questions */}
        {suggestedQuestions.length > 0 && (
          <div className="px-6 py-3 border-t border-gray-100">
            <div className="text-xs text-gray-500 mb-2">
              {language === 'it' ? 'Domande suggerite:' : 'Suggested questions:'}
            </div>
            <div className="flex flex-wrap gap-2">
              {suggestedQuestions.map((question, idx) => (
                <button
                  key={idx}
                  onClick={() => sendSuggestedQuestion(question)}
                  className="text-xs bg-gray-100 hover:bg-[#C8A25A] hover:text-white text-gray-700 px-3 py-1 rounded-full transition-colors"
                  disabled={loading}
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="p-6 border-t border-gray-200">
          <div className="flex space-x-3">
            <div className="flex-1">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={language === 'it' 
                  ? 'Scrivi la tua domanda sui trattamenti KinAura...'
                  : 'Ask about KinAura treatments and protocols...'
                }
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#C8A25A] focus:border-transparent resize-none"
                rows="2"
                disabled={loading}
              />
            </div>
            <button
              onClick={sendMessage}
              disabled={!inputMessage.trim() || loading}
              className="bg-[#C8A25A] hover:bg-[#B8925A] disabled:bg-gray-300 text-white px-6 py-3 rounded-xl transition-colors font-medium"
              data-chatbot-send
            >
              {loading ? (
                <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              )}
            </button>
          </div>
          
          {/* Quick Actions */}
          <div className="flex space-x-2 mt-3">
            <button 
              onClick={() => sendSuggestedQuestion(language === 'it' ? 'Voglio prenotare un appuntamento' : 'I want to book an appointment')}
              className="text-xs bg-[#C8A25A] text-white px-3 py-1 rounded-full hover:bg-[#B8925A] transition-colors"
              disabled={loading}
            >
              {language === 'it' ? '📅 Prenota' : '📅 Book Now'}
            </button>
            <button 
              onClick={() => sendSuggestedQuestion(language === 'it' ? 'Mostrami i vostri trattamenti' : 'Show me your treatments')}
              className="text-xs bg-gray-100 text-gray-700 px-3 py-1 rounded-full hover:bg-gray-200 transition-colors"
              disabled={loading}
            >
              {language === 'it' ? '🏥 Trattamenti' : '🏥 Treatments'}
            </button>
            <button 
              onClick={() => sendSuggestedQuestion(language === 'it' ? 'Contattate il team' : 'Contact the team')}
              className="text-xs bg-gray-100 text-gray-700 px-3 py-1 rounded-full hover:bg-gray-200 transition-colors"
              disabled={loading}
            >
              {language === 'it' ? '📞 Contatto' : '📞 Contact'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PatientChatbot;