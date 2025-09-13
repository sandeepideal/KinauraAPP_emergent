import React, { useState, useEffect } from 'react';

const Concierge = ({ user, onNavigate }) => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [activeSupport, setActiveSupport] = useState('chat');

  // Mock conversation data
  const mockMessages = [
    {
      id: 1,
      sender: 'Dr. Rossi',
      message: 'Good morning! How are you feeling after your last Ozone Therapy session?',
      timestamp: '2024-01-22 09:30',
      isFromPatient: false,
      avatar: '👨‍⚕️'
    },
    {
      id: 2,
      sender: 'You',
      message: 'Much better, thank you! I noticed improved energy levels and my skin looks more radiant.',
      timestamp: '2024-01-22 10:15',
      isFromPatient: true,
      avatar: '👤'
    },
    {
      id: 3,
      sender: 'Dr. Rossi',
      message: 'Excellent! Based on your progress, I recommend scheduling your next IV Therapy session. Would next week work for you?',
      timestamp: '2024-01-22 10:20',
      isFromPatient: false,
      avatar: '👨‍⚕️'
    },
    {
      id: 4,
      sender: 'Nurse Maria',
      message: 'Your custom skincare formulation is ready for pickup. It includes the new peptide complex we discussed.',
      timestamp: '2024-01-22 14:45',
      isFromPatient: false,
      avatar: '👩‍⚕️'
    }
  ];

  const quickActions = [
    { id: 1, title: 'Book Appointment', icon: '📅', action: () => onNavigate('services') },
    { id: 2, title: 'Request Callback', icon: '📞', action: () => {} },
    { id: 3, title: 'Emergency Contact', icon: '🚨', action: () => {} },
    { id: 4, title: 'Prescription Refill', icon: '💊', action: () => {} }
  ];

  const supportTeam = [
    { id: 1, name: 'Dr. Rossi', role: 'Medical Director', avatar: '👨‍⚕️', status: 'online' },
    { id: 2, name: 'Dr. Bianchi', role: 'Aesthetic Medicine', avatar: '👩‍⚕️', status: 'online' },
    { id: 3, name: 'Nurse Maria', role: 'Clinical Coordinator', avatar: '👩‍⚕️', status: 'away' },
    { id: 4, name: 'Sarah', role: 'Concierge Support', avatar: '👤', status: 'online' }
  ];

  useEffect(() => {
    setMessages(mockMessages);
  }, []);

  const handleSendMessage = () => {
    if (newMessage.trim()) {
      const message = {
        id: Date.now(),
        sender: 'You',
        message: newMessage,
        timestamp: new Date().toLocaleString('it-IT'),
        isFromPatient: true,
        avatar: '👤'
      };
      setMessages([...messages, message]);
      setNewMessage('');
    }
  };

  const formatTime = (timestamp) => {
    try {
      // Handle both string timestamps and Date objects
      const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
      
      // Check if date is valid
      if (isNaN(date.getTime())) {
        return timestamp; // Return original if can't parse
      }
      
      return date.toLocaleTimeString('it-IT', { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    } catch (error) {
      return timestamp; // Return original timestamp if parsing fails
    }
  };

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
          <span className="kinaura-logo-text">Concierge Support</span>
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

      <div className="flex-1 content-above-kintsugi">
        {/* Tab Navigation */}
        <div className="p-6 pb-0">
          <div className="flex space-x-3 mb-4">
            <button
              onClick={() => setActiveSupport('chat')}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                activeSupport === 'chat' 
                  ? 'pill-button' 
                  : 'bg-white border border-gray-300 text-gray-600 hover:bg-gray-50'
              }`}
            >
              💬 Chat
            </button>
            <button
              onClick={() => setActiveSupport('team')}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                activeSupport === 'team' 
                  ? 'pill-button' 
                  : 'bg-white border border-gray-300 text-gray-600 hover:bg-gray-50'
              }`}
            >
              👥 Team
            </button>
            <button
              onClick={() => setActiveSupport('actions')}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                activeSupport === 'actions' 
                  ? 'pill-button' 
                  : 'bg-white border border-gray-300 text-gray-600 hover:bg-gray-50'
              }`}
            >
              ⚡ Quick Actions
            </button>
          </div>
        </div>

        {/* Chat Tab */}
        {activeSupport === 'chat' && (
          <div className="flex flex-col h-[calc(100vh-200px)]">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 pt-0">
              <div className="space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.isFromPatient ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`max-w-xs ${message.isFromPatient ? 'order-2' : 'order-1'}`}>
                      <div className={`rounded-lg p-3 ${
                        message.isFromPatient 
                          ? 'bg-black text-white' 
                          : 'bg-white border border-gray-200'
                      }`}>
                        {!message.isFromPatient && (
                          <div className="flex items-center space-x-2 mb-1">
                            <span className="text-lg">{message.avatar}</span>
                            <span className="text-xs font-medium text-gray-600">
                              {message.sender}
                            </span>
                          </div>
                        )}
                        <p className="text-sm kinaura-body">{message.message}</p>
                      </div>
                      <p className="text-xs text-gray-500 mt-1 px-1">
                        {formatTime(message.timestamp)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Message Input */}
            <div className="p-6 pt-0">
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  placeholder="Type your message..."
                  className="flex-1 p-3 border border-gray-300 rounded-full focus:outline-none focus:border-gold bg-white kinaura-body"
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                />
                <button
                  onClick={handleSendMessage}
                  className="pill-button px-6"
                >
                  Send
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Team Tab */}
        {activeSupport === 'team' && (
          <div className="p-6 pt-0">
            <div className="cream-card">
              <h3 className="text-lg font-medium mb-4 kinaura-subheading">Medical Team</h3>
              <div className="space-y-4">
                {supportTeam.map((member) => (
                  <div key={member.id} className="treatment-item">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="relative">
                          <span className="text-2xl">{member.avatar}</span>
                          <div className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full border-2 border-white ${
                            member.status === 'online' ? 'bg-green-500' : 
                            member.status === 'away' ? 'bg-yellow-500' : 'bg-gray-400'
                          }`}></div>
                        </div>
                        <div>
                          <h4 className="font-medium text-sm kinaura-body">{member.name}</h4>
                          <p className="text-xs text-gray-600 kinaura-body">{member.role}</p>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <button className="text-gold hover:text-yellow-600 text-sm">
                          💬
                        </button>
                        <button className="text-gold hover:text-yellow-600 text-sm">
                          📞
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Quick Actions Tab */}
        {activeSupport === 'actions' && (
          <div className="p-6 pt-0">
            <div className="cream-card">
              <h3 className="text-lg font-medium mb-4 kinaura-subheading">Quick Actions</h3>
              <div className="grid grid-cols-2 gap-4">
                {quickActions.map((action) => (
                  <button
                    key={action.id}
                    onClick={action.action}
                    className="cream-card text-center hover:shadow-md transition-shadow p-4"
                  >
                    <div className="text-2xl mb-2">{action.icon}</div>
                    <span className="text-sm font-medium kinaura-body">{action.title}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Emergency Contact */}
            <div className="cream-card mt-4 border-2 border-red-200">
              <div className="text-center">
                <div className="text-3xl mb-2">🚨</div>
                <h3 className="text-lg font-medium mb-2 text-red-600">Emergency Contact</h3>
                <p className="text-sm text-gray-600 mb-4 kinaura-body">
                  For urgent medical concerns outside clinic hours
                </p>
                <a 
                  href="tel:+39123456789" 
                  className="pill-button bg-red-600 hover:bg-red-700 text-white"
                >
                  Call Emergency Line
                </a>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Concierge;