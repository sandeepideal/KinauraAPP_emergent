import React, { useState, useEffect } from 'react';

const BoutiqueAdmin = ({ backendUrl }) => {
  const [activeTab, setActiveTab] = useState('products');
  const [products, setProducts] = useState([]);
  const [collections, setCollections] = useState([]);
  const [crossSellRules, setCrossSellRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showProductModal, setShowProductModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);

  const API = `${backendUrl}/api`;

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const axios = (await import('axios')).default;

      const headers = { 'Authorization': `Bearer ${token}` };

      if (activeTab === 'products') {
        const response = await axios.get(`${API}/admin/shop/products`, { headers });
        if (response.data.success) {
          setProducts(response.data.products);
        }
      } else if (activeTab === 'collections') {
        const response = await axios.get(`${API}/admin/shop/collections`, { headers });
        if (response.data.success) {
          setCollections(response.data.collections);
        }
      } else if (activeTab === 'cross-sell') {
        const response = await axios.get(`${API}/admin/shop/cross-sell-rules`, { headers });
        if (response.data.success) {
          setCrossSellRules(response.data.rules);
        }
      }
    } catch (err) {
      console.error('Error loading data:', err);
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProduct = () => {
    setEditingProduct(null);
    setShowProductModal(true);
  };

  const handleEditProduct = (product) => {
    setEditingProduct(product);
    setShowProductModal(true);
  };

  const handleSaveProduct = async (productData) => {
    try {
      const token = localStorage.getItem('token');
      const axios = (await import('axios')).default;
      const headers = { 'Authorization': `Bearer ${token}` };

      if (editingProduct) {
        // Update existing product
        await axios.put(`${API}/admin/shop/products/${editingProduct.sku}`, productData, { headers });
      } else {
        // Create new product
        await axios.post(`${API}/admin/shop/products`, productData, { headers });
      }

      setShowProductModal(false);
      loadData();
    } catch (err) {
      console.error('Error saving product:', err);
      alert('Failed to save product');
    }
  };

  const tabs = [
    { id: 'products', name: 'Products', icon: '📦' },
    { id: 'collections', name: 'Collections', icon: '📚' },
    { id: 'cross-sell', name: 'Cross-sell Rules', icon: '🎯' },
    { id: 'analytics', name: 'Analytics', icon: '📊' }
  ];

  return (
    <div className="min-h-screen bg-cream">
      {/* Header */}
      <div className="bg-gradient-to-r from-[#C8A25A] to-[#E6C78A] text-white p-6">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-3xl font-bold mb-2">Boutique Management</h1>
          <p className="text-white text-opacity-90">
            Manage products, collections, and cross-sell strategies
          </p>
        </div>
      </div>

      <div className="max-w-6xl mx-auto p-6">
        {/* Tab Navigation */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-[#C8A25A] text-[#C8A25A]'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'products' && (
          <ProductsTab
            products={products}
            loading={loading}
            onCreateProduct={handleCreateProduct}
            onEditProduct={handleEditProduct}
          />
        )}

        {activeTab === 'collections' && (
          <CollectionsTab
            collections={collections}
            loading={loading}
          />
        )}

        {activeTab === 'cross-sell' && (
          <CrossSellTab
            rules={crossSellRules}
            loading={loading}
          />
        )}

        {activeTab === 'analytics' && (
          <AnalyticsTab />
        )}
      </div>

      {/* Product Modal */}
      {showProductModal && (
        <ProductModal
          product={editingProduct}
          onSave={handleSaveProduct}
          onClose={() => setShowProductModal(false)}
        />
      )}
    </div>
  );
};

