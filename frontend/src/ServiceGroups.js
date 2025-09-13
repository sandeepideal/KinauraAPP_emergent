import React, { useState, useEffect } from 'react';

const ServiceGroups = ({ onNavigate, backendUrl }) => {
  const [groups, setGroups] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [selectedService, setSelectedService] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchServiceGroups();
  }, []);

  const fetchServiceGroups = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${backendUrl}/service-groups`);
      
      if (response.ok) {
        const data = await response.json();
        setGroups(data.service_groups || []);
      }
    } catch (error) {
      console.error('Error fetching service groups:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBookService = (service) => {
    // Navigate to appointment booking with pre-selected service
    onNavigate('appointment-booking', { serviceId: service.id });
  };

  const formatPrice = (price) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(price);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#C8A25A]"></div>
      </div>
    );
  }

  // Show service details modal
  if (selectedService) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          {/* Service Header */}
          <div className="relative">
            {selectedService.main_image && (
              <img 
                src={selectedService.main_image} 
                alt={selectedService.name}
                className="w-full h-64 object-cover"
              />
            )}
            <div className="absolute top-4 left-4">
              <button
                onClick={() => setSelectedService(null)}
                className="bg-white bg-opacity-90 text-gray-700 p-2 rounded-full hover:bg-opacity-100 transition-colors"
              >
                ← Back
              </button>
            </div>
          </div>

          <div className="p-8">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h1 className="text-3xl font-bold text-[#222428] mb-2">{selectedService.name}</h1>
                <p className="text-lg text-gray-600 mb-4">{selectedService.description}</p>
                <div className="flex items-center space-x-4 text-sm text-gray-500">
                  <span>⏱️ {selectedService.duration} minutes</span>
                  <span>💰 {formatPrice(selectedService.price)}</span>
                </div>
              </div>
            </div>

            {/* Detailed Description */}
            <div className="mb-8">
              <h2 className="text-xl font-semibold text-[#222428] mb-4">About This Treatment</h2>
              <p className="text-gray-700 leading-relaxed">{selectedService.detailed_description}</p>
            </div>

            {/* Benefits */}
            {selectedService.benefits && selectedService.benefits.length > 0 && (
              <div className="mb-8">
                <h2 className="text-xl font-semibold text-[#222428] mb-4">Benefits</h2>
                <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {selectedService.benefits.map((benefit, index) => (
                    <li key={index} className="flex items-center space-x-3">
                      <span className="text-[#C8A25A]">✓</span>
                      <span className="text-gray-700">{benefit}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Image Gallery */}
            {selectedService.images && selectedService.images.length > 0 && (
              <div className="mb-8">
                <h2 className="text-xl font-semibold text-[#222428] mb-4">Gallery</h2>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {selectedService.images.map((image, index) => (
                    <img 
                      key={index}
                      src={image} 
                      alt={`${selectedService.name} ${index + 1}`}
                      className="w-full h-32 object-cover rounded-lg"
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Additional Resources */}
            <div className="flex flex-wrap gap-4 mb-8">
              {selectedService.brochure_url && (
                <a 
                  href={selectedService.brochure_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center space-x-2 text-[#C8A25A] hover:text-[#B8925A]"
                >
                  <span>📄</span>
                  <span>Download Brochure</span>
                </a>
              )}
              {selectedService.video_url && (
                <a 
                  href={selectedService.video_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center space-x-2 text-[#C8A25A] hover:text-[#B8925A]"
                >
                  <span>🎥</span>
                  <span>Watch Video</span>
                </a>
              )}
            </div>

            {/* Book Button */}
            <div className="flex justify-center">
              <button
                onClick={() => handleBookService(selectedService)}
                className="bg-[#C8A25A] text-white px-8 py-3 rounded-lg text-lg font-medium hover:bg-[#B8925A] transition-colors"
              >
                Book This Treatment - {formatPrice(selectedService.price)}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show services in selected group
  if (selectedGroup) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="mb-8">
          <button
            onClick={() => setSelectedGroup(null)}
            className="text-[#C8A25A] hover:text-[#B8925A] mb-4"
          >
            ← Back to All Categories
          </button>
          <div className="flex items-center space-x-4 mb-2">
            {selectedGroup.icon && <span className="text-3xl">{selectedGroup.icon}</span>}
            <h1 className="text-3xl font-bold text-[#222428]">{selectedGroup.name}</h1>
          </div>
          <p className="text-gray-600 text-lg">{selectedGroup.description}</p>
          <p className="text-sm text-gray-500 mt-2">{selectedGroup.service_count} treatments available</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {selectedGroup.services.map((service) => (
            <div key={service.id} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
              {service.main_image && (
                <img 
                  src={service.main_image} 
                  alt={service.name}
                  className="w-full h-48 object-cover"
                />
              )}
              <div className="p-6">
                <h3 className="text-xl font-semibold text-[#222428] mb-3">{service.name}</h3>
                <p className="text-gray-600 mb-4 line-clamp-3">{service.description}</p>
                
                <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                  <span>⏱️ {service.duration} min</span>
                  <span className="text-lg font-semibold text-[#C8A25A]">{formatPrice(service.price)}</span>
                </div>

                <div className="flex space-x-2">
                  <button
                    onClick={() => setSelectedService(service)}
                    className="flex-1 border border-[#C8A25A] text-[#C8A25A] px-4 py-2 rounded hover:bg-[#C8A25A] hover:text-white transition-colors"
                  >
                    Learn More
                  </button>
                  <button
                    onClick={() => handleBookService(service)}
                    className="flex-1 bg-[#C8A25A] text-white px-4 py-2 rounded hover:bg-[#B8925A] transition-colors"
                  >
                    Book Now
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Show all service groups (main view)
  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header with Navigation */}
      <div className="flex items-center justify-between mb-8">
        <button
          onClick={() => onNavigate('dashboard')}
          className="flex items-center space-x-2 text-[#C8A25A] hover:text-[#B8925A] transition-colors"
          aria-label="Back to dashboard"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span className="font-medium">Back to Dashboard</span>
        </button>
        <button
          onClick={() => onNavigate('menu')}
          className="hamburger-menu"
          aria-label="Main menu"
        >
          <div className="hamburger-line"></div>
          <div className="hamburger-line"></div>
          <div className="hamburger-line"></div>
        </button>
      </div>
      
      <div className="mb-8 text-center">
        <h1 className="text-4xl font-bold text-[#222428] mb-4">Our Treatment Categories</h1>
        <p className="text-xl text-gray-600">Discover our comprehensive range of regenerative and wellness treatments</p>
      </div>

      {groups.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg mb-4">No treatment categories available at the moment</p>
          <button
            onClick={() => onNavigate('services')}
            className="text-[#C8A25A] hover:text-[#B8925A]"
          >
            View individual services instead
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {groups.map((group) => (
            <div 
              key={group.id} 
              className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-all duration-300 cursor-pointer group"
              onClick={() => setSelectedGroup(group)}
              style={{
                borderTop: group.color_theme ? `4px solid ${group.color_theme}` : '4px solid #C8A25A'
              }}
            >
              <div className="p-8 text-center">
                {group.icon && (
                  <div className="text-6xl mb-4 group-hover:scale-110 transition-transform">
                    {group.icon}
                  </div>
                )}
                <h2 className="text-2xl font-bold text-[#222428] mb-4">{group.name}</h2>
                <p className="text-gray-600 mb-6 leading-relaxed">{group.description}</p>
                
                <div className="flex items-center justify-center space-x-4 text-sm text-gray-500 mb-6">
                  <span>{group.service_count} treatments</span>
                </div>

                <div 
                  className="inline-flex items-center space-x-2 px-6 py-3 rounded-full text-white font-medium group-hover:shadow-lg transition-all"
                  style={{
                    backgroundColor: group.color_theme || '#C8A25A'
                  }}
                >
                  <span>Explore Treatments</span>
                  <span>→</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Call to Action */}
      <div className="mt-16 text-center bg-gray-50 rounded-lg p-8">
        <h2 className="text-2xl font-bold text-[#222428] mb-4">Not Sure Which Treatment Is Right for You?</h2>
        <p className="text-gray-600 mb-6">Our expert team can help you choose the perfect treatment plan based on your goals and needs.</p>
        <button
          onClick={() => onNavigate('concierge')}
          className="bg-[#C8A25A] text-white px-8 py-3 rounded-lg font-medium hover:bg-[#B8925A] transition-colors"
        >
          Speak with Our Concierge
        </button>
      </div>
    </div>
  );
};

export default ServiceGroups;