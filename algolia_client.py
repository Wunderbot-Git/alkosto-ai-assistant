"""
Algolia Client for Alkosto AI Assistant (Python)
Production-ready with retry logic, caching, and analytics
"""

import os
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from algoliasearch.search_client import SearchClient
from algoliasearch.exceptions import AlgoliaException

# Configuration
CONFIG = {
    "max_retries": 3,
    "retry_delay_ms": 1000,
    "cache_ttl_ms": 5 * 60 * 1000,  # 5 minutes
    "demo_fallback": True,
    "analytics_enabled": True
}

ALGOLIA_APP_ID = "QX5IPS1B1Q"
ALGOLIA_INDEX_NAME = "test_Philipp"
ALGOLIA_API_KEY = os.getenv("ALGOLIA_API_KEY")


@dataclass
class CacheEntry:
    data: Dict
    timestamp: int


class AlkostoAlgoliaClient:
    def __init__(self):
        self.client = None
        self.index = None
        self.is_demo_mode = False
        self.search_cache: Dict[str, CacheEntry] = {}
        self.analytics_log: List[Dict] = []
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Algolia client or fall back to demo mode"""
        if not ALGOLIA_API_KEY:
            print("⚠️  Demo-Modus: Kein ALGOLIA_API_KEY gefunden. Verwende Beispiel-Daten.")
            self.is_demo_mode = True
            return
        
        try:
            self.client = SearchClient.create(ALGOLIA_APP_ID, ALGOLIA_API_KEY)
            self.index = self.client.init_index(ALGOLIA_INDEX_NAME)
            print("✅ Algolia client initialized")
        except Exception as e:
            print(f"❌ Failed to initialize Algolia client: {e}")
            if CONFIG["demo_fallback"]:
                print("🔄 Fallback to demo mode")
                self.is_demo_mode = True
    
    def _generate_cache_key(self, params: Dict) -> str:
        """Generate cache key from search parameters"""
        return json.dumps({
            "query": params.get("query", ""),
            "filters": params.get("filters", ""),
            "hits_per_page": params.get("hits_per_page", 5)
        }, sort_keys=True)
    
    def _is_cache_valid(self, entry: Optional[CacheEntry]) -> bool:
        """Check if cache entry is still valid"""
        if not entry:
            return False
        age = int(time.time() * 1000) - entry.timestamp
        return age < CONFIG["cache_ttl_ms"]
    
    def _log_analytics(self, params: Dict, result: Dict, duration: int, from_cache: bool = False):
        """Log search analytics"""
        if not CONFIG["analytics_enabled"]:
            return
        
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "query": params.get("query"),
            "filters": params.get("filters"),
            "hits_count": len(result.get("hits", [])),
            "total_hits": result.get("total", 0),
            "duration": duration,
            "from_cache": from_cache,
            "source": "demo" if self.is_demo_mode else "algolia"
        }
        
        self.analytics_log.append(log_entry)
        
        # Keep only last 1000 entries
        if len(self.analytics_log) > 1000:
            self.analytics_log.pop(0)
    
    def _delay(self, ms: int):
        """Delay for retry logic"""
        time.sleep(ms / 1000)
    
    def search_demo_products(self, params: Dict) -> Dict:
        """Search demo products with filtering"""
        query = params.get("query", "")
        filters = params.get("filters", "")
        hits_per_page = params.get("hits_per_page", 5)
        
        print(f"🔍 Demo-Suche: query='{query}', filters='{filters}'")
        
        results = DEMO_PRODUCTS.copy()
        
        # Apply filters
        if filters:
            # Budget filter
            import re
            budget_match = re.search(r'price_sale\s*<(\d+)', filters)
            if budget_match:
                budget = int(budget_match.group(1))
                results = [p for p in results if p["price_sale"] < budget]
            
            # Weight filter
            weight_match = re.search(r'weight_kg\s*<(\d+\.?\d*)', filters)
            if weight_match:
                max_weight = float(weight_match.group(1))
                results = [p for p in results if p.get("weight_kg", 999) < max_weight]
            
            # Battery filter
            battery_match = re.search(r'battery_hours\s*>(\d+\.?\d*)', filters)
            if battery_match:
                min_battery = float(battery_match.group(1))
                results = [p for p in results if p.get("battery_hours", 0) > min_battery]
            
            # Stock filter
            if "in_stock:true" in filters:
                results = [p for p in results if p.get("in_stock", False)]
        
        # Simple text search
        if query and query != "laptop":
            search_terms = query.lower().split()
            results = [
                p for p in results
                if any(term in p["name"].lower() for term in search_terms)
            ]
        
        # Sort by price
        results.sort(key=lambda x: x["price_sale"])
        
        return {
            "hits": results[:hits_per_page],
            "total": len(results),
            "page": 0,
            "processing_time_ms": 10,
            "source": "demo"
        }
    
    def _perform_algolia_search(self, params: Dict, attempt: int = 1) -> Dict:
        """Perform Algolia search with retry logic"""
        search_params = {
            "query": params.get("query", ""),
            "hitsPerPage": params.get("hits_per_page", 5),
            "attributesToRetrieve": params.get("attributes_to_retrieve", [])
        }
        
        if params.get("filters"):
            search_params["filters"] = params["filters"]
        
        try:
            result = self.index.search(search_params)
            
            return {
                "hits": result["hits"],
                "total": result["nbHits"],
                "page": result["page"],
                "processing_time_ms": result.get("processingTimeMS", 0),
                "source": "algolia"
            }
        except AlgoliaException as e:
            if attempt < CONFIG["max_retries"]:
                print(f"⚠️  Search failed (attempt {attempt}), retrying...")
                self._delay(CONFIG["retry_delay_ms"] * attempt)
                return self._perform_algolia_search(params, attempt + 1)
            raise
    
    def search_products(self, params: Optional[Dict] = None) -> Dict:
        """Main search function with caching and fallback"""
        params = params or {}
        start_time = int(time.time() * 1000)
        cache_key = self._generate_cache_key(params)
        
        # Check cache
        cached = self.search_cache.get(cache_key)
        if self._is_cache_valid(cached):
            print("📦 Cache hit")
            self._log_analytics(params, cached.data, 0, from_cache=True)
            return cached.data
        
        # Demo mode
        if self.is_demo_mode:
            result = self.search_demo_products(params)
            duration = int(time.time() * 1000) - start_time
            self._log_analytics(params, result, duration)
            
            # Cache result
            self.search_cache[cache_key] = CacheEntry(data=result, timestamp=start_time)
            return result
        
        # Real Algolia search
        try:
            result = self._perform_algolia_search(params)
            duration = int(time.time() * 1000) - start_time
            
            print(f"✅ {len(result['hits'])} Produkte gefunden (Total: {result['total']})")
            
            self._log_analytics(params, result, duration)
            
            # Cache result
            self.search_cache[cache_key] = CacheEntry(data=result, timestamp=start_time)
            
            return result
        except Exception as e:
            print(f"❌ Algolia Search Error: {e}")
            
            # Fallback to demo
            if CONFIG["demo_fallback"]:
                print("🔄 Falling back to demo data...")
                result = self.search_demo_products(params)
                result["fallback"] = True
                result["error"] = str(e)
                duration = int(time.time() * 1000) - start_time
                self._log_analytics(params, result, duration)
                return result
            
            raise
    
    def get_analytics(self) -> Dict:
        """Get analytics summary"""
        if not self.analytics_log:
            return {"message": "No analytics data available"}
        
        total = len(self.analytics_log)
        cached = sum(1 for log in self.analytics_log if log.get("from_cache"))
        avg_duration = sum(log.get("duration", 0) for log in self.analytics_log) / total
        demo_searches = sum(1 for log in self.analytics_log if log.get("source") == "demo")
        
        return {
            "total_searches": total,
            "cache_hits": cached,
            "cache_hit_rate": f"{(cached / total * 100):.1f}%",
            "average_duration": f"{avg_duration:.0f}ms",
            "demo_searches": demo_searches,
            "recent_searches": self.analytics_log[-10:]
        }
    
    def clear_cache(self):
        """Clear search cache"""
        self.search_cache.clear()
        print("🗑️  Search cache cleared")
    
    def set_demo_mode(self, enabled: bool):
        """Force demo mode (for testing)"""
        self.is_demo_mode = enabled
        print(f"🎮 Demo mode {'enabled' if enabled else 'disabled'}")


# Demo products
DEMO_PRODUCTS = [
    {
        "objectID": "demo-1",
        "name": "HP Laptop 15\" Intel Core i5 16GB RAM 512GB SSD",
        "brand": "HP",
        "price_sale": 2499000,
        "price_list": 2899000,
        "ram": "16 GB",
        "storage": "512 GB SSD",
        "processor": "Intel Core i5-1235U",
        "processor_brand": "Intel",
        "weight_kg": 1.69,
        "battery_hours": 8.0,
        "screen_size": "15.6 Pulgadas",
        "os": "Windows",
        "in_stock": True,
        "stock": 45,
        "key_features": [
            "Procesador Intel Core i5 de 12va generación",
            "16GB RAM para multitarea fluida",
            "Disco SSD 512GB de alta velocidad"
        ],
        "url": "https://www.alkosto.com/laptop-hp-15-intel-core-i5"
    },
    {
        "objectID": "demo-2",
        "name": "ASUS VivoBook 14\" AMD Ryzen 5 8GB RAM 256GB SSD",
        "brand": "ASUS",
        "price_sale": 1999000,
        "price_list": 2299000,
        "ram": "8 GB",
        "storage": "256 GB SSD",
        "processor": "AMD Ryzen 5 5500U",
        "processor_brand": "AMD",
        "weight_kg": 1.40,
        "battery_hours": 10.0,
        "screen_size": "14 Pulgadas",
        "os": "Windows",
        "in_stock": True,
        "stock": 23,
        "key_features": [
            "Diseño ultradelgado y ligero (1.4kg)",
            "Procesador AMD Ryzen 5 eficiente",
            "Pantalla NanoEdge con bordes delgados"
        ],
        "url": "https://www.alkosto.com/asus-vivobook-14-amd"
    },
    {
        "objectID": "demo-3",
        "name": "Lenovo IdeaPad 3 15.6\" Intel Core i3 8GB RAM 256GB SSD",
        "brand": "LENOVO",
        "price_sale": 1799000,
        "price_list": 1999000,
        "ram": "8 GB",
        "storage": "256 GB SSD",
        "processor": "Intel Core i3-1115G4",
        "processor_brand": "Intel",
        "weight_kg": 1.70,
        "battery_hours": 7.5,
        "screen_size": "15.6 Pulgadas",
        "os": "Windows",
        "in_stock": True,
        "stock": 67,
        "key_features": [
            "Excelente relación precio-rendimiento",
            "Pantalla HD antirreflejo",
            "Ideal para estudiantes y oficina"
        ],
        "url": "https://www.alkosto.com/lenovo-ideapad-3-15"
    }
]


# Singleton instance
_client = None

def get_client() -> AlkostoAlgoliaClient:
    """Get or create singleton client instance"""
    global _client
    if _client is None:
        _client = AlkostoAlgoliaClient()
    return _client
