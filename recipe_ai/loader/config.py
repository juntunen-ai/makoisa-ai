"""Configuration for BigQuery loader."""

import os
from typing import Optional


class Config:
    """Configuration settings for BigQuery loader."""
    
    # Default BigQuery settings
    DEFAULT_DATASET_ID = "makoisa_ai"
    DEFAULT_TABLE_ID = "stores"
    DEFAULT_LOCATION = "US"
    
    # K-ruoka specific settings
    K_RUOKA_DATASET_ID = "k_kaupat"
    K_RUOKA_TABLE_ID = "products"
    
    # Environment variable names
    ENV_PROJECT_ID = "GOOGLE_CLOUD_PROJECT"
    ENV_DATASET_ID = "BIGQUERY_DATASET_ID"
    ENV_TABLE_ID = "BIGQUERY_TABLE_ID"
    ENV_CREDENTIALS = "GOOGLE_APPLICATION_CREDENTIALS"
    
    @classmethod
    def get_project_id(cls) -> Optional[str]:
        """Get project ID from environment."""
        return os.getenv(cls.ENV_PROJECT_ID)
    
    @classmethod
    def get_dataset_id(cls) -> str:
        """Get dataset ID from environment or default."""
        return os.getenv(cls.ENV_DATASET_ID, cls.DEFAULT_DATASET_ID)
    
    @classmethod
    def get_table_id(cls) -> str:
        """Get table ID from environment or default."""
        return os.getenv(cls.ENV_TABLE_ID, cls.DEFAULT_TABLE_ID)
    
    @classmethod
    def get_credentials_path(cls) -> Optional[str]:
        """Get credentials path from environment."""
        return os.getenv(cls.ENV_CREDENTIALS)
    
    @classmethod
    def get_full_table_id(cls, project_id: Optional[str] = None) -> str:
        """Get fully qualified table ID."""
        project = project_id or cls.get_project_id()
        if not project:
            raise ValueError("Project ID not specified and not found in environment")
        
        return f"{project}.{cls.get_dataset_id()}.{cls.get_table_id()}"
