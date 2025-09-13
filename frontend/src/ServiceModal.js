import React, { useState, useEffect } from 'react';

const ServiceModal = ({ service, serviceGroups, onClose, onSave, backendUrl }) => {
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    category: 'regenerative',
    description: '',
    detailed_description: '',
    duration: 60,
    price: 0,
    benefits: [],
    is_active: true,
    group_id: '',
    images: [],
    main_image: '',
    brochure_url: '',
    video_url: ''
  });

  const [newBenefit, setNewBenefit] = useState('');
  const [newImageUrl, setNewImageUrl] = useState('');

  useEffect(() => {
    if (service) {
      setFormData({
        name: service.name || '',
        category: service.category || 'regenerative',
        description: service.description || '',
        detailed_description: service.detailed_description || '',
        duration: service.duration || 60,
        price: service.price || 0,
        benefits: service.benefits || [],
        is_active: service.is_active !== undefined ? service.is_active : true,
        group_id: service.group_id || '',
        images: service.images || [],
        main_image: service.main_image || '',
        brochure_url: service.brochure_url || '',
        video_url: service.video_url || ''
      });
    }
  }, [service]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onSave(formData);
      onClose();
    } catch (error) {
      console.error('Error saving service:', error);
      alert('Failed to save service');
    } finally {
      setLoading(false);
    }
  };

  const addBenefit = () => {
    if (newBenefit.trim()) {
      setFormData({
        ...formData,
        benefits: [...formData.benefits, newBenefit.trim()]
      });
      setNewBenefit('');
    }
  };

  const removeBenefit = (index) => {
    setFormData({
      ...formData,
      benefits: formData.benefits.filter((_, i) => i !== index)
    });
  };

  const addImage = () => {
    if (newImageUrl.trim()) {
      setFormData({
        ...formData,
        images: [...formData.images, newImageUrl.trim()]
      });
      setNewImageUrl('');
    }
  };

  const removeImage = (index) => {
    const updatedImages = formData.images.filter((_, i) => i !== index);
    setFormData({
      ...formData,
      images: updatedImages,
      // If we removed the main image, clear it
      main_image: formData.main_image === formData.images[index] ? '' : formData.main_image
    });
  };

  const setMainImage = (imageUrl) => {
    setFormData({
      ...formData,
      main_image: imageUrl
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-[#222428]">
            {service ? 'Edit Service' : 'Create New Service'}
          </h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Basic Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Service Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:border-[#C8A25A]"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Category
              </label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({...formData, category: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:border-[#C8A25A]"
              >
                <option value="regenerative">Regenerative</option>
                <option value="iv_therapy">IV Therapy</option>
                <option value="aesthetics">Aesthetics</option>
                <option value="skincare">Skincare</option>
                <option value="wellness">Wellness</option>
                <option value="diagnostics">Diagnostics</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Duration (minutes) *
              </label>
              <input
                type="number"
                value={formData.duration}
                onChange={(e) => setFormData({...formData, duration: parseInt(e.target.value)})}
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:border-[#C8A25A]"
                min="1"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Price (USD) *
              </label>
              <input
                type="number"
                value={formData.price}
                onChange={(e) => setFormData({...formData, price: parseFloat(e.target.value)})}
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:border-[#C8A25A]"
                min="0"
                step="0.01"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Treatment Group
              </label>
              <select
                value={formData.group_id}
                onChange={(e) => setFormData({...formData, group_id: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:border-[#C8A25A]"
              >
                <option value="">No group assigned</option>
                {serviceGroups.map((group) => (
                  <option key={group.id} value={group.id}>
                    {group.icon ? `${group.icon} ` : ''}{group.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                className="mr-2"
              />
              <label className="text-sm font-medium text-gray-700">Active Service</label>
            </div>
          </div>

          {/* Descriptions */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Short Description *
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                rows={3}
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:border-[#C8A25A]"
                placeholder="Brief description for service cards and listings"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Detailed Description
              </label>
              <textarea
                value={formData.detailed_description}
                onChange={(e) => setFormData({...formData, detailed_description: e.target.value})}
                rows={5}
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:border-[#C8A25A]"
                placeholder="Comprehensive description shown on service detail pages"
              />
            </div>
          </div>

          {/* Benefits */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Service Benefits
            </label>
            <div className="space-y-2">
              {formData.benefits.map((benefit, index) => (
                <div key={index} className="flex items-center space-x-2 p-2 bg-gray-50 rounded">
                  <span className="text-[#C8A25A]">✓</span>
                  <span className="flex-1">{benefit}</span>
                  <button
                    type="button"
                    onClick={() => removeBenefit(index)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Remove
                  </button>
                </div>
              ))}
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={newBenefit}
                  onChange={(e) => setNewBenefit(e.target.value)}
                  className="flex-1 p-2 border border-gray-300 rounded focus:outline-none focus:border-[#C8A25A]"
                  placeholder="Add a benefit..."
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addBenefit())}
                />
                <button
                  type="button"
                  onClick={addBenefit}
                  className="px-3 py-2 bg-[#C8A25A] text-white rounded hover:bg-[#B8925A]"
                >
                  Add
                </button>
              </div>
            </div>
          </div>

          {/* Images */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Service Images
            </label>
            <div className="space-y-3">
              {formData.images.map((image, index) => (
                <div key={index} className="flex items-center space-x-3 p-3 border border-gray-200 rounded">
                  <img src={image} alt="Service" className="w-16 h-16 object-cover rounded" />
                  <span className="flex-1 text-sm text-gray-600">{image}</span>
                  <div className="flex space-x-2">
                    <button
                      type="button"
                      onClick={() => setMainImage(image)}
                      className={`px-2 py-1 text-xs rounded ${
                        formData.main_image === image
                          ? 'bg-[#C8A25A] text-white'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      {formData.main_image === image ? 'Main' : 'Set Main'}
                    </button>
                    <button
                      type="button"
                      onClick={() => removeImage(index)}
                      className="text-red-600 hover:text-red-800 text-xs"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ))}
              <div className="flex space-x-2">
                <input
                  type="url"
                  value={newImageUrl}
                  onChange={(e) => setNewImageUrl(e.target.value)}
                  className="flex-1 p-2 border border-gray-300 rounded focus:outline-none focus:border-[#C8A25A]"
                  placeholder="Image URL..."
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addImage())}
                />
                <button
                  type="button"
                  onClick={addImage}
                  className="px-3 py-2 bg-[#C8A25A] text-white rounded hover:bg-[#B8925A]"
                >
                  Add Image
                </button>
              </div>
            </div>
          </div>

          {/* Additional Media */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Brochure URL
              </label>
              <input
                type="url"
                value={formData.brochure_url}
                onChange={(e) => setFormData({...formData, brochure_url: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:border-[#C8A25A]"
                placeholder="https://..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Demo Video URL
              </label>
              <input
                type="url"
                value={formData.video_url}
                onChange={(e) => setFormData({...formData, video_url: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:border-[#C8A25A]"
                placeholder="https://..."
              />
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-6 py-2 text-gray-600 hover:text-gray-800 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-[#C8A25A] text-white rounded-lg hover:bg-[#B8925A] disabled:opacity-50"
            >
              {loading ? 'Saving...' : (service ? 'Update Service' : 'Create Service')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ServiceModal;