import React, { useEffect, useState } from 'react';
import { apiClient } from './lib/apiClient';

const Profile = ({ onLogin }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const handleEmergentAuth = async () => {
      try {
        // Parse session ID from URL fragment
        const fragment = window.location.hash.substring(1); // Remove #
        const params = new URLSearchParams(fragment);
        const sessionId = params.get('session_id');

        if (!sessionId) {
          setError('No session ID found in callback');
          setLoading(false);
          return;
        }

        // Call backend to exchange session ID for user data
        const response = await apiClient('/api/auth/emergent-auth', {
          method: 'POST',
          headers: {
            'X-Session-ID': sessionId
          },
          skipAuth: true
        });

        if (response.access_token && response.user) {
          // Store authentication data
          localStorage.setItem('token', response.access_token);
          localStorage.setItem('user', JSON.stringify(response.user));
          
          // Call the login handler to update app state
          onLogin(response.user);
          
          // Clear the URL fragment and redirect to dashboard
          window.history.replaceState({}, document.title, window.location.pathname);
          
          // Redirect to appropriate dashboard based on role
          if (response.user.role === 'admin') {
            window.location.href = '/#admin';
          } else {
            window.location.href = '/#dashboard';
          }
        } else {
          setError('Authentication failed - invalid response');
        }

      } catch (err) {
        console.error('Emergent auth error:', err);
        setError(`Authentication failed: ${err.message || 'Unknown error'}`);
      }
      
      setLoading(false);
    };

    // Check if this is an Emergent auth callback
    if (window.location.hash.includes('session_id=')) {
      handleEmergentAuth();
    } else {
      // No session ID, redirect to home
      window.location.href = '/';
    }
  }, [onLogin]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#FDFCFA] via-white to-[#F8F5F0] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Completing authentication...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#FDFCFA] via-white to-[#F8F5F0] flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
            <p className="text-red-600 font-medium">Authentication Error</p>
            <p className="text-red-500 text-sm mt-2">{error}</p>
          </div>
          <button
            onClick={() => window.location.href = '/'}
            className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors"
          >
            Return to Home
          </button>
        </div>
      </div>
    );
  }

  return null;
};

export default Profile;