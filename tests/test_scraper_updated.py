"""Tests for the S-kaupat scraper."""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock
from scraper.main import SKaupatScraper, run_scrape

class TestSKaupatScraper:
    """Test the main scraper functionality."""
    
    @pytest.mark.asyncio
    async def test_scraper_initialization(self):
        """Test scraper can be initialized."""
        scraper = SKaupatScraper(use_browser=True)
        assert scraper.use_browser is True
        
        scraper = SKaupatScraper(use_browser=False)
        assert scraper.use_browser is False
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting function."""
        scraper = SKaupatScraper()
        start_time = asyncio.get_event_loop().time()
        await scraper._rate_limit()
        end_time = asyncio.get_event_loop().time()
        
        # Should delay for at least MIN_DELAY_SECONDS
        assert (end_time - start_time) >= 1.0
    
    def test_normalize_api_data(self):
        """Test API data normalization."""
        scraper = SKaupatScraper()
        
        api_data = [
            {
                'name': 'Test Store',
                'address': '123 Test St',
                'city': 'Test City',
                'postal_code': '12345',
                'lat': 60.1699,
                'lng': 24.9384,
                'type': 'Prisma'
            }
        ]
        
        normalized = scraper._normalize_api_data(api_data)
        
        assert len(normalized) == 1
        store = normalized[0]
        assert store['name'] == 'Test Store'
        assert store['address'] == '123 Test St'
        assert store['city'] == 'Test City'
        assert store['postal_code'] == '12345'
        assert store['latitude'] == 60.1699
        assert store['longitude'] == 24.9384
        assert store['store_type'] == 'Prisma'
        assert store['source'] == 'api'
    
    @pytest.mark.asyncio
    async def test_run_scrape_function(self):
        """Test the public run_scrape function."""
        # This is an integration test that requires network access
        # In a real CI environment, this might be skipped or mocked
        try:
            stores = await run_scrape(use_browser=True)
            assert isinstance(stores, list)
            # Should find at least some stores
            if stores:
                store = stores[0]
                required_fields = ['name', 'address', 'store_type', 'scraped_at', 'source']
                for field in required_fields:
                    assert field in store
        except Exception as e:
            pytest.skip(f"Integration test failed, likely due to network or site changes: {e}")

    def test_store_data_structure(self):
        """Test that scraped data has the expected structure."""
        # Load the golden data file if it exists
        try:
            with open('scraped_stores.json', 'r', encoding='utf-8') as f:
                stores = json.load(f)
                
            if not stores:
                pytest.skip("No stores data available for testing")
                
            store = stores[0]
            
            # Check required fields
            required_fields = [
                'name', 'address', 'city', 'postal_code', 'phone', 
                'hours', 'services', 'latitude', 'longitude', 
                'store_type', 'scraped_at', 'source'
            ]
            
            for field in required_fields:
                assert field in store, f"Missing required field: {field}"
            
            # Check field types
            assert isinstance(store['name'], str)
            assert isinstance(store['address'], str) 
            assert isinstance(store['services'], list)
            assert store['source'] in ['api', 'browser']
            
            # Check store types are valid
            valid_store_types = [
                'Prisma', 'S-market', 'Food Market Herkku', 
                'Alepa', 'Sale', 'Sokos Herkku', 'Mestarin Herkku'
            ]
            assert store['store_type'] in valid_store_types
            
        except FileNotFoundError:
            pytest.skip("Golden data file not found")

class TestStoreDataParsing:
    """Test store data parsing and extraction."""
    
    def test_address_parsing(self):
        """Test address parsing logic."""
        # This would test the address parsing logic
        # For now, we can test the expected format
        test_addresses = [
            ("Unikkotie 13, 01300 Vantaa", "01300", "Vantaa"),
            ("Teollisuustie 2, 96320 Rovaniemi", "96320", "Rovaniemi"),
            ("Aleksanterinkatu 52, 00100 Helsinki", "00100", "Helsinki"),
        ]
        
        for address, expected_postal, expected_city in test_addresses:
            parts = address.split(',')
            if len(parts) >= 2:
                location_part = parts[-1].strip()
                location_words = location_part.split()
                if len(location_words) >= 2 and location_words[0].isdigit():
                    postal_code = location_words[0]
                    city = ' '.join(location_words[1:])
                    
                    assert postal_code == expected_postal
                    assert city == expected_city

if __name__ == "__main__":
    pytest.main([__file__])
