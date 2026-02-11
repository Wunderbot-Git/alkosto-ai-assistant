/**
 * Enhanced Algolia Client with retry logic, caching, analytics, and fallback
 * @module algoliaClient
 */

const algoliasearch = require('algoliasearch');
require('dotenv').config();

// Algolia Configuration
const ALGOLIA_APP_ID = 'QX5IPS1B1Q';
const ALGOLIA_INDEX_NAME = 'test_Philipp';
const ALGOLIA_API_KEY = process.env.ALGOLIA_API_KEY;

// Configuration constants
const CONFIG = {
  MAX_RETRIES: 3,
  RETRY_DELAY_MS: 1000,
  CACHE_TTL_MS: 5 * 60 * 1000, // 5 minutes
  DEMO_FALLBACK: true,
  ANALYTICS_ENABLED: true
};

/**
 * Cache structure for search results
 * @typedef {Object} CacheEntry
 * @property {Object} data - Cached search results
 * @property {number} timestamp - When the entry was cached
 */

/** @type {Map<string, CacheEntry>} */
const searchCache = new Map();

/** @type {Array<Object>} */
const analyticsLog = [];

// Demo products for fallback mode
const DEMO_PRODUCTS = [
  {
    objectID: 'demo-1',
    name: 'HP Laptop 15" Intel Core i5 16GB RAM 512GB SSD',
    brand: 'HP',
    price_sale: 2499000,
    price_list: 2899000,
    ram: '16 GB',
    storage: '512 GB SSD',
    processor: 'Intel Core i5-1235U',
    processor_brand: 'Intel',
    weight_kg: 1.69,
    battery_hours: 8.0,
    screen_size: '15.6 Pulgadas',
    os: 'Windows',
    in_stock: true,
    stock: 45,
    key_features: [
      'Procesador Intel Core i5 de 12va generación',
      '16GB RAM para multitarea fluida',
      'Disco SSD 512GB de alta velocidad',
      'Pantalla Full HD de 15.6 pulgadas',
      'Windows 11 Home preinstalado'
    ],
    url: 'https://www.alkosto.com/laptop-hp-15-intel-core-i5',
    image_1: 'https://cdn.dam.alkosto.com/hp-laptop-15.jpg'
  },
  {
    objectID: 'demo-2',
    name: 'ASUS VivoBook 14" AMD Ryzen 5 8GB RAM 256GB SSD',
    brand: 'ASUS',
    price_sale: 1999000,
    price_list: 2299000,
    ram: '8 GB',
    storage: '256 GB SSD',
    processor: 'AMD Ryzen 5 5500U',
    processor_brand: 'AMD',
    weight_kg: 1.40,
    battery_hours: 10.0,
    screen_size: '14 Pulgadas',
    os: 'Windows',
    in_stock: true,
    stock: 23,
    key_features: [
      'Diseño ultradelgado y ligero (1.4kg)',
      'Procesador AMD Ryzen 5 eficiente',
      'Pantalla NanoEdge con bordes delgados',
      'Teclado retroiluminado',
      'Batería de larga duración'
    ],
    url: 'https://www.alkosto.com/asus-vivobook-14-amd',
    image_1: 'https://cdn.dam.alkosto.com/asus-vivobook-14.jpg'
  },
  {
    objectID: 'demo-3',
    name: 'Lenovo IdeaPad 3 15.6" Intel Core i3 8GB RAM 256GB SSD',
    brand: 'LENOVO',
    price_sale: 1799000,
    price_list: 1999000,
    ram: '8 GB',
    storage: '256 GB SSD',
    processor: 'Intel Core i3-1115G4',
    processor_brand: 'Intel',
    weight_kg: 1.70,
    battery_hours: 7.5,
    screen_size: '15.6 Pulgadas',
    os: 'Windows',
    in_stock: true,
    stock: 67,
    key_features: [
      'Excelente relación precio-rendimiento',
      'Pantalla HD antirreflejo',
      'Dolby Audio para mejor sonido',
      'Webcam con obturador de privacidad',
      'Ideal para estudiantes y oficina'
    ],
    url: 'https://www.alkosto.com/lenovo-ideapad-3-15',
    image_1: 'https://cdn.dam.alkosto.com/lenovo-ideapad-3.jpg'
  },
  {
    objectID: 'demo-4',
    name: 'MacBook Air M2 13.6" 8GB RAM 256GB SSD',
    brand: 'APPLE',
    price_sale: 4999000,
    price_list: 5499000,
    ram: '8 GB',
    storage: '256 GB SSD',
    processor: 'Apple M2',
    processor_brand: 'Apple',
    weight_kg: 1.24,
    battery_hours: 18.0,
    screen_size: '13.6 Pulgadas',
    os: 'MacOS',
    in_stock: true,
    stock: 15,
    key_features: [
      'Chip M2 ultraeficiente',
      'Diseño ultrafino y ligero',
      'Hasta 18 horas de batería',
      'Pantalla Liquid Retina',
      'Cámara FaceTime HD'
    ],
    url: 'https://www.alkosto.com/macbook-air-m2',
    image_1: 'https://cdn.dam.alkosto.com/macbook-air-m2.jpg'
  },
  {
    objectID: 'demo-5',
    name: 'Dell Inspiron 15 3000 Intel Core i5 12GB RAM 512GB SSD',
    brand: 'DELL',
    price_sale: 2299000,
    price_list: 2599000,
    ram: '12 GB',
    storage: '512 GB SSD',
    processor: 'Intel Core i5-1235U',
    processor_brand: 'Intel',
    weight_kg: 1.73,
    battery_hours: 8.5,
    screen_size: '15.6 Pulgadas',
    os: 'Windows',
    in_stock: true,
    stock: 32,
    key_features: [
      'Procesador Intel Core i5 de 12va gen',
      '12GB RAM para mejor multitarea',
      'SSD 512GB de alta velocidad',
      'Pantalla FHD con micro-bordes',
      'Teclado numérico incluido'
    ],
    url: 'https://www.alkosto.com/dell-inspiron-15-3000',
    image_1: 'https://cdn.dam.alkosto.com/dell-inspiron-15.jpg'
  }
];

