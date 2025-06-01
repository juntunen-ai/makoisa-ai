"""Configuration for AI Recipe Generator."""

import os
from typing import Optional
import sys
from pathlib import Path

# Load environment variables from .env file if it exists
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                # Force override environment variables from .env file for recipe AI
                os.environ[key.strip()] = value.strip()

sys.path.append('/Users/harrijuntunen/s-kaupat-scraper')
try:
    from loader.config import Config as LoaderConfig
except ImportError:
    # Fallback for containerized environment
    try:
        from loader_config import Config as LoaderConfig
    except ImportError:
        # Create a minimal config class if loader is not available
        class LoaderConfig:
            @staticmethod
            def get_full_table_id(project_id):
                return f"{project_id}.scraped_data.products"


class RecipeAIConfig:
    """Configuration settings for AI Recipe Generator."""
    
    # Vertex AI settings
    DEFAULT_PROJECT_ID = "ruokahinta-scraper-1748695687"
    DEFAULT_LOCATION = "us-central1"  # Gemini models available here
    DEFAULT_MODEL = "gemini-2.5-flash-preview-05-20"
    
    # Recipe generation settings
    DEFAULT_RECIPE_LANGUAGE = "fi"  # Finnish
    MAX_INGREDIENTS = 20
    MAX_RECIPE_TOKENS = 2000
    
    # Ingredient matching settings
    FUZZY_MATCH_THRESHOLD = 0.7
    MAX_PRICE_RESULTS = 10
    
    # Environment variable names
    ENV_PROJECT_ID = "GOOGLE_CLOUD_PROJECT"
    ENV_VERTEX_LOCATION = "VERTEX_AI_LOCATION"
    ENV_VERTEX_MODEL = "VERTEX_AI_MODEL"
    ENV_CREDENTIALS = "GOOGLE_APPLICATION_CREDENTIALS"
    
    @classmethod
    def get_project_id(cls) -> str:
        """Get project ID from environment or default."""
        return os.getenv(cls.ENV_PROJECT_ID, cls.DEFAULT_PROJECT_ID)
    
    @classmethod
    def get_vertex_location(cls) -> str:
        """Get Vertex AI location from environment or default."""
        return os.getenv(cls.ENV_VERTEX_LOCATION, cls.DEFAULT_LOCATION)
    
    @classmethod
    def get_vertex_model(cls) -> str:
        """Get Vertex AI model from environment or default."""
        return os.getenv(cls.ENV_VERTEX_MODEL, cls.DEFAULT_MODEL)
    
    @classmethod
    def get_credentials_path(cls) -> Optional[str]:
        """Get credentials path from environment."""
        return os.getenv(cls.ENV_CREDENTIALS)
    
    @classmethod
    def get_bigquery_table(cls) -> str:
        """Get fully qualified BigQuery table ID using loader config."""
        # Use the existing loader config for consistency
        return LoaderConfig.get_full_table_id(cls.get_project_id())
