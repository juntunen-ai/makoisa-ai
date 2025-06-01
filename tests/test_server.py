"""
Test suite for the FastAPI server
"""

import pytest
import requests
import subprocess
import time
import signal
import os

def test_server_imports():
    """Test that we can import the server module"""
    try:
        import server
        assert hasattr(server, 'app')
        assert server.app.title == "S-kaupat Scraper API"
        print("✅ Server module imports successfully")
    except Exception as e:
        pytest.fail(f"Failed to import server: {e}")

def test_fastapi_app_creation():
    """Test that FastAPI app is created properly"""
    import server
    app = server.app
    
    # Check app configuration
    assert app.title == "S-kaupat Scraper API"
    assert app.version == "1.0.0"
    assert "REST API for scraping S-kaupat.fi" in app.description
    print("✅ FastAPI app configured correctly")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
