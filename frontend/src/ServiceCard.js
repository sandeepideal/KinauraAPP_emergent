import React, { useState } from 'react';

const ServiceCard = ({ service, serviceGroups, onEdit, onDelete, onAssignGroup, backendUrl }) => {
  const [assigningGroup, setAssigningGroup] = useState(false);

  const formatPrice = (price) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(price);
  };

  const getServiceGroup = () => {
    if (service.group_id) {
      return serviceGroups.find(group => group.id === service.group_id);
    }
    return null;
  };

  const serviceGroup = getServiceGroup();

  const handleGroupAssignment = async (e) => {
    const groupId = e.target.value || null;
    setAssigningGroup(true);
    try {
      await onAssignGroup(service.id, groupId);
    } catch (error) {
      console.error('Error assigning group:', error);
      alert('Failed to assign group');
    } finally {
      setAssigningGroup(false);
    }
  };

  const handleDelete = () => {
    if (confirm(`Are you sure you want to delete the service "${service.name}"? This action cannot be undone.`)) {
      onDelete(service.id);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden border border-gray-200 hover:shadow-lg transition-shadow">
      {/* Service Image */}
      {service.main_image && (
        <img 
          src={service.main_image} 
          alt={service.name}
          className="w-full h-48 object-cover"
        />
      )}

      <div className="p-6">
        {/* Service Header */}
        <div className="flex justify-between items-start mb-3">
          <h3 className="text-xl font-semibold text-[#222428] flex-1">{service.name}</h3>
          <div className="flex space-x-2 ml-2">
            <button
              onClick={() => onEdit(service)}
              className="text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              Edit
            </button>
            <button
              onClick={handleDelete}
              className="text-red-600 hover:text-red-800 text-sm font-medium"
            >
              Delete
            </button>
          </div>
        </div>

        {/* Service Details */}
        <p className="text-gray-600 mb-4 line-clamp-3">{service.description}</p>

        {/* Service Info */}
        <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
          <span>⏱️ {service.duration} min</span>
          <span className="text-lg font-semibold text-[#C8A25A]">{formatPrice(service.price)}</span>
        </div>

        {/* Category */}
        <div className="mb-4">
          <span className="inline-block bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm">
            {service.category}
          </span>
        </div>

        {/* Current Group */}
        {serviceGroup && (
          <div className="mb-4 p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-2">
              {serviceGroup.icon && <span className="text-lg">{serviceGroup.icon}</span>}
              <span className="text-sm font-medium text-gray-700">{serviceGroup.name}</span>
            </div>
          </div>
        )}

        {/* Group Assignment */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            Treatment Group
          </label>
          <select
            value={service.group_id || ''}
            onChange={handleGroupAssignment}
            disabled={assigningGroup}
            className="w-full p-2 border border-gray-300 rounded text-sm disabled:opacity-50"
          >
            <option value="">No group assigned</option>
            {serviceGroups.map((group) => (
              <option key={group.id} value={group.id}>
                {group.icon ? `${group.icon} ` : ''}{group.name}
              </option>
            ))}
          </select>
          {assigningGroup && (
            <p className="text-xs text-gray-500">Updating group assignment...</p>
          )}
        </div>

        {/* Media Count */}
        <div className="mt-4 flex items-center justify-between text-xs text-gray-500">
          <div className="flex space-x-4">
            {service.images && service.images.length > 0 && (
              <span>📷 {service.images.length} images</span>
            )}
            {service.brochure_url && <span>📄 Brochure</span>}
            {service.video_url && <span>🎥 Video</span>}
          </div>
          <span className={`px-2 py-1 rounded-full text-xs ${
            service.is_active 
              ? 'bg-green-100 text-green-800' 
              : 'bg-red-100 text-red-800'
          }`}>
            {service.is_active ? 'Active' : 'Inactive'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ServiceCard;