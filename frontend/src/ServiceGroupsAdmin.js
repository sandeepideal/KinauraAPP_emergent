import React, { useState, useEffect } from 'react';

const ServiceGroupsAdmin = ({ backendUrl }) => {
  const [groups, setGroups] = useState([]);
  const [services, setServices] = useState([]);
  const [ungroupedServices, setUngroupedServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingGroup, setEditingGroup] = useState(null);
  const [selectedServices, setSelectedServices] = useState({});

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    icon: '',
    display_order: 0,
    color_theme: '#C8A25A',
    is_active: true
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // Fetch service groups
      const groupsResponse = await fetch(`${backendUrl}/admin/service-groups`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (groupsResponse.ok) {
        const groupsData = await groupsResponse.json();
        setGroups(groupsData.service_groups || []);
      }

      // Fetch all services
      const servicesResponse = await fetch(`${backendUrl}/admin/services`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (servicesResponse.ok) {
        const servicesData = await servicesResponse.json();
        setServices(servicesData.services || []);
      }

      // Fetch ungrouped services
      const ungroupedResponse = await fetch(`${backendUrl}/services/ungrouped`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (ungroupedResponse.ok) {
        const ungroupedData = await ungroupedResponse.json();
        setUngroupedServices(ungroupedData.services || []);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateGroup = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/admin/service-groups`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        setShowCreateModal(false);
        setFormData({
          name: '',
          description: '',
          icon: '',
          display_order: 0,
          color_theme: '#C8A25A',
          is_active: true
        });
        await fetchData();
      } else {
        const error = await response.json();
        alert(`Failed to create group: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error creating group:', error);
      alert('Error creating group');
    }
  };

  const handleUpdateGroup = async (groupId, updatedData) => {
    try {
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/admin/service-groups/${groupId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(updatedData)
      });

      if (response.ok) {
        await fetchData();
      } else {
        const error = await response.json();
        alert(`Failed to update group: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error updating group:', error);
      alert('Error updating group');
    }
  };

  const handleDeleteGroup = async (groupId) => {
    if (!confirm('Are you sure you want to delete this service group?')) return;
    
    try {
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/admin/service-groups/${groupId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        await fetchData();
      } else {
        const error = await response.json();
        alert(`Failed to delete group: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error deleting group:', error);
      alert('Error deleting group');
    }
  };

  const handleAssignServiceToGroup = async (serviceId, groupId) => {
    try {
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/admin/services/${serviceId}/group`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ group_id: groupId })
      });

      if (response.ok) {
        await fetchData();
      } else {
        const error = await response.json();
        alert(`Failed to assign service: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error assigning service:', error);
      alert('Error assigning service');
    }
  };

  const getServicesForGroup = (groupId) => {
    return services.filter(service => service.group_id === groupId);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#C8A25A]"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-[#222428] mb-2">Service Groups Management</h1>
            <p className="text-gray-600">Organize services into categories for better patient experience</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-[#C8A25A] text-white px-6 py-2 rounded-lg hover:bg-[#B8925A] transition-colors"
          >
            + Create Group
          </button>
        </div>
      </div>

      {/* Service Groups List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {groups.map((group) => {
          const groupServices = getServicesForGroup(group.id);
          return (
            <div key={group.id} className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  {group.icon && <span className="text-2xl">{group.icon}</span>}
                  <div>
                    <h3 className="text-xl font-semibold text-[#222428]">{group.name}</h3>
                    <p className="text-sm text-gray-500">{group.service_count || 0} services</p>
                  </div>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setEditingGroup(group)}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDeleteGroup(group.id)}
                    className="text-red-600 hover:text-red-800"
                  >
                    Delete
                  </button>
                </div>
              </div>
              
              <p className="text-gray-600 mb-4">{group.description}</p>
              
              {group.color_theme && (
                <div className="flex items-center space-x-2 mb-4">
                  <span className="text-sm text-gray-500">Theme Color:</span>
                  <div 
                    className="w-6 h-6 rounded-full border"
                    style={{ backgroundColor: group.color_theme }}
                  ></div>
                </div>
              )}

              {/* Services in this group */}
              <div className="space-y-2">
                <h4 className="font-medium text-[#222428]">Services in this group:</h4>
                {groupServices.length === 0 ? (
                  <p className="text-gray-500 text-sm">No services assigned</p>
                ) : (
                  <div className="max-h-32 overflow-y-auto">
                    {groupServices.map((service) => (
                      <div key={service.id} className="flex items-center justify-between text-sm bg-gray-50 p-2 rounded">
                        <span>{service.name}</span>
                        <button
                          onClick={() => handleAssignServiceToGroup(service.id, null)}
                          className="text-red-600 hover:text-red-800 text-xs"
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Ungrouped Services */}
      {ungroupedServices.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-[#222428] mb-4">
            Ungrouped Services ({ungroupedServices.length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {ungroupedServices.map((service) => (
              <div key={service.id} className="border border-gray-200 rounded-lg p-4">
                <h3 className="font-medium text-[#222428] mb-2">{service.name}</h3>
                <p className="text-sm text-gray-600 mb-3">{service.description}</p>
                <select
                  onChange={(e) => {
                    if (e.target.value) {
                      handleAssignServiceToGroup(service.id, e.target.value);
                    }
                  }}
                  defaultValue=""
                  className="w-full p-2 border border-gray-300 rounded text-sm"
                >
                  <option value="">Assign to group...</option>
                  {groups.map((group) => (
                    <option key={group.id} value={group.id}>
                      {group.name}
                    </option>
                  ))}
                </select>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Create/Edit Group Modal */}
      {(showCreateModal || editingGroup) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-[#222428] mb-4">
              {editingGroup ? 'Edit Service Group' : 'Create Service Group'}
            </h3>
            
            <form onSubmit={editingGroup ? 
              (e) => {
                e.preventDefault();
                handleUpdateGroup(editingGroup.id, formData);
                setEditingGroup(null);
              } : 
              handleCreateGroup
            }>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Group Name
                  </label>
                  <input
                    type="text"
                    value={editingGroup ? (formData.name || editingGroup.name) : formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={editingGroup ? (formData.description || editingGroup.description) : formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded h-20"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Icon (emoji or text)
                  </label>
                  <input
                    type="text"
                    value={editingGroup ? (formData.icon || editingGroup.icon || '') : formData.icon}
                    onChange={(e) => setFormData({...formData, icon: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded"
                    placeholder="🏥"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Display Order
                  </label>
                  <input
                    type="number"
                    value={editingGroup ? (formData.display_order || editingGroup.display_order) : formData.display_order}
                    onChange={(e) => setFormData({...formData, display_order: parseInt(e.target.value)})}
                    className="w-full p-2 border border-gray-300 rounded"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Theme Color
                  </label>
                  <input
                    type="color"
                    value={editingGroup ? (formData.color_theme || editingGroup.color_theme || '#C8A25A') : formData.color_theme}
                    onChange={(e) => setFormData({...formData, color_theme: e.target.value})}
                    className="w-full p-1 border border-gray-300 rounded h-10"
                  />
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={editingGroup ? (formData.is_active !== undefined ? formData.is_active : editingGroup.is_active) : formData.is_active}
                    onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                    className="mr-2"
                  />
                  <label className="text-sm font-medium text-gray-700">Active</label>
                </div>
              </div>

              <div className="mt-6 flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setEditingGroup(null);
                    setFormData({
                      name: '',
                      description: '',
                      icon: '',
                      display_order: 0,
                      color_theme: '#C8A25A',
                      is_active: true
                    });
                  }}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-[#C8A25A] text-white rounded hover:bg-[#B8925A]"
                >
                  {editingGroup ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ServiceGroupsAdmin;