// Products Tab Component
const ProductsTab = ({ products, loading, onCreateProduct, onEditProduct }) => {
  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="ka-card p-4 animate-pulse">
            <div className="flex items-center space-x-4">
              <div className="w-16 h-16 bg-gray-200 rounded"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-200 rounded w-1/3"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div>
      {/* Header with Create Button */}
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Products ({products.length})</h2>
        <button
          onClick={onCreateProduct}
          className="ka-button-primary flex items-center space-x-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          <span>Create Product</span>
        </button>
      </div>

      {/* Products Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {products.map((product) => (
          <div key={product.sku} className="ka-card hover:shadow-lg transition-shadow">
            <div className="aspect-square bg-gray-100 rounded-lg mb-4 overflow-hidden">
              {product.images && product.images.length > 0 ? (
                <img
                  src={product.images[0].url}
                  alt={product.name.en}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-400 text-4xl">
                  📦
                </div>
              )}
            </div>

            <div className="space-y-3">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-gray-900 line-clamp-1">
                    {product.name.en}
                  </h3>
                  {product.badge && (
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                      {product.badge}
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-600">SKU: {product.sku}</p>
                <p className="text-sm text-gray-600">Category: {product.category}</p>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <span className="text-lg font-bold text-[#C8A25A]">€{product.price_eur}</span>
                  <span className="text-sm text-gray-500 ml-2">Stock: {product.inventory}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 rounded-full text-xs ${
                    product.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {product.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>

              <button
                onClick={() => onEditProduct(product)}
                className="w-full ka-button-secondary py-2 text-sm"
              >
                Edit Product
              </button>
            </div>
          </div>
        ))}
      </div>

      {products.length === 0 && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">📦</div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No products yet</h3>
          <p className="text-gray-600 mb-4">Create your first product to get started</p>
          <button onClick={onCreateProduct} className="ka-button-primary">
            Create Product
          </button>
        </div>
      )}
    </div>
  );
};

// Collections Tab Component  
const CollectionsTab = ({ collections, loading }) => {
  if (loading) {
    return <div className="text-center py-8">Loading collections...</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Collections ({collections.length})</h2>
        <button className="ka-button-primary">Create Collection</button>
      </div>

      <div className="space-y-4">
        {collections.map((collection) => (
          <div key={collection.id} className="ka-card p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {collection.name.en}
                </h3>
                <p className="text-gray-600 mb-2">
                  {collection.description.en}
                </p>
                <p className="text-sm text-gray-500">
                  {collection.products.length} products • Order: {collection.ordering}
                </p>
              </div>
              <div className="flex items-center space-x-4">
                <span className={`px-3 py-1 rounded-full text-sm ${
                  collection.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {collection.is_active ? 'Active' : 'Inactive'}
                </span>
                <button className="ka-button-secondary">Edit</button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {collections.length === 0 && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">📚</div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No collections yet</h3>
          <p className="text-gray-600">Create curated product collections</p>
        </div>
      )}
    </div>
  );
};

// Cross-sell Tab Component
const CrossSellTab = ({ rules, loading }) => {
  if (loading) {
    return <div className="text-center py-8">Loading cross-sell rules...</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Cross-sell Rules ({rules.length})</h2>
        <button className="ka-button-primary">Create Rule</button>
      </div>

      <div className="space-y-4">
        {rules.map((rule) => (
          <div key={rule.id} className="ka-card p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Protocol: {rule.protocol_id}
                </h3>
                <p className="text-gray-600 mb-2">
                  Products: {rule.product_skus.join(', ')}
                </p>
                <p className="text-sm text-gray-500">
                  Priority: {rule.priority} • {rule.is_active ? 'Active' : 'Inactive'}
                </p>
              </div>
              <button className="ka-button-secondary">Edit</button>
            </div>
          </div>
        ))}
      </div>

      {rules.length === 0 && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🎯</div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No cross-sell rules yet</h3>
          <p className="text-gray-600">Create rules to suggest products based on protocols</p>
        </div>
      )}
    </div>
  );
};

// Analytics Tab Component
const AnalyticsTab = () => {
  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 mb-6">Boutique Analytics</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="ka-card p-6 text-center">
          <div className="text-3xl font-bold text-[#C8A25A] mb-2">€12,450</div>
          <div className="text-sm text-gray-600">Revenue (30d)</div>
        </div>
        <div className="ka-card p-6 text-center">
          <div className="text-3xl font-bold text-green-600 mb-2">127</div>
          <div className="text-sm text-gray-600">Orders (30d)</div>
        </div>
        <div className="ka-card p-6 text-center">
          <div className="text-3xl font-bold text-blue-600 mb-2">€98</div>
          <div className="text-sm text-gray-600">Avg Order Value</div>
        </div>
        <div className="ka-card p-6 text-center">
          <div className="text-3xl font-bold text-purple-600 mb-2">3.2%</div>
          <div className="text-sm text-gray-600">Conversion Rate</div>
        </div>
      </div>

      <div className="ka-card p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Products</h3>
        <div className="space-y-3">
          {[
            { name: 'KinAura Illuminating Cream', sales: 45, revenue: '€8,100' },
            { name: 'NAD+ Longevity Blend', sales: 32, revenue: '€4,800' },
            { name: 'Collagen Boost Complex', sales: 28, revenue: '€2,240' }
          ].map((product, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="font-medium">{product.name}</span>
              <div className="text-right">
                <div className="font-semibold text-[#C8A25A]">{product.revenue}</div>
                <div className="text-sm text-gray-600">{product.sales} sales</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Product Modal Component
const ProductModal = ({ product, onSave, onClose }) => {
  const [formData, setFormData] = useState({
    name: { en: '', it: '' },
    slug: '',
    short_description: { en: '', it: '' },
    description_html: { en: '', it: '' },
    category: 'skincare',
    price_eur: 0,
    price_membership: { gold: null, platinum: null, elite: null },
    tags: [],
    protocol_bindings: [],
    inventory: 0,
    is_active: true,
    badge: '',
    ingredients: { en: '', it: '' },
    warnings: { en: '', it: '' },
    usage_instructions: { en: '', it: '' },
    images: []
  });

  useEffect(() => {
    if (product) {
      setFormData({
        ...product,
        price_membership: product.price_membership || { gold: null, platinum: null, elite: null }
      });
    }
  }, [product]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  const handleInputChange = (field, value, lang = null) => {
    if (lang) {
      setFormData(prev => ({
        ...prev,
        [field]: {
          ...prev[field],
          [lang]: value
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [field]: value
      }));
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-[#C8A25A] to-[#E6C78A] p-6 text-white">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold">
              {product ? 'Edit Product' : 'Create Product'}
            </h2>
            <button onClick={onClose} className="text-white hover:text-gray-200">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto max-h-[calc(90vh-80px)]">
          <div className="space-y-6">
            {/* Basic Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Name (English)</label>
                <input
                  type="text"
                  value={formData.name.en}
                  onChange={(e) => handleInputChange('name', e.target.value, 'en')}
                  className="ka-input w-full"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Name (Italian)</label>
                <input
                  type="text"
                  value={formData.name.it}
                  onChange={(e) => handleInputChange('name', e.target.value, 'it')}
                  className="ka-input w-full"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
                <select
                  value={formData.category}
                  onChange={(e) => handleInputChange('category', e.target.value)}
                  className="ka-input w-full"
                >
                  <option value="skincare">Skincare</option>
                  <option value="supplements">Supplements</option>
                  <option value="kits">Kits</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Price (EUR)</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.price_eur}
                  onChange={(e) => handleInputChange('price_eur', parseFloat(e.target.value))}
                  className="ka-input w-full"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Inventory</label>
                <input
                  type="number"
                  value={formData.inventory}
                  onChange={(e) => handleInputChange('inventory', parseInt(e.target.value))}
                  className="ka-input w-full"
                />
              </div>
            </div>

            {/* Membership Pricing */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Membership Pricing</label>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Gold Price</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.price_membership.gold || ''}
                    onChange={(e) => handleInputChange('price_membership', {
                      ...formData.price_membership,
                      gold: e.target.value ? parseFloat(e.target.value) : null
                    })}
                    className="ka-input w-full"
                    placeholder="Optional"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Platinum Price</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.price_membership.platinum || ''}
                    onChange={(e) => handleInputChange('price_membership', {
                      ...formData.price_membership,
                      platinum: e.target.value ? parseFloat(e.target.value) : null
                    })}
                    className="ka-input w-full"
                    placeholder="Optional"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Elite Price</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.price_membership.elite || ''}
                    onChange={(e) => handleInputChange('price_membership', {
                      ...formData.price_membership,
                      elite: e.target.value ? parseFloat(e.target.value) : null
                    })}
                    className="ka-input w-full"
                    placeholder="Optional"
                  />
                </div>
              </div>
            </div>

            {/* Description */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Description (English)</label>
                <textarea
                  value={formData.short_description.en}
                  onChange={(e) => handleInputChange('short_description', e.target.value, 'en')}
                  className="ka-input w-full h-24"
                  rows={3}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Description (Italian)</label>
                <textarea
                  value={formData.short_description.it}
                  onChange={(e) => handleInputChange('short_description', e.target.value, 'it')}
                  className="ka-input w-full h-24"
                  rows={3}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Badge</label>
                <select
                  value={formData.badge}
                  onChange={(e) => handleInputChange('badge', e.target.value)}
                  className="ka-input w-full"
                >
                  <option value="">No Badge</option>
                  <option value="New">New</option>
                  <option value="Best Seller">Best Seller</option>
                  <option value="Platinum Only">Platinum Only</option>
                  <option value="Limited Edition">Limited Edition</option>
                </select>
              </div>
              <div className="flex items-center">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => handleInputChange('is_active', e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm font-medium text-gray-700">Active</span>
                </label>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-end space-x-4 mt-8 pt-6 border-t">
            <button
              type="button"
              onClick={onClose}
              className="ka-button-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="ka-button-primary"
            >
              {product ? 'Update Product' : 'Create Product'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default BoutiqueAdmin;