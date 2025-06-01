"""Tests for the Ruokahinta scraper."""

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from scraper.main import SKaupatScraper, run_scrape


class TestSKaupatScraper:
    """Test cases for the Ruokahinta scraper."""

    @pytest.fixture
    def golden_page_html(self):
        """Load golden page HTML for testing."""
        # This would be a saved HTML file from s-kaupat.fi
        golden_page = Path(__file__).parent / "fixtures" / "golden_page.html"
        if golden_page.exists():
            return golden_page.read_text(encoding='utf-8')
        else:
            # Minimal mock HTML for testing
            return """
            <html>
            <body>
                <div class="store-card">
                    <h3 class="store-card__title">Test Store</h3>
                    <p class="store-card__address">Test Street 1, 00100 Helsinki</p>
                    <p class="store-card__hours">Ma-Pe 8-21, La 8-18</p>
                </div>
            </body>
            </html>
            """

    @pytest.fixture
    def mock_api_response(self):
        """Mock API response data."""
        return [
            {
                "name": "Test Store API",
                "address": "API Street 1",
                "city": "Helsinki", 
                "postal_code": "00100",
                "phone": "+358501234567",
                "opening_hours": {"monday": "8-21", "tuesday": "8-21"},
                "services": ["grocery", "pharmacy"],
                "lat": 60.1699,
                "lng": 24.9384,
                "type": "hypermarket"
            }
        ]

    @pytest.mark.asyncio
    async def test_api_approach_success(self, mock_api_response):
        """Test successful API data extraction."""
        
        with patch('httpx.AsyncClient') as mock_client:
            # Mock successful API response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_api_response
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            async with SKaupatScraper(use_browser=False) as scraper:
                result = await scraper._try_api_approach()
                
            assert result is not None
            assert len(result) == 1
            assert result[0]['name'] == 'Test Store API'
            assert result[0]['source'] == 'api'

    @pytest.mark.asyncio 
    async def test_api_approach_fallback(self):
        """Test fallback when API is not available."""
        
        with patch('httpx.AsyncClient') as mock_client:
            # Mock failed API responses
            mock_response = AsyncMock()
            mock_response.status_code = 404
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            async with SKaupatScraper(use_browser=False) as scraper:
                result = await scraper._try_api_approach()
                
            assert result is None

    @pytest.mark.asyncio
    async def test_normalize_api_data(self, mock_api_response):
        """Test API data normalization."""
        
        scraper = SKaupatScraper()
        normalized = scraper._normalize_api_data(mock_api_response)
        
        assert len(normalized) == 1
        store = normalized[0]
        assert store['name'] == 'Test Store API'
        assert store['address'] == 'API Street 1'
        assert store['city'] == 'Helsinki'
        assert store['postal_code'] == '00100'
        assert store['latitude'] == 60.1699
        assert store['longitude'] == 24.9384
        assert store['source'] == 'api'
        assert 'scraped_at' in store

    @pytest.mark.asyncio
    async def test_run_scrape_integration(self):
        """Integration test for run_scrape function."""
        
        with patch('scraper.main.SKaupatScraper') as mock_scraper_class:
            # Mock the scraper instance
            mock_scraper = AsyncMock()
            mock_scraper.scrape_stores.return_value = [
                {
                    'name': 'Integration Test Store',
                    'address': 'Test Address',
                    'source': 'test'
                }
            ]
            mock_scraper_class.return_value.__aenter__.return_value = mock_scraper
            
            result = await run_scrape(use_browser=False)
            
            assert len(result) == 1
            assert result[0]['name'] == 'Integration Test Store'

    def test_data_structure_validation(self, mock_api_response):
        """Test that scraped data has the expected structure."""
        
        scraper = SKaupatScraper()
        normalized = scraper._normalize_api_data(mock_api_response)
        
        required_fields = [
            'name', 'address', 'city', 'postal_code', 'phone',
            'hours', 'services', 'latitude', 'longitude', 
            'store_type', 'scraped_at', 'source'
        ]
        
        for store in normalized:
            for field in required_fields:
                assert field in store, f"Missing required field: {field}"


if __name__ == "__main__":
    pytest.main([__file__])
