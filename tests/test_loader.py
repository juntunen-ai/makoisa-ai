"""Tests for BigQuery loader functionality."""

import json
import pytest
import tempfile
import os
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from loader.main import BigQueryLoader, load_stores_to_bigquery
from loader.config import Config


@pytest.fixture
def sample_stores() -> List[Dict[str, Any]]:
    """Sample store data for testing."""
    return [
        {
            "name": "Prisma Espoo",
            "address": "Kauppakatu 1",
            "city": "Espoo",
            "postal_code": "02100",
            "hours": "Ma-Su 8-22",
            "services": ["Pickup", "Delivery"],
            "store_type": "prisma",
            "scraped_at": "2024-01-15T10:30:00+00:00",
        },
        {
            "name": "S-market Helsinki",
            "address": "Mannerheimintie 10",
            "city": "Helsinki",
            "postal_code": "00100",
            "hours": "Ma-Su 7-23",
            "services": ["Pickup"],
            "store_type": "s-market",
            "scraped_at": "2024-01-15T10:31:00+00:00",
        },
    ]


@pytest.fixture
def sample_stores_file(sample_stores: List[Dict[str, Any]]) -> str:
    """Create a temporary JSON file with sample stores."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_stores, f)
        return f.name


class TestBigQueryLoader:
    """Test BigQuery loader functionality."""
    
    @patch('loader.main.bigquery.Client')
    def test_init_with_project_id(self, mock_client_class):
        """Test BigQueryLoader initialization with project ID."""
        mock_client = Mock()
        mock_client.project = "test-project"
        mock_client_class.return_value = mock_client
        
        loader = BigQueryLoader(project_id="test-project")
        
        assert loader.project_id == "test-project"
        assert loader.dataset_id == "s_kaupat"
        assert loader.table_id == "stores"
        mock_client_class.assert_called_once_with(project="test-project")
    
    @patch('loader.main.bigquery.Client')
    def test_init_auto_detect_project(self, mock_client_class):
        """Test BigQueryLoader initialization with auto-detected project."""
        mock_client = Mock()
        mock_client.project = "auto-detected-project"
        mock_client_class.return_value = mock_client
        
        loader = BigQueryLoader()
        
        assert loader.project_id == "auto-detected-project"
        mock_client_class.assert_called_once_with(project=None)
    
    @patch('loader.main.bigquery.Client')
    def test_prepare_data(self, mock_client_class, sample_stores):
        """Test data preparation for BigQuery."""
        mock_client = Mock()
        mock_client.project = "test-project"
        mock_client_class.return_value = mock_client
        
        loader = BigQueryLoader(project_id="test-project")
        df = loader._prepare_data(sample_stores)
        
        assert len(df) == 2
        assert "loaded_at" in df.columns
        assert "scraped_at" in df.columns
        assert all(isinstance(services, list) for services in df["services"])
        assert df["name"].notna().all()
        assert df["store_type"].notna().all()
    
    @patch('loader.main.bigquery.Client')
    def test_prepare_data_empty_list(self, mock_client_class):
        """Test data preparation with empty store list."""
        mock_client = Mock()
        mock_client.project = "test-project"
        mock_client_class.return_value = mock_client
        
        loader = BigQueryLoader(project_id="test-project")
        
        with pytest.raises(ValueError, match="No stores data provided"):
            loader._prepare_data([])
    
    @patch('loader.main.bigquery.Client')
    def test_prepare_data_missing_required_field(self, mock_client_class):
        """Test data preparation with missing required field."""
        mock_client = Mock()
        mock_client.project = "test-project"
        mock_client_class.return_value = mock_client
        
        loader = BigQueryLoader(project_id="test-project")
        
        # Missing 'name' field
        stores = [{"store_type": "prisma", "city": "Helsinki"}]
        
        with pytest.raises(ValueError, match="Required field 'name' missing"):
            loader._prepare_data(stores)
    
    @patch('loader.main.bigquery.Client')
    def test_load_stores_success(self, mock_client_class, sample_stores):
        """Test successful store loading."""
        mock_client = Mock()
        mock_client.project = "test-project"
        mock_client_class.return_value = mock_client
        
        # Mock dataset and table operations
        mock_client.get_dataset.return_value = Mock()
        mock_client.get_table.return_value = Mock()
        
        # Mock load job
        mock_job = Mock()
        mock_job.result.return_value = None
        mock_job.error_result = None
        mock_job.output_rows = 2
        mock_client.load_table_from_dataframe.return_value = mock_job
        
        loader = BigQueryLoader(project_id="test-project")
        job = loader.load_stores(sample_stores)
        
        assert job == mock_job
        mock_client.load_table_from_dataframe.assert_called_once()
    
    @patch('loader.main.bigquery.Client')
    def test_load_from_file(self, mock_client_class, sample_stores_file):
        """Test loading stores from file."""
        mock_client = Mock()
        mock_client.project = "test-project"
        mock_client_class.return_value = mock_client
        
        # Mock operations
        mock_client.get_dataset.return_value = Mock()
        mock_client.get_table.return_value = Mock()
        
        mock_job = Mock()
        mock_job.result.return_value = None
        mock_job.error_result = None
        mock_job.output_rows = 2
        mock_client.load_table_from_dataframe.return_value = mock_job
        
        loader = BigQueryLoader(project_id="test-project")
        job = loader.load_from_file(sample_stores_file)
        
        assert job == mock_job
        
        # Cleanup
        os.unlink(sample_stores_file)
    
    @patch('loader.main.bigquery.Client')
    def test_query_stores(self, mock_client_class):
        """Test querying stores from BigQuery."""
        mock_client = Mock()
        mock_client.project = "test-project"
        mock_client_class.return_value = mock_client
        
        # Mock query results
        mock_row1 = {"name": "Store 1", "store_type": "prisma", "city": "Helsinki"}
        mock_row2 = {"name": "Store 2", "store_type": "alepa", "city": "Espoo"}
        mock_results = [mock_row1, mock_row2]
        
        mock_query_job = Mock()
        mock_query_job.result.return_value = mock_results
        mock_client.query.return_value = mock_query_job
        
        loader = BigQueryLoader(project_id="test-project")
        stores = loader.query_stores(limit=10, store_type="prisma")
        
        assert len(stores) == 2
        assert stores[0] == mock_row1
        assert stores[1] == mock_row2
        
        # Verify query was called with filters
        call_args = mock_client.query.call_args[0][0]
        assert "store_type = 'prisma'" in call_args
        assert "LIMIT 10" in call_args
    
    @patch('loader.main.bigquery.Client')
    def test_get_table_info(self, mock_client_class):
        """Test getting table information."""
        mock_client = Mock()
        mock_client.project = "test-project"
        mock_client_class.return_value = mock_client
        
        # Mock table
        mock_table = Mock()
        mock_table.project = "test-project"
        mock_table.dataset_id = "s_kaupat"
        mock_table.table_id = "stores"
        mock_table.num_rows = 100
        mock_table.num_bytes = 1024
        mock_table.created = datetime.now(timezone.utc)
        mock_table.modified = datetime.now(timezone.utc)
        
        # Mock schema
        mock_field = Mock()
        mock_field.name = "name"
        mock_field.field_type = "STRING"
        mock_field.mode = "REQUIRED"
        mock_field.description = "Store name"
        mock_table.schema = [mock_field]
        
        mock_client.get_table.return_value = mock_table
        
        loader = BigQueryLoader(project_id="test-project")
        info = loader.get_table_info()
        
        assert info["project_id"] == "test-project"
        assert info["num_rows"] == 100
        assert info["num_bytes"] == 1024
        assert len(info["schema"]) == 1
        assert info["schema"][0]["name"] == "name"


class TestConfig:
    """Test configuration functionality."""
    
    def test_default_values(self):
        """Test default configuration values."""
        assert Config.DEFAULT_DATASET_ID == "s_kaupat"
        assert Config.DEFAULT_TABLE_ID == "stores"
        assert Config.DEFAULT_LOCATION == "US"
    
    @patch.dict(os.environ, {"GOOGLE_CLOUD_PROJECT": "env-project"})
    def test_get_project_id_from_env(self):
        """Test getting project ID from environment."""
        assert Config.get_project_id() == "env-project"
    
    @patch.dict(os.environ, {"BIGQUERY_DATASET_ID": "custom_dataset"})
    def test_get_dataset_id_from_env(self):
        """Test getting dataset ID from environment."""
        assert Config.get_dataset_id() == "custom_dataset"
    
    def test_get_dataset_id_default(self):
        """Test getting default dataset ID."""
        with patch.dict(os.environ, {}, clear=True):
            assert Config.get_dataset_id() == "s_kaupat"
    
    def test_get_full_table_id(self):
        """Test getting full table ID."""
        full_id = Config.get_full_table_id("test-project")
        assert full_id == "test-project.s_kaupat.stores"
    
    def test_get_full_table_id_no_project(self):
        """Test getting full table ID without project."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Project ID not specified"):
                Config.get_full_table_id()


@patch('loader.main.bigquery.Client')
def test_load_stores_to_bigquery_function(mock_client_class, sample_stores):
    """Test the convenience function for loading stores."""
    mock_client = Mock()
    mock_client.project = "test-project"
    mock_client_class.return_value = mock_client
    
    # Mock operations
    mock_client.get_dataset.return_value = Mock()
    mock_client.get_table.return_value = Mock()
    
    mock_job = Mock()
    mock_job.result.return_value = None
    mock_job.error_result = None
    mock_job.output_rows = 2
    mock_client.load_table_from_dataframe.return_value = mock_job
    
    job = load_stores_to_bigquery(
        sample_stores,
        project_id="test-project",
        dataset_id="custom_dataset",
        table_id="custom_table",
    )
    
    assert job == mock_job
    mock_client_class.assert_called_once()