let client = null;
let index = null;
let isDemoMode = false;

/**
 * Initialize Algolia client
 * Falls back to demo mode if API key is missing or connection fails
 */
function initializeClient() {
  if (!ALGOLIA_API_KEY) {
    console.log('⚠️  Demo-Modus: Kein ALGOLIA_API_KEY gefunden. Verwende Beispiel-Daten.');
    isDemoMode = true;
    return;
  }

  try {
    client = algoliasearch(ALGOLIA_APP_ID, ALGOLIA_API_KEY);
    index = client.initIndex(ALGOLIA_INDEX_NAME);
    console.log('✅ Algolia client initialized');
  } catch (error) {
    console.error('❌ Failed to initialize Algolia client:', error.message);
    if (CONFIG.DEMO_FALLBACK) {
      console.log('🔄 Fallback to demo mode');
      isDemoMode = true;
    }
  }
}

/**
 * Generate cache key from search parameters
 * @param {Object} params - Search parameters
 * @returns {string} Cache key
 */
function generateCacheKey(params) {
  // Handle null/undefined params
  const safeParams = params || {};
  return JSON.stringify({
    query: safeParams.query || '',
    filters: safeParams.filters || '',
    hitsPerPage: safeParams.hitsPerPage || 5
  });
}

/**
 * Check if cache entry is still valid
 * @param {CacheEntry} entry - Cache entry to check
 * @returns {boolean} Whether entry is valid
 */
function isCacheValid(entry) {
  if (!entry) return false;
  const age = Date.now() - entry.timestamp;
  return age < CONFIG.CACHE_TTL_MS;
}

/**
 * Log search analytics
 * @param {Object} params - Search parameters
 * @param {Object} result - Search result
 * @param {number} duration - Search duration in ms
 * @param {boolean} fromCache - Whether result came from cache
 */
