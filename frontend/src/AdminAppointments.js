import React, { useState, useEffect } from 'react';

const AdminAppointments = ({ user, onNavigate }) => {
  const [activeTab, setActiveTab] = useState('bookings');
  const [services, setServices] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [availability, setAvailability] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedService, setSelectedService] = useState('');

  // Form states
  const [availabilityForm, setAvailabilityForm] = useState({
    service_id: '',
    days_of_week: [],
    start_time: '09:00',
    end_time: '17:00',
    slot_duration: 60,
    buffer_time: 15
  });

  const [slotGenerationForm, setSlotGenerationForm] = useState({
    service_id: '',
    start_date: '',
    end_date: ''
  });

  const [blockSlotForm, setBlockSlotForm] = useState({
    service_id: '',
    date: '',
    start_time: '',
    end_time: '',
    reason: 'admin_use',
    notes: ''
  });

  // Get backend URL
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    fetchServices();
    fetchBookings();
  }, []);

  useEffect(() => {
    if (selectedService) {
      fetchAvailability(selectedService);
    }
  }, [selectedService]);

  const fetchServices = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/services`);
      if (response.ok) {
        const data = await response.json();
        setServices(data.services || []);
      }
    } catch (error) {
      console.error('Error fetching services:', error);
    }
  };

  const fetchBookings = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/admin/appointments/bookings`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setBookings(data || []);
      }
    } catch (error) {
      console.error('Error fetching bookings:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailability = async (serviceId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${BACKEND_URL}/api/admin/services/${serviceId}/availability`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      
      if (response.ok) {
        const data = await response.json();
        setAvailability(data || []);
      }
    } catch (error) {
      console.error('Error fetching availability:', error);
    }
  };

  const createAvailability = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(
        `${BACKEND_URL}/api/admin/services/${availabilityForm.service_id}/availability`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(availabilityForm)
        }
      );

      if (response.ok) {
        alert('Availability created successfully!');
        setAvailabilityForm({
          service_id: '',
          days_of_week: [],
          start_time: '09:00',
          end_time: '17:00',
          slot_duration: 60,
          buffer_time: 15
        });
        if (selectedService) {
          fetchAvailability(selectedService);
        }
      } else {
        const errorData = await response.json();
        alert(`Error: ${errorData.detail}`);
      }
    } catch (error) {
      console.error('Error creating availability:', error);
      alert('Failed to create availability');
    } finally {
      setLoading(false);
    }
  };

  const generateSlots = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const params = new URLSearchParams({
        service_id: slotGenerationForm.service_id,
        start_date: slotGenerationForm.start_date,
        end_date: slotGenerationForm.end_date
      });

      const response = await fetch(
        `${BACKEND_URL}/api/admin/appointments/slots/generate?${params}`,
        {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );

      if (response.ok) {
        const data = await response.json();
        alert(`Successfully generated ${data.slots_created} appointment slots!`);
        setSlotGenerationForm({
          service_id: '',
          start_date: '',
          end_date: ''
        });
      } else {
        const errorData = await response.json();
        alert(`Error: ${errorData.detail}`);
      }
    } catch (error) {
      console.error('Error generating slots:', error);
      alert('Failed to generate slots');
    } finally {
      setLoading(false);
    }
  };

  const blockSlot = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${BACKEND_URL}/api/admin/appointments/slots/block`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(blockSlotForm)
      });

      if (response.ok) {
        alert('Slot blocked successfully!');
        setBlockSlotForm({
          service_id: '',
          date: '',
          start_time: '',
          end_time: '',
          reason: 'admin_use',
          notes: ''
        });
      } else {
        const errorData = await response.json();
        alert(`Error: ${errorData.detail}`);
      }
    } catch (error) {
      console.error('Error blocking slot:', error);
      alert('Failed to block slot');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
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

  const getDayName = (dayIndex) => {
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    return days[dayIndex];
  };

  const getStatusBadge = (status) => {
    const statusColors = {
      pending: 'bg-yellow-100 text-yellow-800',
      confirmed: 'bg-green-100 text-green-800',
      completed: 'bg-blue-100 text-blue-800',
      cancelled: 'bg-red-100 text-red-800',
      no_show: 'bg-gray-100 text-gray-800'
    };

    return (
      <span className={`px-2 py-1 text-xs rounded-full ${statusColors[status] || 'bg-gray-100 text-gray-800'}`}>
        {status.replace('_', ' ').toUpperCase()}
      </span>
    );
  };

  const getPaymentStatusBadge = (paymentStatus) => {
    const statusColors = {
      pending: 'bg-yellow-100 text-yellow-800',
      processing: 'bg-blue-100 text-blue-800',
      paid: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      refunded: 'bg-purple-100 text-purple-800'
    };

    return (
      <span className={`px-2 py-1 text-xs rounded-full ${statusColors[paymentStatus] || 'bg-gray-100 text-gray-800'}`}>
        {paymentStatus.toUpperCase()}
      </span>
    );
  };

  const tabs = [
    { id: 'bookings', name: 'Bookings', icon: '📅' },
    { id: 'availability', name: 'Availability', icon: '🗓️' },
    { id: 'slots', name: 'Slot Management', icon: '⚙️' }
  ];

  return (
    <div className="min-h-screen bg-cream">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <button
            onClick={() => onNavigate('admin')}
            className="text-charcoal text-2xl"
          >
            ←
          </button>
          <h1 className="text-xl font-medium text-charcoal">Appointment Management</h1>
          <div></div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white border-b border-gray-200">
        <div className="flex overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-shrink-0 px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-gold text-gold bg-gold bg-opacity-5'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.name}
            </button>
          ))}
        </div>
      </div>

      <div className="p-4">
        {/* Bookings Tab */}
        {activeTab === 'bookings' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-medium text-charcoal mb-4">Recent Bookings</h2>
              
              {loading ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold"></div>
                </div>
              ) : bookings.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No bookings found</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-2 text-sm font-medium text-gray-600">Patient</th>
                        <th className="text-left py-2 text-sm font-medium text-gray-600">Service</th>
                        <th className="text-left py-2 text-sm font-medium text-gray-600">Date & Time</th>
                        <th className="text-left py-2 text-sm font-medium text-gray-600">Status</th>
                        <th className="text-left py-2 text-sm font-medium text-gray-600">Payment</th>
                        <th className="text-left py-2 text-sm font-medium text-gray-600">Amount</th>
                      </tr>
                    </thead>
                    <tbody>
                      {bookings.map((booking) => (
                        <tr key={booking._id} className="border-b border-gray-100">
                          <td className="py-3">
                            <div>
                              <div className="font-medium text-charcoal">
                                {booking.patient?.full_name || 'Unknown Patient'}
                              </div>
                              <div className="text-sm text-gray-500">
                                {booking.patient?.email}
                              </div>
                            </div>
                          </td>
                          <td className="py-3">
                            <div className="font-medium text-charcoal">
                              {booking.service?.name || 'Unknown Service'}
                            </div>
                          </td>
                          <td className="py-3">
                            <div>
                              <div className="font-medium text-charcoal">
                                {formatDate(booking.appointment_date)}
                              </div>
                              <div className="text-sm text-gray-500">
                                {formatTime(booking.start_time)} - {formatTime(booking.end_time)}
                              </div>
                            </div>
                          </td>
                          <td className="py-3">
                            {getStatusBadge(booking.status)}
                          </td>
                          <td className="py-3">
                            {getPaymentStatusBadge(booking.payment_status)}
                          </td>
                          <td className="py-3">
                            <span className="font-medium text-charcoal">
                              €{booking.amount}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Availability Tab */}
        {activeTab === 'availability' && (
          <div className="space-y-6">
            {/* Create Availability Form */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-medium text-charcoal mb-4">Create Service Availability</h2>
              
              <form onSubmit={createAvailability} className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Service</label>
                    <select
                      value={availabilityForm.service_id}
                      onChange={(e) => setAvailabilityForm({...availabilityForm, service_id: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                      required
                    >
                      <option value="">Select Service</option>
                      {services.map((service) => (
                        <option key={service.id} value={service.id}>{service.name}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Days of Week</label>
                    <div className="grid grid-cols-7 gap-1">
                      {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, index) => (
                        <label key={index} className="flex items-center justify-center">
                          <input
                            type="checkbox"
                            checked={availabilityForm.days_of_week.includes(index)}
                            onChange={(e) => {
                              const days = [...availabilityForm.days_of_week];
                              if (e.target.checked) {
                                days.push(index);
                              } else {
                                const idx = days.indexOf(index);
                                if (idx > -1) days.splice(idx, 1);
                              }
                              setAvailabilityForm({...availabilityForm, days_of_week: days});
                            }}
                            className="sr-only"
                          />
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs cursor-pointer ${
                            availabilityForm.days_of_week.includes(index)
                              ? 'bg-gold text-white'
                              : 'bg-gray-200 text-gray-600'
                          }`}>
                            {day[0]}
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="grid md:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Start Time</label>
                    <input
                      type="time"
                      value={availabilityForm.start_time}
                      onChange={(e) => setAvailabilityForm({...availabilityForm, start_time: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">End Time</label>
                    <input
                      type="time"
                      value={availabilityForm.end_time}
                      onChange={(e) => setAvailabilityForm({...availabilityForm, end_time: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Slot Duration (min)</label>
                    <input
                      type="number"
                      value={availabilityForm.slot_duration}
                      onChange={(e) => setAvailabilityForm({...availabilityForm, slot_duration: parseInt(e.target.value)})}
                      className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                      min="15"
                      max="240"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Buffer Time (min)</label>
                    <input
                      type="number"
                      value={availabilityForm.buffer_time}
                      onChange={(e) => setAvailabilityForm({...availabilityForm, buffer_time: parseInt(e.target.value)})}
                      className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                      min="0"
                      max="60"
                      required
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="bg-gold text-white px-6 py-2 rounded hover:bg-yellow-600 disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Create Availability'}
                </button>
              </form>
            </div>

            {/* Current Availability */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-medium text-charcoal">Current Availability</h2>
                <select
                  value={selectedService}
                  onChange={(e) => setSelectedService(e.target.value)}
                  className="p-2 border border-gray-300 rounded focus:outline-none focus:border-gold"
                >
                  <option value="">Select Service to View</option>
                  {services.map((service) => (
                    <option key={service.id} value={service.id}>{service.name}</option>
                  ))}
                </select>
              </div>

              {selectedService && availability.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No availability settings found for this service</p>
              ) : selectedService && availability.length > 0 ? (
                <div className="grid gap-4">
                  {availability.map((avail) => (
                    <div key={avail._id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="font-medium text-charcoal">{getDayName(avail.day_of_week)}</h4>
                          <p className="text-sm text-gray-600">
                            {formatTime(avail.start_time)} - {formatTime(avail.end_time)}
                          </p>
                          <p className="text-xs text-gray-500 mt-1">
                            {avail.slot_duration}min slots, {avail.buffer_time}min buffer
                          </p>
                        </div>
                        <span className={`px-2 py-1 text-xs rounded ${
                          avail.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                        }`}>
                          {avail.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">Select a service to view availability settings</p>
              )}
            </div>
          </div>
        )}

        {/* Slot Management Tab */}
        {activeTab === 'slots' && (
          <div className="space-y-6">
            {/* Generate Slots Form */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-medium text-charcoal mb-4">Generate Appointment Slots</h2>
              
              <form onSubmit={generateSlots} className="space-y-4">
                <div className="grid md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Service</label>
                    <select
                      value={slotGenerationForm.service_id}
                      onChange={(e) => setSlotGenerationForm({...slotGenerationForm, service_id: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                      required
                    >
                      <option value="">Select Service</option>
                      {services.map((service) => (
                        <option key={service.id} value={service.id}>{service.name}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
                    <input
                      type="date"
                      value={slotGenerationForm.start_date}
                      onChange={(e) => setSlotGenerationForm({...slotGenerationForm, start_date: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
                    <input
                      type="date"
                      value={slotGenerationForm.end_date}
                      onChange={(e) => setSlotGenerationForm({...slotGenerationForm, end_date: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                      required
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="bg-gold text-white px-6 py-2 rounded hover:bg-yellow-600 disabled:opacity-50"
                >
                  {loading ? 'Generating...' : 'Generate Slots'}
                </button>
              </form>
            </div>

            {/* Block Slot Form */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-medium text-charcoal mb-4">Block Appointment Slot</h2>
              
              <form onSubmit={blockSlot} className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Service</label>
                    <select
                      value={blockSlotForm.service_id}
                      onChange={(e) => setBlockSlotForm({...blockSlotForm, service_id: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                      required
                    >
                      <option value="">Select Service</option>
                      {services.map((service) => (
                        <option key={service.id} value={service.id}>{service.name}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Date</label>
                    <input
                      type="date"
                      value={blockSlotForm.date}
                      onChange={(e) => setBlockSlotForm({...blockSlotForm, date: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Start Time</label>
                    <input
                      type="time"
                      value={blockSlotForm.start_time}
                      onChange={(e) => setBlockSlotForm({...blockSlotForm, start_time: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">End Time</label>
                    <input
                      type="time"
                      value={blockSlotForm.end_time}
                      onChange={(e) => setBlockSlotForm({...blockSlotForm, end_time: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Reason</label>
                    <select
                      value={blockSlotForm.reason}
                      onChange={(e) => setBlockSlotForm({...blockSlotForm, reason: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                      required
                    >
                      <option value="admin_use">Admin Use</option>
                      <option value="maintenance">Maintenance</option>
                      <option value="reserved_for_patient">Reserved for Patient</option>
                      <option value="other">Other</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Notes</label>
                    <input
                      type="text"
                      value={blockSlotForm.notes}
                      onChange={(e) => setBlockSlotForm({...blockSlotForm, notes: e.target.value})}
                      className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:border-gold"
                      placeholder="Optional notes"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="bg-red-600 text-white px-6 py-2 rounded hover:bg-red-700 disabled:opacity-50"
                >
                  {loading ? 'Blocking...' : 'Block Slot'}
                </button>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminAppointments;