import React, { useState, useEffect } from 'react';
import PlatformUtils from './utils/platform';

const BookingSuccess = ({ onNavigate }) => {
  const [paymentStatus, setPaymentStatus] = useState('checking');
  const [bookingDetails, setBookingDetails] = useState(null);
  const [error, setError] = useState(null);

  // Get backend URL
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    // Get session_id from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');

    if (sessionId) {
      checkPaymentStatus(sessionId);
    } else {
      setError('No payment session found');
      setPaymentStatus('error');
    }
  }, []);

  const checkPaymentStatus = async (sessionId, attempt = 0) => {
    const maxAttempts = 5;
    const pollInterval = 2000; // 2 seconds

    if (attempt >= maxAttempts) {
      setError('Payment status check timed out. Please check your email for confirmation.');
      setPaymentStatus('error');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${BACKEND_URL}/api/patient/appointments/payment/status/${sessionId}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        
        if (data.payment_status === 'paid') {
          setPaymentStatus('success');
          setBookingDetails(data);
          
          // Add haptic feedback on mobile
          if (PlatformUtils.isMobile()) {
            PlatformUtils.hapticFeedback('medium');
          }
          
          // Show success message
          if (PlatformUtils.isMobile()) {
            PlatformUtils.showAlert(
              'Payment Successful!', 
              'Your appointment has been confirmed. You will receive a confirmation email shortly.'
            );
          }
          
          return;
        } else if (data.status === 'expired') {
          setError('Payment session expired. Please try booking again.');
          setPaymentStatus('error');
          return;
        }

        // If payment is still pending, continue polling
        setPaymentStatus('processing');
        setTimeout(() => checkPaymentStatus(sessionId, attempt + 1), pollInterval);
      } else {
        throw new Error('Failed to check payment status');
      }
    } catch (error) {
      console.error('Error checking payment status:', error);
      setError('Error checking payment status. Please try again.');
      setPaymentStatus('error');
    }
  };

  const formatCurrency = (amount, currency) => {
    if (currency?.toLowerCase() === 'eur') {
      return `€${amount.toFixed(2)}`;
    }
    return `${currency?.toUpperCase() || 'EUR'} ${amount.toFixed(2)}`;
  };

  // Loading/Processing State
  if (paymentStatus === 'checking' || paymentStatus === 'processing') {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center p-4 safe-area-top">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 max-w-md w-full text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold mx-auto mb-4"></div>
          <h2 className="text-xl font-medium text-charcoal mb-2">
            {paymentStatus === 'checking' ? 'Checking Payment Status...' : 'Processing Payment...'}
          </h2>
          <p className="text-gray-600">
            Please wait while we confirm your payment. This may take a few moments.
          </p>
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-700">
              ℹ️ Do not close this page or navigate away
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Success State
  if (paymentStatus === 'success') {
    return (
      <div className="min-h-screen bg-cream p-4 safe-area-top">
        <div className="max-w-2xl mx-auto">
          {/* Success Header */}
          <div className="text-center mb-8">
            <div className="w-20 h-20 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-6">
              <span className="text-white text-3xl">✓</span>
            </div>
            <h1 className="text-3xl font-light text-charcoal mb-2">Payment Successful!</h1>
            <p className="text-lg text-gray-600">Your appointment has been confirmed</p>
          </div>

          {/* Payment Details */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <h2 className="text-lg font-medium text-charcoal mb-4">Payment Confirmation</h2>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Payment Status:</span>
                <span className="font-medium text-green-600">Paid</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Amount:</span>
                <span className="font-medium">
                  {formatCurrency(bookingDetails?.amount_total || 0, bookingDetails?.currency)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Session ID:</span>
                <span className="font-mono text-sm">{bookingDetails?.session_id}</span>
              </div>
            </div>
          </div>

          {/* Next Steps */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <h2 className="text-lg font-medium text-charcoal mb-4">What's Next?</h2>
            
            <div className="space-y-3">
              <div className="flex items-start">
                <div className="w-6 h-6 bg-gold rounded-full flex items-center justify-center mr-3 mt-0.5">
                  <span className="text-white text-xs">1</span>
                </div>
                <div>
                  <p className="font-medium text-charcoal">Confirmation Email</p>
                  <p className="text-sm text-gray-600">You will receive a confirmation email with your appointment details within the next few minutes.</p>
                </div>
              </div>
              
              <div className="flex items-start">
                <div className="w-6 h-6 bg-gold rounded-full flex items-center justify-center mr-3 mt-0.5">
                  <span className="text-white text-xs">2</span>
                </div>
                <div>
                  <p className="font-medium text-charcoal">Appointment Preparation</p>
                  <p className="text-sm text-gray-600">Please arrive 10-15 minutes before your scheduled time. Bring a valid ID and any relevant medical records.</p>
                </div>
              </div>
              
              <div className="flex items-start">
                <div className="w-6 h-6 bg-gold rounded-full flex items-center justify-center mr-3 mt-0.5">
                  <span className="text-white text-xs">3</span>
                </div>
                <div>
                  <p className="font-medium text-charcoal">Need Changes?</p>
                  <p className="text-sm text-gray-600">Contact our concierge team if you need to reschedule or have any questions about your appointment.</p>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3">
            <button
              onClick={() => onNavigate('bookings')}
              className="w-full bg-gold text-white py-3 px-6 rounded-lg font-medium hover:bg-yellow-600 transition-colors mobile-button"
            >
              View My Bookings
            </button>
            
            <button
              onClick={() => onNavigate('dashboard')}
              className="w-full bg-white border border-gray-300 text-charcoal py-3 px-6 rounded-lg font-medium hover:bg-gray-50 transition-colors mobile-button"
            >
              Return to Dashboard
            </button>
            
            <div className="text-center">
              <button
                onClick={() => onNavigate('appointment-booking')}
                className="text-gold font-medium mobile-tap-target"
              >
                Book Another Appointment
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error State
  if (paymentStatus === 'error') {
    return (
      <div className="min-h-screen bg-cream p-4 safe-area-top">
        <div className="max-w-2xl mx-auto">
          {/* Error Header */}
          <div className="text-center mb-8">
            <div className="w-20 h-20 bg-red-500 rounded-full flex items-center justify-center mx-auto mb-6">
              <span className="text-white text-3xl">!</span>
            </div>
            <h1 className="text-3xl font-light text-charcoal mb-2">Payment Issue</h1>
            <p className="text-lg text-gray-600">There was an issue with your payment</p>
          </div>

          {/* Error Details */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <h2 className="text-lg font-medium text-charcoal mb-4">What Happened?</h2>
            <p className="text-gray-600 mb-4">{error}</p>
            
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <p className="text-sm text-yellow-800">
                <strong>Don't worry!</strong> If you were charged, we'll process a refund within 3-5 business days. 
                You can also check your email for any payment confirmation.
              </p>
            </div>
          </div>

          {/* Support Information */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <h2 className="text-lg font-medium text-charcoal mb-4">Need Help?</h2>
            
            <div className="space-y-3">
              <div className="flex items-center">
                <span className="text-gold mr-3">💬</span>
                <div>
                  <p className="font-medium text-charcoal">Contact Concierge</p>
                  <p className="text-sm text-gray-600">Get immediate assistance with your booking</p>
                </div>
              </div>
              
              <div className="flex items-center">
                <span className="text-gold mr-3">📧</span>
                <div>
                  <p className="font-medium text-charcoal">Email Support</p>
                  <p className="text-sm text-gray-600">support@kinaura.com</p>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3">
            <button
              onClick={() => onNavigate('appointment-booking')}
              className="w-full bg-gold text-white py-3 px-6 rounded-lg font-medium hover:bg-yellow-600 transition-colors mobile-button"
            >
              Try Booking Again
            </button>
            
            <button
              onClick={() => onNavigate('concierge')}
              className="w-full bg-white border border-gray-300 text-charcoal py-3 px-6 rounded-lg font-medium hover:bg-gray-50 transition-colors mobile-button"
            >
              Contact Support
            </button>
            
            <div className="text-center">
              <button
                onClick={() => onNavigate('dashboard')}
                className="text-gray-600 mobile-tap-target"
              >
                Return to Dashboard
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default BookingSuccess;