function logAnalytics(params, result, duration, fromCache = false) {
  if (!CONFIG.ANALYTICS_ENABLED) return;

  // Handle null/undefined params
  const safeParams = params || {};
  
  const logEntry = {
    timestamp: new Date().toISOString(),
    query: safeParams.query,
    filters: safeParams.filters,
    hitsCount: result.hits?.length || 0,
    totalHits: result.total,
    duration: duration,
    fromCache: fromCache,
    source: isDemoMode ? 'demo' : 'algolia'
  };

  analyticsLog.push(logEntry);

  // Keep only last 1000 entries
  if (analyticsLog.length > 1000) {
    analyticsLog.shift();
  }
}

/**
 * Delay function for retry logic
 * @param {number} ms - Milliseconds to delay
 * @returns {Promise<void>}
 */
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Search demo products with filtering
 * @param {Object} params - Search parameters
 * @returns {Object} Search results
 */
function searchDemoProducts(params) {
  // Handle null/undefined params
  const safeParams = params || {};
  const { query = '', filters = '', hitsPerPage = 5 } = safeParams;
  
  console.log('🔍 Demo-Suche:', { query, filters });
  
  let results = [...DEMO_PRODUCTS];
  
  // Apply filters
  if (filters) {
    // Budget filter
    const budgetMatch = filters.match(/price_sale\s*<?\s*(\d+)/);
    if (budgetMatch) {
      const budget = parseInt(budgetMatch[1]);
      results = results.filter(p => p.price_sale < budget);
    }
    
    // Weight filter
    const weightMatch = filters.match(/weight_kg\s*<?\s*(\d+\.?\d*)/);
    if (weightMatch) {
      const maxWeight = parseFloat(weightMatch[1]);
      results = results.filter(p => p.weight_kg < maxWeight);
    }
    
    // Battery filter
    const batteryMatch = filters.match(/battery_hours\s*>?\s*(\d+\.?\d*)/);
    if (batteryMatch) {
      const minBattery = parseFloat(batteryMatch[1]);
      results = results.filter(p => p.battery_hours > minBattery);
    }
    
    // Stock filter
    if (filters.includes('in_stock:true')) {
      results = results.filter(p => p.in_stock);
    }
    
    // Brand filter
    const brandMatch = filters.match(/brand:([^\s]+)/);
    if (brandMatch) {
      const brand = brandMatch[1].toUpperCase();
      results = results.filter(p => p.brand.toUpperCase() === brand);
    }
  }
  
  // Simple text search on name
  if (query && query !== 'laptop') {
    const searchTerms = query.toLowerCase().split(' ');
    results = results.filter(p => {
      const nameLower = p.name.toLowerCase();
      return searchTerms.some(term => nameLower.includes(term));
    });
  }
  
  // Sort by price
  results.sort((a, b) => a.price_sale - b.price_sale);
  
  return {
    hits: results.slice(0, hitsPerPage),
    total: results.length,
    page: 0,
    processingTimeMs: 10,
    source: 'demo'
  };
}

/**
 * Perform Algolia search with retry logic
 * @param {Object} params - Search parameters
 * @param {number} attempt - Current attempt number
 * @returns {Promise<Object>} Search results
 */
async function performAlgoliaSearch(params, attempt = 1) {
  const searchParams = {
    query: params.query || '',
    hitsPerPage: params.hitsPerPage || 5,
    attributesToRetrieve: params.attributesToRetrieve || []
  };

  if (params.filters) {
    searchParams.filters = params.filters;
  }

  try {
    const result = await index.search(searchParams);
    
    return {
      hits: result.hits,
      total: result.nbHits,
      page: result.page,
      processingTimeMs: result.processingTimeMS,
      source: 'algolia'
    };
  } catch (error) {
    if (attempt < CONFIG.MAX_RETRIES) {
      console.log(`⚠️  Search failed (attempt ${attempt}), retrying...`);
      await delay(CONFIG.RETRY_DELAY_MS * attempt);
      return performAlgoliaSearch(params, attempt + 1);
    }
    throw error;
  }
}

