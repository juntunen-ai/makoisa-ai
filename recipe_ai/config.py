"""Configuration for AI Recipe Generator."""

import os
from typing import Optional


class RecipeAIConfig:
    """Configuration settings for AI Recipe Generator."""
    
    # Vertex AI settings
    DEFAULT_PROJECT_ID = "ruokahinta-scraper-1748695687"
    DEFAULT_LOCATION = "europe-west1"  # Good for EU users
    DEFAULT_MODEL = "gemini-1.5-pro"
    
    # BigQuery settings (inherit from existing config)
    BIGQUERY_DATASET_ID = "s_kaupat"
    BIGQUERY_TABLE_ID = "stores"
    
    # Recipe generation settings
    DEFAULT_RECIPE_LANGUAGE = "fi"  # Finnish
    MAX_INGREDIENTS = 20
    MAX_RECIPE_TOKENS = 2000
    
    # Ingredient matching settings
    FUZZY_MATCH_THRESHOLD = 0.7
    MAX_PRICE_RESULTS = 5
    
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
        """Get fully qualified BigQuery table ID."""
        return f"{cls.get_project_id()}.{cls.BIGQUERY_DATASET_ID}.{cls.BIGQUERY_TABLE_ID}"
