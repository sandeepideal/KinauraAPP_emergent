import React, { useState, useEffect } from 'react';

const ProactiveNotification = ({ user, onClose }) => {
  const [notification, setNotification] = useState(null);
  const [isVisible, setIsVisible] = useState(false);
  const [isClosing, setIsClosing] = useState(false);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
  const API = `${BACKEND_URL}/api`;

  useEffect(() => {
    if (user && user.token) {
      checkForLatestRecommendation();
    }
  }, [user]);

  const checkForLatestRecommendation = async () => {
    try {
      const axios = (await import('axios')).default;
      const response = await axios.get(`${API}/patient/notifications/latest-protocol-recommendation`, {
        headers: {
          'Authorization': `Bearer ${user.token}`
        }
      });

      if (response.data.has_notification) {
        setNotification(response.data.notification);
        setIsVisible(true);
      }
    } catch (error) {
      console.error('Error checking for latest recommendation:', error);
    }
  };

  const markAsRead = async () => {
    if (!notification) return;

    try {
      const axios = (await import('axios')).default;
      await axios.put(`${API}/patient/notifications/proactive/${notification._id}/read`, {}, {
        headers: {
          'Authorization': `Bearer ${user.token}`
        }
      });
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const handleClose = async () => {
    setIsClosing(true);
    await markAsRead();
    
    setTimeout(() => {
      setIsVisible(false);
      setIsClosing(false);
      setNotification(null);
      if (onClose) onClose();
    }, 300);
  };

  const handleLearnMore = () => {
    // Navigate to chatbot to discuss the protocol
    handleClose();
    // Trigger chatbot with pre-filled message about the protocol
    const event = new CustomEvent('openChatbotWithMessage', {
      detail: {
        message: `Tell me more about the ${notification.protocol_name} protocol`
      }
    });
    window.dispatchEvent(event);
  };

  if (!isVisible || !notification) {
    return null;
  }

  return (
    <div className={`fixed inset-0 z-50 flex items-center justify-center p-4 ${isClosing ? 'animate-fadeOut' : 'animate-fadeIn'}`}>
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-50 backdrop-blur-sm"
        onClick={handleClose}
      ></div>
      
      {/* Notification Modal */}
      <div className={`relative bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 transform transition-all duration-300 ${
        isClosing ? 'scale-95 opacity-0' : 'scale-100 opacity-100'
      }`}>
        
        {/* Header */}
        <div className="bg-gradient-to-r from-[#C8A25A] to-[#E6C78A] p-6 rounded-t-2xl">
          <div className="flex justify-between items-start">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-white bg-opacity-20 rounded-full flex items-center justify-center">
                <span className="text-2xl">🌟</span>
              </div>
              <div>
                <h3 className="text-white font-bold text-lg">
                  {notification.language === 'it' ? 'Raccomandazione Protocollo' : 'Protocol Recommendation'}
                </h3>
                <p className="text-white text-opacity-90 text-sm">
                  {notification.language === 'it' ? 'Personalizzato per te' : 'Personalized for you'}
                </p>
              </div>
            </div>
            <button
              onClick={handleClose}
              className="text-white hover:text-gray-200 transition-colors p-1"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Main Message */}
          <div className="prose prose-sm max-w-none">
            {/* Format the message with proper styling */}
            {notification.message.split('\n').map((line, index) => {
              if (line.startsWith('🌟 **') && line.includes('**')) {
                return (
                  <h4 key={index} className="text-lg font-bold text-gray-800 mb-2 flex items-center">
                    <span className="mr-2">🌟</span>
                    {line.replace('🌟 **', '').replace('**', '')}
                  </h4>
                );
              } else if (line.startsWith('**') && line.includes(':**')) {
                return (
                  <h5 key={index} className="font-semibold text-gray-700 mt-3 mb-2">
                    {line.replace(/\*\*/g, '')}
                  </h5>
                );
              } else if (line.startsWith('• **')) {
                const formattedLine = line.replace(/• \*\*(.*?)\*\* - (.*)/g, '• <strong>$1</strong> - $2');
                return (
                  <div key={index} className="text-gray-600 ml-2" dangerouslySetInnerHTML={{ __html: formattedLine }} />
                );
              } else if (line.startsWith('**') && line.includes(':** ')) {
                return (
                  <p key={index} className="text-gray-600 italic mt-3">
                    <strong>{line.split(':** ')[0].replace(/\*\*/g, '')}:</strong> {line.split(':** ')[1]}
                  </p>
                );
              } else if (line.trim() && !line.includes('💫')) {
                return <p key={index} className="text-gray-600">{line}</p>;
              }
              return null;
            })}
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-3 pt-4">
            <button
              onClick={handleLearnMore}
              className="flex-1 bg-gradient-to-r from-[#C8A25A] to-[#E6C78A] text-white px-4 py-3 rounded-xl font-semibold hover:shadow-lg transition-all duration-200 transform hover:scale-105"
            >
              {notification.language === 'it' ? 'Scopri di più' : 'Learn More'}
            </button>
            <button
              onClick={handleClose}
              className="px-4 py-3 border border-gray-300 text-gray-600 rounded-xl font-medium hover:bg-gray-50 transition-colors"
            >
              {notification.language === 'it' ? 'Dopo' : 'Later'}
            </button>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-6 py-4 rounded-b-2xl">
          <div className="flex items-center justify-center space-x-2 text-sm text-gray-500">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>
              {notification.language === 'it' 
                ? 'Raccomandazione basata sul tuo trattamento prenotato' 
                : 'Recommendation based on your booked treatment'
              }
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProactiveNotification;