"""
Test Suite for Alkosto AI Assistant (Python)
Comprehensive tests for all functionality
"""

import pytest
import time
from unittest.mock import Mock, patch
from algolia_client import AlkostoAlgoliaClient, DEMO_PRODUCTS, get_client


@pytest.fixture
def client():
    """Create fresh client for each test"""
    client = AlkostoAlgoliaClient()
    client.set_demo_mode(True)
    client.clear_cache()
    return client


class TestBasicSearch:
    """Basic search functionality tests"""
    
    def test_search_returns_products(self, client):
        result = client.search_products({})
        assert "hits" in result
        assert "total" in result
        assert isinstance(result["hits"], list)
    
    def test_search_respects_hits_per_page(self, client):
        result = client.search_products({"hits_per_page": 2})
        assert len(result["hits"]) <= 2
    
    def test_search_includes_required_fields(self, client):
        result = client.search_products({"hits_per_page": 1})
        if result["hits"]:
            product = result["hits"][0]
            assert "objectID" in product
            assert "name" in product
            assert "brand" in product
            assert "price_sale" in product
    
    def test_returns_source_identifier(self, client):
        result = client.search_products({})
        assert result["source"] == "demo"


class TestBudgetFilter:
    """Budget filter tests"""
    
    def test_filter_products_under_budget(self, client):
        budget = 2000000
        result = client.search_products({
            "filters": f"price_sale < {budget}"
        })
        for product in result["hits"]:
            assert product["price_sale"] < budget
    
    def test_handles_very_low_budget(self, client):
        result = client.search_products({
            "filters": "price_sale < 1000000"
        })
        # Should return empty or very cheap products
        assert result["total"] >= 0
    
    def test_handles_very_high_budget(self, client):
        result = client.search_products({
            "filters": "price_sale < 10000000"
        })
        # Should return many or all products
        assert result["total"] >= 0


class TestPortabilityFilter:
    """Weight/portability filter tests"""
    
    def test_lightweight_filter(self, client):
        result = client.search_products({
            "filters": "weight_kg < 1.5"
        })
        for product in result["hits"]:
            assert product.get("weight_kg", 999) < 1.5
    
    def test_very_light_filter(self, client):
        result = client.search_products({
            "filters": "weight_kg < 1.0"
        })
        for product in result["hits"]:
            assert product.get("weight_kg", 999) < 1.0


class TestBatteryFilter:
    """Battery life filter tests"""
    
    def test_long_battery_filter(self, client):
        result = client.search_products({
            "filters": "battery_hours > 10"
        })
        for product in result["hits"]:
            assert product.get("battery_hours", 0) > 10
    
    def test_short_battery_filter(self, client):
        result = client.search_products({
            "filters": "battery_hours > 5"
        })
        for product in result["hits"]:
            assert product.get("battery_hours", 0) > 5


class TestCaching:
    """Cache functionality tests"""
    
    def test_cache_returns_same_result(self, client):
        params = {"query": "test", "filters": "price_sale < 3000000"}
        
        # First search
        result1 = client.search_products(params)
        
        # Second search (should be cached)
        result2 = client.search_products(params)
        
        assert result1["hits"] == result2["hits"]
    
    def test_cache_can_be_cleared(self, client):
        client.search_products({})
        client.clear_cache()
        assert len(client.search_cache) == 0


class TestAnalytics:
    """Analytics functionality tests"""
    
    def test_tracks_search_analytics(self, client):
        client.clear_analytics()
        client.search_products({"query": "test"})
        
        analytics = client.get_analytics()
        assert analytics["total_searches"] == 1
    
    def test_calculates_average_duration(self, client):
        client.clear_analytics()
        client.search_products({})
        client.search_products({})
        
        analytics = client.get_analytics()
        assert analytics["total_searches"] == 2
        assert "average_duration" in analytics


class TestEdgeCases:
    """Edge case handling tests"""
    
    def test_handles_none_parameters(self, client):
        result = client.search_products(None)
        assert "hits" in result
    
    def test_handles_empty_parameters(self, client):
        result = client.search_products({})
        assert "hits" in result
    
    def test_handles_missing_optional_fields(self, client):
        result = client.search_products({
            "query": "",
            "filters": "",
            "hits_per_page": 10
        })
        assert "hits" in result
    
    def test_handles_impossible_filter_combination(self, client):
        # Weight < 0.5 AND battery > 20 (likely no results)
        result = client.search_products({
            "filters": "weight_kg < 0.5 AND battery_hours > 20"
        })
        # Should handle gracefully
        assert result["total"] >= 0


class TestDataIntegrity:
    """Data integrity tests"""
    
    def test_demo_products_have_valid_prices(self, client):
        result = client.search_products({"hits_per_page": 10})
        for product in result["hits"]:
            assert isinstance(product["price_sale"], (int, float))
            assert product["price_sale"] > 0
    
    def test_demo_products_have_required_strings(self, client):
        result = client.search_products({"hits_per_page": 10})
        for product in result["hits"]:
            assert isinstance(product["name"], str)
            assert len(product["name"]) > 0
            assert isinstance(product["brand"], str)
    
    def test_unique_object_ids(self, client):
        result = client.search_products({"hits_per_page": 10})
        ids = [p["objectID"] for p in result["hits"]]
        assert len(ids) == len(set(ids))


class TestPerformance:
    """Performance tests"""
    
    def test_completes_within_reasonable_time(self, client):
        start = time.time()
        client.search_products({})
        duration = (time.time() - start) * 1000
        assert duration < 5000  # Should complete within 5 seconds
    
    def test_handles_rapid_searches(self, client):
        # Simulate rapid consecutive searches
        for _ in range(10):
            client.search_products({})
        # Should not crash


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
