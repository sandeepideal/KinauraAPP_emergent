import React, { useState, useEffect } from 'react';
import PlatformUtils from './utils/platform';

const AppointmentBooking = ({ user, onNavigate }) => {
  const [selectedService, setSelectedService] = useState(null);
  const [services, setServices] = useState([]);
  const [availableSlots, setAvailableSlots] = useState({});
  const [selectedDate, setSelectedDate] = useState(null);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [loading, setLoading] = useState(false);
  const [bookingStep, setBookingStep] = useState('services'); // services, calendar, confirmation
  const [bookingDetails, setBookingDetails] = useState(null);
  const [paymentLoading, setPaymentLoading] = useState(false);

  // Get backend URL
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    fetchServices();
  }, []);

  useEffect(() => {
    if (selectedService) {
      fetchAvailableSlots(selectedService.id);
    }
  }, [selectedService]);

  const fetchServices = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${BACKEND_URL}/api/services`);
      if (response.ok) {
        const data = await response.json();
        setServices(data.services || []);
      }
    } catch (error) {
      console.error('Error fetching services:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableSlots = async (serviceId) => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${BACKEND_URL}/api/patient/appointments/availability/${serviceId}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        setAvailableSlots(data.calendar || {});
      }
    } catch (error) {
      console.error('Error fetching available slots:', error);
    } finally {
      setLoading(false);
    }
  };

  const bookAppointment = async () => {
    if (!selectedService || !selectedDate || !selectedSlot) return;

    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const bookingData = {
        service_id: selectedService.id,
        appointment_date: selectedDate,
        start_time: selectedSlot.start_time,
        notes: `Appointment booked via ${PlatformUtils.isMobile() ? 'mobile app' : 'web'}`
      };

      const response = await fetch(`${BACKEND_URL}/api/patient/appointments/book`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(bookingData)
      });

      if (response.ok) {
        const data = await response.json();
        setBookingDetails(data);
        setBookingStep('confirmation');
        
        // Add haptic feedback on mobile
        if (PlatformUtils.isMobile()) {
          PlatformUtils.hapticFeedback('medium');
        }
      } else {
        const errorData = await response.json();
        alert(`Booking failed: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error booking appointment:', error);
      alert('Failed to book appointment. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const processPayment = async () => {
    if (!bookingDetails) return;

    try {
      setPaymentLoading(true);
      const token = localStorage.getItem('token');
      
      const paymentData = {
        booking_id: bookingDetails.booking_id,
        origin_url: window.location.origin
      };

      const response = await fetch(`${BACKEND_URL}/api/patient/appointments/payment`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(paymentData)
      });

      if (response.ok) {
        const data = await response.json();
        // Redirect to Stripe checkout
        window.location.href = data.checkout_url;
      } else {
        const errorData = await response.json();
        alert(`Payment setup failed: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error setting up payment:', error);
      alert('Failed to set up payment. Please try again.');
    } finally {
      setPaymentLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatTime = (timeString) => {
    const [hours, minutes] = timeString.split(':');
    const date = new Date();
    date.setHours(parseInt(hours), parseInt(minutes));
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  // Service Selection Step
  if (bookingStep === 'services') {
    return (
      <div className="min-h-screen bg-cream p-4 safe-area-top">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <button
              onClick={() => onNavigate('dashboard')}
              className="text-charcoal text-2xl"
              aria-label="Back to dashboard"
            >
              ←
            </button>
            <h1 className="text-2xl font-light text-charcoal">Book Appointment</h1>
            <div></div>
          </div>

          {/* Service Selection */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <h2 className="text-lg font-medium text-charcoal mb-4">Select a Service</h2>
            
            {loading ? (
              <div className="flex justify-center items-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold"></div>
              </div>
            ) : (
              <div className="grid gap-4">
                {services.map((service) => (
                  <div
                    key={service.id}
                    onClick={() => {
                      setSelectedService(service);
                      setBookingStep('calendar');
                    }}
                    className="border border-gray-200 rounded-lg p-4 cursor-pointer hover:shadow-md transition-shadow mobile-tap-target"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-medium text-charcoal">{service.name}</h3>
                        <p className="text-sm text-gray-600 mt-1">{service.description}</p>
                        <div className="flex items-center mt-2 text-sm text-gray-500">
                          <span className="mr-4">⏱️ {service.duration || '60'} min</span>
                          <span>💰 €{service.price}</span>
                        </div>
                      </div>
                      <div className="text-gold text-xl">→</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Calendar Selection Step
  if (bookingStep === 'calendar') {
    const sortedDates = Object.keys(availableSlots).sort();
    
    return (
      <div className="min-h-screen bg-cream p-4 safe-area-top">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <button
              onClick={() => setBookingStep('services')}
              className="text-charcoal text-2xl"
              aria-label="Back to services"
            >
              ←
            </button>
            <h1 className="text-xl font-light text-charcoal">Choose Date & Time</h1>
            <div></div>
          </div>

          {/* Selected Service Info */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
            <div className="flex items-center">
              <div>
                <h3 className="font-medium text-charcoal">{selectedService?.name}</h3>
                <p className="text-sm text-gray-600">
                  {selectedService?.duration || '60'} min • €{selectedService?.price}
                </p>
              </div>
            </div>
          </div>

          {/* Calendar */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-medium text-charcoal mb-4">Available Times</h2>
            
            {loading ? (
              <div className="flex justify-center items-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold"></div>
              </div>
            ) : sortedDates.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500">No available appointments found.</p>
                <p className="text-sm text-gray-400 mt-2">Please try selecting a different service or check back later.</p>
              </div>
            ) : (
              <div className="space-y-6">
                {sortedDates.map((date) => (
                  <div key={date} className="border-b border-gray-100 pb-4 last:border-b-0">
                    <h3 className="font-medium text-charcoal mb-3">{formatDate(date)}</h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                      {availableSlots[date].map((slot) => (
                        <button
                          key={`${date}-${slot.start_time}`}
                          onClick={() => {
                            setSelectedDate(date);
                            setSelectedSlot(slot);
                            bookAppointment();
                          }}
                          disabled={loading}
                          className="border border-gray-300 rounded-lg p-3 text-center hover:border-gold hover:bg-gold hover:text-white transition-colors mobile-button disabled:opacity-50"
                        >
                          <div className="font-medium">{formatTime(slot.start_time)}</div>
                          <div className="text-xs mt-1">
                            {slot.available_spots} spot{slot.available_spots !== 1 ? 's' : ''}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Confirmation Step
  if (bookingStep === 'confirmation') {
    return (
      <div className="min-h-screen bg-cream p-4 safe-area-top">
        <div className="max-w-2xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-gold rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-white text-2xl">✓</span>
            </div>
            <h1 className="text-2xl font-light text-charcoal">Appointment Reserved</h1>
            <p className="text-gray-600 mt-2">Complete payment to confirm your booking</p>
          </div>

          {/* Booking Details */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <h2 className="text-lg font-medium text-charcoal mb-4">Booking Details</h2>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Service:</span>
                <span className="font-medium">{selectedService?.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Date:</span>
                <span className="font-medium">{formatDate(selectedDate)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Time:</span>
                <span className="font-medium">{formatTime(selectedSlot?.start_time)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Duration:</span>
                <span className="font-medium">{selectedService?.duration || '60'} minutes</span>
              </div>
              <div className="border-t pt-3 mt-3">
                <div className="flex justify-between text-lg">
                  <span className="font-medium">Total:</span>
                  <span className="font-medium text-gold">€{bookingDetails?.amount}</span>
                </div>
              </div>
            </div>

            <div className="mt-4 p-3 bg-cream rounded-lg">
              <p className="text-sm text-gray-600">
                <strong>Confirmation Code:</strong> {bookingDetails?.confirmation_code}
              </p>
            </div>
          </div>

          {/* Payment Section */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <h2 className="text-lg font-medium text-charcoal mb-4">Payment</h2>
            <p className="text-gray-600 mb-4">
              Secure payment processing powered by Stripe. Your payment information is encrypted and secure.
            </p>
            
            <button
              onClick={processPayment}
              disabled={paymentLoading}
              className="w-full bg-gold text-white py-3 px-6 rounded-lg font-medium hover:bg-yellow-600 transition-colors disabled:opacity-50 mobile-button"
            >
              {paymentLoading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Processing...
                </div>
              ) : (
                `Pay €${bookingDetails?.amount} with Stripe`
              )}
            </button>
          </div>

          {/* Actions */}
          <div className="text-center space-y-3">
            <button
              onClick={() => onNavigate('bookings')}
              className="text-gold font-medium mobile-tap-target"
            >
              View My Bookings
            </button>
            <br />
            <button
              onClick={() => {
                setBookingStep('services');
                setSelectedService(null);
                setSelectedDate(null);
                setSelectedSlot(null);
                setBookingDetails(null);
              }}
              className="text-gray-600 mobile-tap-target"
            >
              Book Another Appointment
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default AppointmentBooking;