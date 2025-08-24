"""BigQuery loader for Makoisa AI store and product data."""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone

try:
    from google.cloud import bigquery
    from google.cloud.bigquery import LoadJobConfig, SchemaField, WriteDisposition
    from google.auth import default
    from google.auth.exceptions import DefaultCredentialsError
    import pandas as pd
except ImportError as e:
    raise ImportError(
        "BigQuery dependencies not installed. Run: poetry add google-cloud-bigquery google-auth pandas"
    ) from e

logger = logging.getLogger(__name__)


class BigQueryLoader:
    """Load scraped store data into BigQuery."""
    
    # BigQuery table schema for Makoisa AI stores
    TABLE_SCHEMA = [
        SchemaField("name", "STRING", mode="REQUIRED", description="Store name"),
        SchemaField("address", "STRING", mode="NULLABLE", description="Store address"),
        SchemaField("city", "STRING", mode="NULLABLE", description="Store city"),
        SchemaField("postal_code", "STRING", mode="NULLABLE", description="Store postal code"),
        SchemaField("hours", "STRING", mode="NULLABLE", description="Store operating hours"),
        SchemaField("services", "STRING", mode="REPEATED", description="Store services array"),
        SchemaField("store_type", "STRING", mode="REQUIRED", description="Store chain type"),
        SchemaField("scraped_at", "TIMESTAMP", mode="REQUIRED", description="When data was scraped"),
        SchemaField("loaded_at", "TIMESTAMP", mode="REQUIRED", description="When data was loaded to BigQuery"),
    ]
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        dataset_id: str = "makoisa_ai",
        table_id: str = "stores",
        credentials_path: Optional[str] = None,
    ):
        """Initialize BigQuery loader.
        
        Args:
            project_id: Google Cloud project ID. If None, will be auto-detected.
            dataset_id: BigQuery dataset ID (default: 'makoisa_ai')
            table_id: BigQuery table ID (default: 'stores')
            credentials_path: Path to service account JSON file. If None, uses default credentials.
        """
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        
        # Set up authentication
        if credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        
        try:
            self.client = bigquery.Client(project=project_id)
            if not self.project_id:
                self.project_id = self.client.project
                logger.info(f"Auto-detected project ID: {self.project_id}")
        except DefaultCredentialsError:
            logger.error(
                "Google Cloud credentials not found. Please set up authentication:\n"
                "1. Install gcloud CLI: https://cloud.google.com/sdk/docs/install\n"
                "2. Run: gcloud auth application-default login\n"
                "3. Or set GOOGLE_APPLICATION_CREDENTIALS environment variable"
            )
            raise
        
        self.dataset_ref = self.client.dataset(self.dataset_id)
        self.table_ref = self.dataset_ref.table(self.table_id)
        
    def _ensure_dataset_exists(self) -> None:
        """Create dataset if it doesn't exist."""
        try:
            self.client.get_dataset(self.dataset_ref)
            logger.info(f"Dataset {self.dataset_id} already exists")
        except Exception:
            dataset = bigquery.Dataset(self.dataset_ref)
            dataset.location = "US"  # Default location
            dataset.description = "Makoisa AI store data scraped from s-kaupat.fi"
            
            dataset = self.client.create_dataset(dataset, timeout=30)
            logger.info(f"Created dataset {self.dataset_id}")
    
    def _ensure_table_exists(self) -> None:
        """Create table if it doesn't exist."""
        try:
            self.client.get_table(self.table_ref)
            logger.info(f"Table {self.table_id} already exists")
        except Exception:
            table = bigquery.Table(self.table_ref, schema=self.TABLE_SCHEMA)
            table.description = "Store data scraped from S-kaupat.fi for Makoisa AI"
            
            table = self.client.create_table(table, timeout=30)
            logger.info(f"Created table {self.table_id}")
    
    def _prepare_data(self, stores: List[Dict[str, Any]]) -> pd.DataFrame:
        """Prepare store data for BigQuery loading.
        
        Args:
            stores: List of store dictionaries
            
        Returns:
            DataFrame ready for BigQuery loading
        """
        if not stores:
            raise ValueError("No stores data provided")
        
        # Create DataFrame
        df = pd.DataFrame(stores)
        
        # Add loaded_at timestamp
        df["loaded_at"] = datetime.now(timezone.utc)
        
        # Ensure scraped_at is datetime
        if "scraped_at" in df.columns:
            df["scraped_at"] = pd.to_datetime(df["scraped_at"], utc=True)
        else:
            df["scraped_at"] = datetime.now(timezone.utc)
        
        # Ensure services is a list (for REPEATED field)
        if "services" not in df.columns:
            df["services"] = [[] for _ in range(len(df))]
        else:
            # Convert services to list if it's not already
            df["services"] = df["services"].apply(
                lambda x: x if isinstance(x, list) else [x] if x else []
            )
        
        # Validate required fields
        required_fields = ["name", "store_type"]
        for field in required_fields:
            if field not in df.columns:
                raise ValueError(f"Required field '{field}' missing from data")
            if df[field].isnull().any():
                raise ValueError(f"Required field '{field}' has null values")
        
        logger.info(f"Prepared {len(df)} rows for loading")
        return df
    
    def load_stores(
        self,
        stores: List[Dict[str, Any]],
        write_disposition: str = WriteDisposition.WRITE_APPEND,
        create_if_needed: bool = True,
    ) -> bigquery.LoadJob:
        """Load store data into BigQuery.
        
        Args:
            stores: List of store dictionaries
            write_disposition: How to handle existing data ('WRITE_APPEND', 'WRITE_TRUNCATE', 'WRITE_EMPTY')
            create_if_needed: Whether to create dataset/table if they don't exist
            
        Returns:
            BigQuery load job
        """
        if create_if_needed:
            self._ensure_dataset_exists()
            self._ensure_table_exists()
        
        # Prepare data
        df = self._prepare_data(stores)
        
        # Configure load job
        job_config = LoadJobConfig(
            schema=self.TABLE_SCHEMA,
            write_disposition=write_disposition,
            source_format=bigquery.SourceFormat.PARQUET,  # Use Parquet for efficiency
        )
        
        # Load data
        logger.info(f"Loading {len(df)} stores to {self.project_id}.{self.dataset_id}.{self.table_id}")
        job = self.client.load_table_from_dataframe(
            df, self.table_ref, job_config=job_config
        )
        
        # Wait for job to complete
        job.result()
        
        if job.error_result:
            logger.error(f"Load job failed: {job.error_result}")
            raise RuntimeError(f"BigQuery load job failed: {job.error_result}")
        
        logger.info(f"Successfully loaded {job.output_rows} rows")
        return job
    
    def load_from_file(
        self,
        file_path: str,
        write_disposition: str = WriteDisposition.WRITE_APPEND,
        create_if_needed: bool = True,
    ) -> bigquery.LoadJob:
        """Load store data from JSON file into BigQuery.
        
        Args:
            file_path: Path to JSON file containing store data
            write_disposition: How to handle existing data
            create_if_needed: Whether to create dataset/table if they don't exist
            
        Returns:
            BigQuery load job
        """
        with open(file_path, "r", encoding="utf-8") as f:
            stores = json.load(f)
        
        return self.load_stores(stores, write_disposition, create_if_needed)
    
    def query_stores(
        self,
        limit: Optional[int] = None,
        store_type: Optional[str] = None,
        city: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Query stores from BigQuery.
        
        Args:
            limit: Maximum number of rows to return
            store_type: Filter by store type
            city: Filter by city
            
        Returns:
            List of store dictionaries
        """
        query = f"""
        SELECT * FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
        WHERE 1=1
        """
        
        if store_type:
            query += f" AND store_type = '{store_type}'"
        
        if city:
            query += f" AND LOWER(city) = LOWER('{city}')"
        
        query += " ORDER BY scraped_at DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        logger.info(f"Executing query: {query}")
        
        query_job = self.client.query(query)
        results = query_job.result()
        
        return [dict(row) for row in results]
    
    def get_table_info(self) -> Dict[str, Any]:
        """Get information about the BigQuery table.
        
        Returns:
            Dictionary with table information
        """
        try:
            table = self.client.get_table(self.table_ref)
            return {
                "project_id": table.project,
                "dataset_id": table.dataset_id,
                "table_id": table.table_id,
                "num_rows": table.num_rows,
                "num_bytes": table.num_bytes,
                "created": table.created.isoformat() if table.created else None,
                "modified": table.modified.isoformat() if table.modified else None,
                "schema": [
                    {
                        "name": field.name,
                        "type": field.field_type,
                        "mode": field.mode,
                        "description": field.description,
                    }
                    for field in table.schema
                ],
            }
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            raise


class ProductBigQueryLoader:
    """Load scraped product data into BigQuery."""
    PRODUCT_TABLE_SCHEMA = [
        SchemaField("name", "STRING", mode="REQUIRED", description="Product name"),
        SchemaField("price", "STRING", mode="NULLABLE", description="Product price (as string)"),
        SchemaField("description", "STRING", mode="NULLABLE", description="Product description"),
        SchemaField("url", "STRING", mode="REQUIRED", description="Product URL"),
        SchemaField("scraped_at", "TIMESTAMP", mode="REQUIRED", description="When data was scraped"),
        SchemaField("source", "STRING", mode="NULLABLE", description="Scraping source (browser/api)")
    ]

    def __init__(
        self,
        project_id: Optional[str] = None,
        dataset_id: str = "makoisa_ai",
        table_id: str = "products",
        credentials_path: Optional[str] = None,
    ):
        """Initialize Product BigQuery loader.
        
        Args:
            project_id: Google Cloud project ID. If None, will be auto-detected.
            dataset_id: BigQuery dataset ID (default: 'makoisa_ai')
            table_id: BigQuery table ID (default: 'products')
            credentials_path: Path to service account JSON file. If None, uses default credentials.
        """
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        
        # Set up authentication
        if credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        
        try:
            self.client = bigquery.Client(project=project_id)
            if not self.project_id:
                self.project_id = self.client.project
                logger.info(f"Auto-detected project ID: {self.project_id}")
        except DefaultCredentialsError:
            logger.error(
                "Google Cloud credentials not found. Please set up authentication:\n"
                "1. Install gcloud CLI: https://cloud.google.com/sdk/docs/install\n"
                "2. Run: gcloud auth application-default login\n"
                "3. Or set GOOGLE_APPLICATION_CREDENTIALS environment variable"
            )
            raise
        
        self.dataset_ref = self.client.dataset(self.dataset_id)
        self.table_ref = self.dataset_ref.table(self.table_id)

    def _ensure_dataset_exists(self) -> None:
        """Create dataset if it doesn't exist."""
        try:
            self.client.get_dataset(self.dataset_ref)
            logger.info(f"Dataset {self.dataset_id} already exists")
        except Exception:
            dataset = bigquery.Dataset(self.dataset_ref)
            dataset.location = "US"  # Default location
            dataset.description = "Makoisa AI product data scraped from s-kaupat.fi"
            
            dataset = self.client.create_dataset(dataset, timeout=30)
            logger.info(f"Created dataset {self.dataset_id}")
    
    def _ensure_table_exists(self) -> None:
        """Create table if it doesn't exist."""
        try:
            self.client.get_table(self.table_ref)
            logger.info(f"Table {self.table_id} already exists")
        except Exception:
            table = bigquery.Table(self.table_ref, schema=self.PRODUCT_TABLE_SCHEMA)
            table.description = "Product data scraped from S-kaupat.fi for Makoisa AI"
            
            table = self.client.create_table(table, timeout=30)
            logger.info(f"Created table {self.table_id}")
    
    def _prepare_data(self, products: List[Dict[str, Any]]) -> pd.DataFrame:
        """Prepare product data for BigQuery loading.
        
        Args:
            products: List of product dictionaries
            
        Returns:
            DataFrame ready for BigQuery loading
        """
        if not products:
            raise ValueError("No product data provided")
        
        # Create DataFrame
        df = pd.DataFrame(products)
        
        # Ensure scraped_at is datetime
        if "scraped_at" in df.columns:
            df["scraped_at"] = pd.to_datetime(df["scraped_at"], utc=True, errors="coerce")
        else:
            df["scraped_at"] = datetime.now(timezone.utc)
        
        return df
    
    def load_products(
        self,
        products: List[Dict[str, Any]],
        write_disposition: str = WriteDisposition.WRITE_APPEND,
        create_if_needed: bool = True,
    ) -> bigquery.LoadJob:
        """Load product data into BigQuery.
        
        Args:
            products: List of product dictionaries
            write_disposition: How to handle existing data ('WRITE_APPEND', 'WRITE_TRUNCATE', 'WRITE_EMPTY')
            create_if_needed: Whether to create dataset/table if they don't exist
            
        Returns:
            BigQuery load job
        """
        if create_if_needed:
            self._ensure_dataset_exists()
            self._ensure_table_exists()
        
        # Prepare data
        df = self._prepare_data(products)
        
        # Configure load job
        job_config = LoadJobConfig(
            schema=self.PRODUCT_TABLE_SCHEMA,
            write_disposition=write_disposition,
            source_format=bigquery.SourceFormat.PARQUET,  # Use Parquet for efficiency
        )
        
        # Load data
        logger.info(f"Loading {len(df)} products to {self.project_id}.{self.dataset_id}.{self.table_id}")
        job = self.client.load_table_from_dataframe(
            df, self.table_ref, job_config=job_config
        )
        
        # Wait for job to complete
        job.result()
        
        if job.error_result:
            logger.error(f"Load job failed: {job.error_result}")
            raise RuntimeError(f"BigQuery load job failed: {job.error_result}")
        
        logger.info(f"Successfully loaded {job.output_rows} product rows")
        return job
    
    def load_from_file(
        self,
        file_path: str,
        write_disposition: str = WriteDisposition.WRITE_APPEND,
        create_if_needed: bool = True,
    ) -> bigquery.LoadJob:
        """Load product data from JSON file into BigQuery.
        
        Args:
            file_path: Path to JSON file containing product data
            write_disposition: How to handle existing data
            create_if_needed: Whether to create dataset/table if they don't exist
            
        Returns:
            BigQuery load job
        """
        with open(file_path, "r", encoding="utf-8") as f:
            products = json.load(f)
        
        return self.load_products(products, write_disposition, create_if_needed)


def load_stores_to_bigquery(
    stores: List[Dict[str, Any]],
    project_id: Optional[str] = None,
    dataset_id: str = "makoisa_ai",
    table_id: str = "stores",
    credentials_path: Optional[str] = None,
    write_disposition: str = WriteDisposition.WRITE_APPEND,
) -> bigquery.LoadJob:
    """Convenience function to load stores to BigQuery.
    
    Args:
        stores: List of store dictionaries
        project_id: Google Cloud project ID
        dataset_id: BigQuery dataset ID
        table_id: BigQuery table ID
        credentials_path: Path to service account JSON file
        write_disposition: How to handle existing data
        
    Returns:
        BigQuery load job
    """
    loader = BigQueryLoader(
        project_id=project_id,
        dataset_id=dataset_id,
        table_id=table_id,
        credentials_path=credentials_path,
    )
    
    return loader.load_stores(stores, write_disposition=write_disposition)


def load_products_to_bigquery(
    products: List[Dict[str, Any]],
    project_id: Optional[str] = None,
    dataset_id: str = "makoisa_ai",
    table_id: str = "products",
    credentials_path: Optional[str] = None,
    write_disposition: str = WriteDisposition.WRITE_APPEND,
) -> bigquery.LoadJob:
    """Convenience function to load products to BigQuery.
    
    Args:
        products: List of product dictionaries
        project_id: Google Cloud project ID
        dataset_id: BigQuery dataset ID
        table_id: BigQuery table ID
        credentials_path: Path to service account JSON file
        write_disposition: How to handle existing data
        
    Returns:
        BigQuery load job
    """
    loader = ProductBigQueryLoader(
        project_id=project_id,
        dataset_id=dataset_id,
        table_id=table_id,
        credentials_path=credentials_path,
    )
    
    return loader.load_products(products, write_disposition=write_disposition)


def load_rows(data: Union[List[Dict], str], **kwargs) -> bigquery.LoadJob:
    """Legacy function to maintain compatibility with __init__.py export.
    
    Args:
        data: Store data (list of dicts) or path to JSON file
        **kwargs: Additional arguments for BigQueryLoader
        
    Returns:
        BigQuery load job
    """
    if isinstance(data, str):
        # Assume it's a file path
        loader = BigQueryLoader(**kwargs)
        return loader.load_from_file(data)
    else:
        # Assume it's store data
        return load_stores_to_bigquery(data, **kwargs)


def load_product_rows(data: Union[List[Dict], str], **kwargs) -> bigquery.LoadJob:
    """Legacy function to maintain compatibility with __init__.py export.
    
    Args:
        data: Product data (list of dicts) or path to JSON file
        **kwargs: Additional arguments for ProductBigQueryLoader
        
    Returns:
        BigQuery load job
    """
    if isinstance(data, str):
        # Assume it's a file path
        loader = ProductBigQueryLoader(**kwargs)
        return loader.load_from_file(data)
    else:
        # Assume it's product data
        return load_products_to_bigquery(data, **kwargs)
