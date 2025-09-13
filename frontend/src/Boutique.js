import React, { useState, useEffect } from 'react';
import { useTranslation } from './contexts/LanguageContext';
import OptimizedImage from './components/ui/OptimizedImage';

const Boutique = ({ backendUrl, user, onNavigate, onLogoClick }) => {
  const { t, language } = useTranslation();
  const [products, setProducts] = useState([]);
  const [collections, setCollections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedProtocol, setSelectedProtocol] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [cart, setCart] = useState([]);
  const [showCart, setShowCart] = useState(false);

  const API = `${backendUrl}/api`;

  useEffect(() => {
    loadBoutiqueData();
  }, [selectedCategory, selectedProtocol, searchTerm]);

  useEffect(() => {
    // Load cart from localStorage
    const savedCart = localStorage.getItem('kinaura_cart');
    if (savedCart) {
      setCart(JSON.parse(savedCart));
    }
  }, []);

  const loadBoutiqueData = async () => {
    try {
      setLoading(true);
      const axios = (await import('axios')).default;

      // Build query parameters
      const params = new URLSearchParams();
      if (selectedCategory !== 'all') params.append('category', selectedCategory);
      if (selectedProtocol !== 'all') params.append('protocol', selectedProtocol);
      if (searchTerm) params.append('search', searchTerm);

      // Load products
      const productsResponse = await axios.get(`${API}/shop/products?${params}`, {
        headers: user?.token ? { 'Authorization': `Bearer ${user.token}` } : {}
      });

      // Load collections
      const collectionsResponse = await axios.get(`${API}/shop/collections`, {
        headers: user?.token ? { 'Authorization': `Bearer ${user.token}` } : {}
      });

      if (productsResponse.data.success) {
        setProducts(productsResponse.data.products);
      }

      if (collectionsResponse.data.success) {
        setCollections(collectionsResponse.data.collections);
      }

    } catch (err) {
      console.error('Error loading boutique data:', err);
      setError('Failed to load boutique data');
    } finally {
      setLoading(false);
    }
  };

  const addToCart = (product, quantity = 1) => {
    const existingItem = cart.find(item => item.sku === product.sku);
    let newCart;

    if (existingItem) {
      newCart = cart.map(item =>
        item.sku === product.sku
          ? { ...item, quantity: item.quantity + quantity }
          : item
      );
    } else {
      newCart = [...cart, {
        sku: product.sku,
        name: product.name[language] || product.name.en,
        price: getProductPrice(product),
        image: product.images?.[0]?.url || '',
        quantity
      }];
    }

    setCart(newCart);
    localStorage.setItem('kinaura_cart', JSON.stringify(newCart));
    
    // Show success feedback
    showAddToCartFeedback(product.name[language] || product.name.en);
  };

  const removeFromCart = (sku) => {
    const newCart = cart.filter(item => item.sku !== sku);
    setCart(newCart);
    localStorage.setItem('kinaura_cart', JSON.stringify(newCart));
  };

  const updateCartQuantity = (sku, quantity) => {
    if (quantity === 0) {
      removeFromCart(sku);
      return;
    }

    const newCart = cart.map(item =>
      item.sku === sku ? { ...item, quantity } : item
    );
    setCart(newCart);
    localStorage.setItem('kinaura_cart', JSON.stringify(newCart));
  };

  const getProductPrice = (product) => {
    const basePrice = product.price_eur;
    const membershipTier = user?.membership_tier;

    if (membershipTier && product.price_membership?.[membershipTier]) {
      const discountedPrice = product.price_membership[membershipTier];
      return discountedPrice || basePrice;
    }

    return basePrice;
  };

  const showAddToCartFeedback = (productName) => {
    // Create temporary toast notification
    const toast = document.createElement('div');
    toast.className = 'fixed top-4 right-4 bg-[#C8A25A] text-white px-6 py-3 rounded-lg shadow-lg z-50 transform translate-x-0 transition-transform duration-300';
    toast.innerHTML = `
      <div class="flex items-center space-x-2">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
        </svg>
        <span>Added ${productName} to cart</span>
      </div>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => document.body.removeChild(toast), 300);
    }, 2000);
  };

  const getCartTotal = () => {
    return cart.reduce((total, item) => total + (item.price * item.quantity), 0);
  };

  const getCartItemCount = () => {
    return cart.reduce((total, item) => total + item.quantity, 0);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-cream p-4">
        <div className="max-w-6xl mx-auto">
          {/* Header Skeleton */}
          <div className="mb-8">
            <div className="h-8 bg-gray-200 rounded w-48 mb-4 animate-pulse"></div>
            <div className="h-4 bg-gray-200 rounded w-96 animate-pulse"></div>
          </div>
          
          {/* Products Grid Skeleton */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
              <div key={i} className="ka-card p-4">
                <div className="aspect-square bg-gray-200 rounded-lg mb-4 animate-pulse"></div>
                <div className="h-4 bg-gray-200 rounded mb-2 animate-pulse"></div>
                <div className="h-6 bg-gray-200 rounded w-20 animate-pulse"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream">
      {/* Navigation Header */}
      <div className="app-header content-above-kintsugi">
        <div className="flex items-center space-x-2 cursor-pointer" onClick={onLogoClick || (() => onNavigate('dashboard'))}>
          <img 
            src="/brand/kinaura-symbol.svg" 
            alt="KinAura" 
            className="ka-logo w-8 h-8"
          />
          <span className="kinaura-logo-text hover:text-gold transition-colors">KinAura</span>
        </div>
        
        <div className="flex items-center space-x-4">
          {/* Back Button */}
          <button 
            onClick={() => onNavigate('dashboard')}
            className="flex items-center space-x-1 text-gray-700 hover:text-[#C8A25A] transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            <span className="hidden sm:inline">{language === 'it' ? 'Indietro' : 'Back'}</span>
          </button>
          
          {/* Hamburger Menu */}
          <button 
            onClick={() => onNavigate('menu')}
            className="hamburger-menu flex flex-col space-y-1 p-2 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Open menu"
          >
            <div className="hamburger-line w-6 h-0.5 bg-gray-700"></div>
            <div className="hamburger-line w-6 h-0.5 bg-gray-700"></div>
            <div className="hamburger-line w-6 h-0.5 bg-gray-700"></div>
          </button>
        </div>
      </div>

      {/* Boutique Header */}
      <div className="bg-gradient-to-r from-[#C8A25A] to-[#E6C78A] text-white p-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold mb-2">
                {language === 'it' ? 'Boutique KinAura' : 'KinAura Boutique'}
              </h1>
              <p className="text-white text-opacity-90">
                {language === 'it' 
                  ? 'Porta KinAura a casa. Mantieni il tuo protocollo con skincare e nutraceutici selezionati.'
                  : 'Bring KinAura home. Maintain your protocol with curated skincare and nutraceuticals.'
                }
              </p>
            </div>
            
            {/* Cart Button */}
            <button
              onClick={() => setShowCart(true)}
              className="relative bg-white bg-opacity-20 backdrop-blur-sm border border-white border-opacity-30 text-white px-4 py-2 rounded-lg hover:bg-opacity-30 transition-colors flex items-center space-x-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4m0 0L7 13m0 0l-1.5 5M7 13l4.5-4.5m0 0v7a2 2 0 002 2h6a2 2 0 002-2v-7m-10 0h10" />
              </svg>
              <span>{language === 'it' ? 'Carrello' : 'Cart'}</span>
              {getCartItemCount() > 0 && (
                <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                  {getCartItemCount()}
                </span>
              )}
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto p-6">
        {/* Filters */}
        <div className="mb-8 space-y-4">
          <div className="flex flex-wrap gap-4">
            {/* Category Filter */}
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="ka-input min-w-[150px]"
            >
              <option value="all">{language === 'it' ? 'Tutte le categorie' : 'All Categories'}</option>
              <option value="skincare">{language === 'it' ? 'Skincare' : 'Skincare'}</option>
              <option value="supplements">{language === 'it' ? 'Integratori' : 'Supplements'}</option>
              <option value="kits">{language === 'it' ? 'Kit' : 'Kits'}</option>
            </select>

            {/* Protocol Filter */}
            <select
              value={selectedProtocol}
              onChange={(e) => setSelectedProtocol(e.target.value)}
              className="ka-input min-w-[150px]"
            >
              <option value="all">{language === 'it' ? 'Tutti i protocolli' : 'All Protocols'}</option>
              <option value="bright-and-even">{language === 'it' ? 'Luminosità & Uniformità' : 'Bright & Even'}</option>
              <option value="cellular-renewal">{language === 'it' ? 'Rinnovo Cellulare' : 'Cellular Renewal'}</option>
              <option value="longevity">{language === 'it' ? 'Longevità' : 'Longevity'}</option>
            </select>

            {/* Search */}
            <div className="flex-1 min-w-[200px]">
              <input
                type="text"
                placeholder={language === 'it' ? 'Cerca prodotti...' : 'Search products...'}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="ka-input w-full"
              />
            </div>
          </div>
        </div>

        {/* Collections Section */}
        {collections.length > 0 && (
          <div className="mb-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              {language === 'it' ? 'Collezioni Selezionate' : 'Curated Collections'}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {collections.map((collection) => (
                <div key={collection.id} className="ka-card p-6 group hover:shadow-lg transition-shadow">
                  {collection.hero_image && (
                    <OptimizedImage
                      src={collection.hero_image}
                      alt={collection.name[language] || collection.name.en}
                      className="w-full h-48 object-cover rounded-lg mb-4"
                    />
                  )}
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {collection.name[language] || collection.name.en}
                  </h3>
                  <p className="text-gray-600 text-sm mb-4">
                    {collection.description[language] || collection.description.en}
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">
                      {collection.populated_products?.length || 0} {language === 'it' ? 'prodotti' : 'products'}
                    </span>
                    <button className="ka-button-secondary text-sm">
                      {language === 'it' ? 'Esplora' : 'Explore'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Products Grid */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">
              {language === 'it' ? 'Prodotti' : 'Products'}
            </h2>
            <span className="text-gray-600">
              {products.length} {language === 'it' ? 'prodotti trovati' : 'products found'}
            </span>
          </div>

          {products.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🔍</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {language === 'it' ? 'Nessun prodotto trovato' : 'No products found'}
              </h3>
              <p className="text-gray-600">
                {language === 'it' ? 'Prova a modificare i filtri di ricerca.' : 'Try adjusting your search filters.'}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {products.map((product) => (
                <ProductCard 
                  key={product.sku} 
                  product={product} 
                  language={language}
                  user={user}
                  onAddToCart={addToCart}
                  getProductPrice={getProductPrice}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Shopping Cart Modal */}
      {showCart && (
        <ShoppingCartModal
          cart={cart}
          language={language}
          user={user}
          onClose={() => setShowCart(false)}
          onUpdateQuantity={updateCartQuantity}
          onRemove={removeFromCart}
          getCartTotal={getCartTotal}
          backendUrl={backendUrl}
        />
      )}
    </div>
  );
};

// Product Card Component
const ProductCard = ({ product, language, user, onAddToCart, getProductPrice }) => {
  const price = getProductPrice(product);
  const originalPrice = product.price_eur;
  const hasDiscount = price < originalPrice;
  const membershipTier = user?.membership_tier;

  return (
    <div className="ka-card group hover:shadow-lg transition-shadow duration-200">
      {/* Product Image */}
      <div className="relative aspect-square mb-4 overflow-hidden rounded-lg bg-gray-100">
        {product.images && product.images.length > 0 ? (
          <OptimizedImage
            src={product.images[0].url}
            alt={product.images[0].alt[language] || product.images[0].alt.en || product.name[language]}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center">
            <div className="text-gray-400 text-4xl">📦</div>
          </div>
        )}
        
        {/* Badge */}
        {product.badge && (
          <div className="absolute top-2 left-2">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              product.badge === 'New' ? 'bg-blue-500 text-white' :
              product.badge === 'Best Seller' ? 'bg-green-500 text-white' :
              product.badge === 'Platinum Only' ? 'bg-purple-500 text-white' :
              'bg-orange-500 text-white'
            }`}>
              {product.badge}
            </span>
          </div>
        )}

        {/* Membership Discount Badge */}
        {hasDiscount && membershipTier && (
          <div className="absolute top-2 right-2">
            <span className="bg-[#C8A25A] text-white px-2 py-1 rounded-full text-xs font-medium">
              {membershipTier}
            </span>
          </div>
        )}
      </div>

      {/* Product Info */}
      <div className="space-y-3">
        <div>
          <h3 className="font-semibold text-gray-900 line-clamp-2">
            {product.name[language] || product.name.en}
          </h3>
          {product.short_description && (
            <p className="text-sm text-gray-600 line-clamp-2 mt-1">
              {product.short_description[language] || product.short_description.en}
            </p>
          )}
        </div>

        {/* Price */}
        <div className="flex items-center space-x-2">
          <span className="text-lg font-bold text-[#C8A25A]">
            €{price.toFixed(2)}
          </span>
          {hasDiscount && (
            <span className="text-sm text-gray-500 line-through">
              €{originalPrice.toFixed(2)}
            </span>
          )}
        </div>

        {/* Add to Cart Button */}
        <button
          onClick={() => onAddToCart(product)}
          className="w-full ka-button-primary py-2 text-sm font-medium transition-colors"
        >
          {language === 'it' ? 'Aggiungi al carrello' : 'Add to Cart'}
        </button>
      </div>
    </div>
  );
};

