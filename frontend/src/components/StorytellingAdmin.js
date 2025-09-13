import React, { useState, useEffect } from 'react';

const StorytellingAdmin = ({ backendUrl }) => {
  const [activeSubTab, setActiveSubTab] = useState('backgrounds');
  const [backgroundSettings, setBackgroundSettings] = useState({
    enabled: true,
    intensity: 2,
    palette: 'gold600',
    scope: 'global'
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  // Load background settings on component mount
  useEffect(() => {
    loadBackgroundSettings();
  }, []);

  const loadBackgroundSettings = async () => {
    try {
      // For now, use localStorage as backend endpoint doesn't exist yet
      const saved = localStorage.getItem('kinaura_storytelling_backgrounds');
      if (saved) {
        setBackgroundSettings(JSON.parse(saved));
      }
    } catch (error) {
      console.error('Error loading background settings:', error);
    }
  };

  const saveBackgroundSettings = async () => {
    try {
      setLoading(true);
      
      // For now, save to localStorage - will be replaced with API call later
      localStorage.setItem('kinaura_storytelling_backgrounds', JSON.stringify(backgroundSettings));
      
      // Trigger background update via custom event
      window.dispatchEvent(new CustomEvent('kinaura-bg-update', {
        detail: backgroundSettings
      }));
      
      setMessage('Background settings saved successfully!');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Error saving background settings:', error);
      setMessage('Error saving settings. Please try again.');
      setTimeout(() => setMessage(''), 3000);
    } finally {
      setLoading(false);
    }
  };

  const handleSettingChange = (key, value) => {
    setBackgroundSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const subTabs = [
    { id: 'backgrounds', name: 'Backgrounds', icon: '✨' },
    { id: 'videos', name: 'Journey Videos', icon: '🎬', disabled: true },
    { id: 'gallery', name: 'Before & After', icon: '📸', disabled: true },
    { id: 'copy', name: 'Copy Library', icon: '📝', disabled: true }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Storytelling</h2>
        <p className="text-gray-600">
          Manage immersive visual experiences across the KinAura app.
        </p>
      </div>

      {/* Sub-navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {subTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => !tab.disabled && setActiveSubTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeSubTab === tab.id
                  ? 'border-[#C8A25A] text-[#C8A25A]'
                  : tab.disabled
                  ? 'border-transparent text-gray-300 cursor-not-allowed'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } transition-colors duration-200`}
              disabled={tab.disabled}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.name}
              {tab.disabled && (
                <span className="ml-2 text-xs bg-gray-100 text-gray-500 px-2 py-1 rounded">
                  Phase 2+
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Status Message */}
      {message && (
        <div className={`p-4 rounded-lg ${
          message.includes('Error') ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-green-50 text-green-700 border border-green-200'
        }`}>
          {message}
        </div>
      )}

      {/* Backgrounds Tab */}
      {activeSubTab === 'backgrounds' && (
        <div className="space-y-6">
          <div className="ka-card p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Animated Background Settings
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Enable/Disable */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Animation Status
                </label>
                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => handleSettingChange('enabled', !backgroundSettings.enabled)}
                    className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-[#C8A25A] focus:ring-offset-2 ${
                      backgroundSettings.enabled ? 'bg-[#C8A25A]' : 'bg-gray-200'
                    }`}
                  >
                    <span
                      className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                        backgroundSettings.enabled ? 'translate-x-5' : 'translate-x-0'
                      }`}
                    />
                  </button>
                  <span className="text-sm text-gray-600">
                    {backgroundSettings.enabled ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
              </div>

              {/* Intensity */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Animation Intensity
                </label>
                <select
                  value={backgroundSettings.intensity}
                  onChange={(e) => handleSettingChange('intensity', parseInt(e.target.value))}
                  className="ka-input w-full"
                  disabled={!backgroundSettings.enabled}
                >
                  <option value={0}>0 - Static (No Animation)</option>
                  <option value={1}>1 - Subtle</option>
                  <option value={2}>2 - Moderate</option>
                  <option value={3}>3 - Enhanced</option>
                </select>
              </div>

              {/* Palette */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Color Palette
                </label>
                <select
                  value={backgroundSettings.palette}
                  onChange={(e) => handleSettingChange('palette', e.target.value)}
                  className="ka-input w-full"
                  disabled={!backgroundSettings.enabled}
                >
                  <option value="gold500">Gold 500 (Lighter)</option>
                  <option value="gold600">Gold 600 (Standard)</option>
                </select>
              </div>

              {/* Scope */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Display Scope
                </label>
                <select
                  value={backgroundSettings.scope}
                  onChange={(e) => handleSettingChange('scope', e.target.value)}
                  className="ka-input w-full"
                  disabled={!backgroundSettings.enabled}
                >
                  <option value="global">Global (All Pages)</option>
                  <option value="heroOnly">Hero Sections Only</option>
                </select>
              </div>
            </div>

            {/* Preview Information */}
            <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
              <h4 className="text-sm font-medium text-amber-800 mb-2">Preview Settings</h4>
              <div className="text-sm text-amber-700 space-y-1">
                <p><span className="font-medium">Status:</span> {backgroundSettings.enabled ? 'Active' : 'Inactive'}</p>
                <p><span className="font-medium">Intensity:</span> Level {backgroundSettings.intensity}</p>
                <p><span className="font-medium">Palette:</span> {backgroundSettings.palette}</p>
                <p><span className="font-medium">Scope:</span> {backgroundSettings.scope === 'global' ? 'All pages' : 'Hero sections only'}</p>
              </div>
            </div>

            {/* Save Button */}
            <div className="mt-6 flex justify-end">
              <button
                onClick={saveBackgroundSettings}
                disabled={loading}
                className="ka-button-primary px-6 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Saving...' : 'Save Settings'}
              </button>
            </div>
          </div>

          {/* Technical Information */}
          <div className="ka-card p-6 bg-gray-50">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Technical Information
            </h3>
            <div className="text-sm text-gray-600 space-y-2">
              <p><span className="font-medium">Animation Type:</span> CSS-based kintsugi pulse animation</p>
              <p><span className="font-medium">Performance:</span> GPU-accelerated, optimized for mobile</p>
              <p><span className="font-medium">Accessibility:</span> Automatically disabled for users with reduced motion preferences</p>
              <p><span className="font-medium">Fallback:</span> Static background for unsupported browsers</p>
              <p><span className="font-medium">Background Color:</span> Ivory (#FAFAF7)</p>
              <p><span className="font-medium">Animation Duration:</span> 14-second breathing loop</p>
            </div>
          </div>
        </div>
      )}

      {/* Placeholder for other tabs */}
      {activeSubTab !== 'backgrounds' && (
        <div className="ka-card p-12 text-center">
          <div className="text-4xl mb-4">🚧</div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">Coming Soon</h3>
          <p className="text-gray-600">
            This feature will be available in Phase 2+ of the storytelling implementation.
          </p>
        </div>
      )}
    </div>
  );
};

export default StorytellingAdmin;