/**
 * Main search function with caching, retry logic, and fallback
 * @param {Object} params - Search parameters
 * @param {string} params.query - Search query string
 * @param {string} params.filters - Algolia filter string
 * @param {number} params.hitsPerPage - Number of results to return
 * @param {string[]} params.attributesToRetrieve - Fields to retrieve
 * @returns {Promise<Object>} Search results
 * @throws {Error} If search fails and no fallback available
 */
async function searchProducts(params = {}) {
  const startTime = Date.now();
  const cacheKey = generateCacheKey(params);
  
  // Check cache
  const cached = searchCache.get(cacheKey);
  if (isCacheValid(cached)) {
    console.log('📦 Cache hit for query:', params.query);
    logAnalytics(params, cached.data, 0, true);
    return cached.data;
  }
  
  // Demo mode
  if (isDemoMode) {
    const result = searchDemoProducts(params);
    const duration = Date.now() - startTime;
    logAnalytics(params, result, duration, false);
    
    // Cache result
    searchCache.set(cacheKey, { data: result, timestamp: Date.now() });
    
    return result;
  }
  
  // Real Algolia search with retry
  try {
    const result = await performAlgoliaSearch(params);
    const duration = Date.now() - startTime;
    
    console.log(`✅ ${result.hits.length} Produkte gefunden (Total: ${result.total})`);
    
    logAnalytics(params, result, duration, false);
    
    // Cache result
    searchCache.set(cacheKey, { data: result, timestamp: Date.now() });
    
    return result;
  } catch (error) {
    console.error('❌ Algolia Search Error after retries:', error.message);
    
    // Fallback to demo if enabled
    if (CONFIG.DEMO_FALLBACK) {
      console.log('🔄 Falling back to demo data...');
      const result = searchDemoProducts(params);
      result.fallback = true;
      result.error = error.message;
      
      const duration = Date.now() - startTime;
      logAnalytics(params, result, duration, false);
      
      return result;
    }
    
    throw error;
  }
}

/**
 * Get analytics summary
 * @returns {Object} Analytics data
 */
function getAnalytics() {
  if (analyticsLog.length === 0) {
    return { message: 'No analytics data available' };
  }
  
  const total = analyticsLog.length;
  const cached = analyticsLog.filter(l => l.fromCache).length;
  const avgDuration = analyticsLog.reduce((sum, l) => sum + l.duration, 0) / total;
  const demoSearches = analyticsLog.filter(l => l.source === 'demo').length;
  
  return {
    totalSearches: total,
    cacheHits: cached,
    cacheHitRate: (cached / total * 100).toFixed(1) + '%',
    averageDuration: Math.round(avgDuration) + 'ms',
    demoSearches: demoSearches,
    recentSearches: analyticsLog.slice(-10)
  };
}

/**
 * Clear search cache
 */
function clearCache() {
  searchCache.clear();
  console.log('🗑️  Search cache cleared');
}

/**
 * Clear analytics log (for testing)
 */
function clearAnalytics() {
  analyticsLog.length = 0;
  console.log('🗑️  Analytics log cleared');
}

/**
 * Get cache stats
 * @returns {Object} Cache statistics
 */
function getCacheStats() {
  return {
    entries: searchCache.size,
    maxAge: CONFIG.CACHE_TTL_MS / 1000 + ' seconds'
  };
}

/**
 * Force demo mode (for testing)
 * @param {boolean} enabled - Whether to enable demo mode
 */
function setDemoMode(enabled) {
  isDemoMode = enabled;
  console.log(`🎮 Demo mode ${enabled ? 'enabled' : 'disabled'}`);
}

// Initialize on module load
initializeClient();

module.exports = {
  searchProducts,
  getAnalytics,
  clearCache,
  clearAnalytics,
  getCacheStats,
  setDemoMode,
  DEMO_PRODUCTS,
  ALGOLIA_INDEX_NAME,
  CONFIG
};