// Shopping Cart Modal Component
const ShoppingCartModal = ({ cart, language, user, onClose, onUpdateQuantity, onRemove, getCartTotal, backendUrl }) => {
  const [loading, setLoading] = useState(false);

  const handleCheckout = async () => {
    try {
      setLoading(true);
      const axios = (await import('axios')).default;

      const checkoutData = {
        items: cart.map(item => ({
          sku: item.sku,
          quantity: item.quantity
        }))
      };

      const response = await axios.post(`${backendUrl}/api/shop/checkout/create-session`, checkoutData, {
        headers: {
          'Authorization': `Bearer ${user.token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.data.success) {
        // Redirect to Stripe checkout
        window.location.href = response.data.checkout_url;
      }
    } catch (error) {
      console.error('Checkout error:', error);
      alert(language === 'it' 
        ? 'Errore durante il checkout. Riprova.' 
        : 'Checkout error. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-[#C8A25A] to-[#E6C78A] p-6 text-white">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold">
              {language === 'it' ? 'Carrello' : 'Shopping Cart'}
            </h2>
            <button onClick={onClose} className="text-white hover:text-gray-200">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Cart Content */}
        <div className="p-6 overflow-y-auto max-h-96">
          {cart.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-4xl mb-4">🛒</div>
              <p className="text-gray-600">
                {language === 'it' ? 'Il tuo carrello è vuoto' : 'Your cart is empty'}
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {cart.map((item) => (
                <div key={item.sku} className="flex items-center space-x-4 p-4 border border-gray-200 rounded-lg">
                  <img src={item.image} alt={item.name} className="w-16 h-16 object-cover rounded" />
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">{item.name}</h4>
                    <p className="text-sm text-gray-600">€{item.price.toFixed(2)}</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => onUpdateQuantity(item.sku, item.quantity - 1)}
                      className="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-100"
                    >
                      -
                    </button>
                    <span className="w-8 text-center">{item.quantity}</span>
                    <button
                      onClick={() => onUpdateQuantity(item.sku, item.quantity + 1)}
                      className="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-100"
                    >
                      +
                    </button>
                  </div>
                  <button
                    onClick={() => onRemove(item.sku)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        {cart.length > 0 && (
          <div className="border-t p-6 bg-gray-50">
            <div className="flex justify-between items-center mb-4">
              <span className="text-lg font-semibold">
                {language === 'it' ? 'Totale:' : 'Total:'}
              </span>
              <span className="text-xl font-bold text-[#C8A25A]">
                €{getCartTotal().toFixed(2)}
              </span>
            </div>
            <button
              onClick={handleCheckout}
              disabled={loading || !user}
              className="w-full ka-button-primary py-3 font-medium disabled:opacity-50"
            >
              {loading 
                ? (language === 'it' ? 'Elaborazione...' : 'Processing...') 
                : (language === 'it' ? 'Procedi al pagamento' : 'Proceed to Checkout')
              }
            </button>
            {!user && (
              <p className="text-sm text-gray-600 text-center mt-2">
                {language === 'it' ? 'Accedi per completare l\'acquisto' : 'Login required to checkout'}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Boutique;