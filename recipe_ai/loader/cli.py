"""CLI for BigQuery loader operations."""

import json
import logging
import click
from typing import Optional

from .main import BigQueryLoader, ProductBigQueryLoader


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """BigQuery loader for Makoisa AI store data."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    setup_logging(verbose)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--project-id', '-p', help='Google Cloud project ID')
@click.option('--dataset-id', '-d', default='makoisa_ai', help='BigQuery dataset ID')
@click.option('--table-id', '-t', default='stores', help='BigQuery table ID')
@click.option('--credentials', '-c', help='Path to service account JSON file')
@click.option('--mode', '-m', 
              type=click.Choice(['append', 'truncate', 'empty']),
              default='append',
              help='Write mode (append/truncate/empty)')
@click.option('--dry-run', is_flag=True, help='Validate data without loading')
@click.pass_context
def load(
    ctx: click.Context,
    file_path: str,
    project_id: Optional[str],
    dataset_id: str,
    table_id: str,
    credentials: Optional[str],
    mode: str,
    dry_run: bool,
) -> None:
    """Load store data from JSON file to BigQuery."""
    verbose = ctx.obj['verbose']
    
    # Map mode to BigQuery write disposition
    mode_mapping = {
        'append': 'WRITE_APPEND',
        'truncate': 'WRITE_TRUNCATE',
        'empty': 'WRITE_EMPTY',
    }
    write_disposition = mode_mapping[mode]
    
    try:
        # Read and validate data
        with open(file_path, 'r', encoding='utf-8') as f:
            stores = json.load(f)
        
        if not isinstance(stores, list):
            raise ValueError("JSON file must contain a list of stores")
        
        click.echo(f"Loaded {len(stores)} stores from {file_path}")
        
        if dry_run:
            click.echo("DRY RUN: Validating data structure...")
            # Validate by creating DataFrame without loading
            loader = BigQueryLoader(
                project_id=project_id,
                dataset_id=dataset_id,
                table_id=table_id,
                credentials_path=credentials,
            )
            df = loader._prepare_data(stores)
            click.echo(f"✓ Data validation successful: {len(df)} rows prepared")
            
            # Show sample data
            if verbose and len(df) > 0:
                click.echo("\nSample data:")
                click.echo(df.head().to_string())
            
            return
        
        # Create loader and load data
        loader = BigQueryLoader(
            project_id=project_id,
            dataset_id=dataset_id,
            table_id=table_id,
            credentials_path=credentials,
        )
        
        click.echo(f"Loading to {loader.project_id}.{dataset_id}.{table_id} (mode: {mode})")
        
        job = loader.load_stores(stores, write_disposition=write_disposition)
        
        click.echo(f"✓ Successfully loaded {job.output_rows} rows")
        click.echo(f"Job ID: {job.job_id}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        raise click.ClickException(str(e))


@cli.command()
@click.option('--project-id', '-p', help='Google Cloud project ID')
@click.option('--dataset-id', '-d', default='makoisa_ai', help='BigQuery dataset ID')
@click.option('--table-id', '-t', default='stores', help='BigQuery table ID')
@click.option('--credentials', '-c', help='Path to service account JSON file')
@click.option('--limit', '-l', type=int, help='Limit number of results')
@click.option('--store-type', '-s', help='Filter by store type')
@click.option('--city', help='Filter by city')
@click.option('--output', '-o', help='Output file (JSON format)')
@click.pass_context
def query(
    ctx: click.Context,
    project_id: Optional[str],
    dataset_id: str,
    table_id: str,
    credentials: Optional[str],
    limit: Optional[int],
    store_type: Optional[str],
    city: Optional[str],
    output: Optional[str],
) -> None:
    """Query stores from BigQuery."""
    verbose = ctx.obj['verbose']
    
    try:
        loader = BigQueryLoader(
            project_id=project_id,
            dataset_id=dataset_id,
            table_id=table_id,
            credentials_path=credentials,
        )
        
        click.echo(f"Querying {loader.project_id}.{dataset_id}.{table_id}")
        
        stores = loader.query_stores(
            limit=limit,
            store_type=store_type,
            city=city,
        )
        
        click.echo(f"Found {len(stores)} stores")
        
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(stores, f, indent=2, default=str)
            click.echo(f"Results saved to {output}")
        else:
            if verbose:
                click.echo(json.dumps(stores, indent=2, default=str))
            else:
                for store in stores[:5]:  # Show first 5 stores
                    click.echo(f"- {store.get('name', 'N/A')} ({store.get('store_type', 'N/A')}) in {store.get('city', 'N/A')}")
                if len(stores) > 5:
                    click.echo(f"... and {len(stores) - 5} more stores")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        raise click.ClickException(str(e))


@cli.command()
@click.option('--project-id', '-p', help='Google Cloud project ID')
@click.option('--dataset-id', '-d', default='makoisa_ai', help='BigQuery dataset ID')
@click.option('--table-id', '-t', default='stores', help='BigQuery table ID')
@click.option('--credentials', '-c', help='Path to service account JSON file')
@click.pass_context
def info(
    ctx: click.Context,
    project_id: Optional[str],
    dataset_id: str,
    table_id: str,
    credentials: Optional[str],
) -> None:
    """Get information about the BigQuery table."""
    verbose = ctx.obj['verbose']
    
    try:
        loader = BigQueryLoader(
            project_id=project_id,
            dataset_id=dataset_id,
            table_id=table_id,
            credentials_path=credentials,
        )
        
        info = loader.get_table_info()
        
        click.echo(f"Table: {info['project_id']}.{info['dataset_id']}.{info['table_id']}")
        click.echo(f"Rows: {info['num_rows']:,}")
        click.echo(f"Size: {info['num_bytes']:,} bytes")
        click.echo(f"Created: {info['created']}")
        click.echo(f"Modified: {info['modified']}")
        
        if verbose:
            click.echo("\nSchema:")
            for field in info['schema']:
                mode = f" ({field['mode']})" if field['mode'] != 'NULLABLE' else ""
                desc = f" - {field['description']}" if field['description'] else ""
                click.echo(f"  {field['name']}: {field['type']}{mode}{desc}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        raise click.ClickException(str(e))


@cli.command()
@click.option('--project-id', '-p', help='Google Cloud project ID')
@click.option('--dataset-id', '-d', default='makoisa_ai', help='BigQuery dataset ID')
@click.option('--table-id', '-t', default='stores', help='BigQuery table ID')
@click.option('--credentials', '-c', help='Path to service account JSON file')
@click.pass_context
def setup(
    ctx: click.Context,
    project_id: Optional[str],
    dataset_id: str,
    table_id: str,
    credentials: Optional[str],
) -> None:
    """Create BigQuery dataset and table if they don't exist."""
    verbose = ctx.obj['verbose']
    
    try:
        loader = BigQueryLoader(
            project_id=project_id,
            dataset_id=dataset_id,
            table_id=table_id,
            credentials_path=credentials,
        )
        
        click.echo(f"Setting up {loader.project_id}.{dataset_id}.{table_id}")
        
        loader._ensure_dataset_exists()
        loader._ensure_table_exists()
        
        click.echo("✓ Setup complete")
        
        # Show info
        info = loader.get_table_info()
        click.echo(f"Table ready: {info['num_rows']:,} rows")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        raise click.ClickException(str(e))


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--project-id', '-p', help='Google Cloud project ID')
@click.option('--dataset-id', '-d', default='makoisa_ai', help='BigQuery dataset ID')
@click.option('--table-id', '-t', default='products', help='BigQuery table ID')
@click.option('--credentials', '-c', help='Path to service account JSON file')
@click.option('--mode', '-m', 
              type=click.Choice(['append', 'truncate', 'empty']),
              default='append',
              help='Write mode (append/truncate/empty)')
@click.option('--dry-run', is_flag=True, help='Validate data without loading')
@click.pass_context
def load_products(
    ctx: click.Context,
    file_path: str,
    project_id: Optional[str],
    dataset_id: str,
    table_id: str,
    credentials: Optional[str],
    mode: str,
    dry_run: bool,
) -> None:
    """Load product data from JSON file to BigQuery."""
    verbose = ctx.obj['verbose']
    mode_mapping = {
        'append': 'WRITE_APPEND',
        'truncate': 'WRITE_TRUNCATE',
        'empty': 'WRITE_EMPTY',
    }
    write_disposition = mode_mapping[mode]
    loader = ProductBigQueryLoader(
        project_id=project_id,
        dataset_id=dataset_id,
        table_id=table_id,
        credentials_path=credentials,
    )
    if dry_run:
        click.echo(f"[DRY RUN] Would upload products from {file_path} to {dataset_id}.{table_id}")
        return
    click.echo(f"Uploading products from {file_path} to {dataset_id}.{table_id} ...")
    job = loader.load_from_file(file_path, write_disposition=write_disposition)
    click.echo(f"✅ Upload complete! {job.output_rows} rows loaded.")


if __name__ == '__main__':
    cli()
