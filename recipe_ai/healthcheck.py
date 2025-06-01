#!/usr/bin/env python3
"""
Health check endpoint for AI Recipe Generator Cloud Run deployment.
Returns 200 OK if the service is healthy.
"""

import sys
import os
import logging
from pathlib import Path

# Add the app directory to Python path
sys.path.append('/app')

def check_health():
    """Check if the service is healthy."""
    try:
        # Basic import check
        from recipe_ai.config import RecipeAIConfig
        
        # Check if we can access configuration
        project_id = RecipeAIConfig.get_project_id()
        if not project_id:
            return False, "Missing project ID configuration"
        
        # Check if Vertex AI client can be initialized
        from recipe_ai.vertex_ai_client import VertexAIClient
        client = VertexAIClient()
        
        return True, "Service is healthy"
        
    except Exception as e:
        return False, f"Health check failed: {str(e)}"

if __name__ == "__main__":
    try:
        healthy, message = check_health()
        if healthy:
            print(f"✅ {message}")
            sys.exit(0)
        else:
            print(f"❌ {message}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Health check error: {e}")
        sys.exit(1)
