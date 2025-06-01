# Ruokahinta

A comprehensive end-to-end solution for scraping Finnish grocery store data and loading it into Google BigQuery.

## Overview

This project scrapes grocery store data from Finnish grocery delivery services and provides tools to extract, transform, and load the data into BigQuery for analysis. The scraper extracts information about individual stores across 7 different store chains.

## Features

- **Multi-chain support**: Scrapes 7 different store types (Prisma, S-market, Alepa, Sale, Food Market Herkku, Sokos Herkku, Mestarin Herkku)
- **Comprehensive data extraction**: Store names, addresses, cities, postal codes, operating hours, and services
- **Multiple output formats**: JSON and CSV export
- **Filtering capabilities**: Filter by store type, limit results
- **CLI interface**: Easy-to-use command-line interface with multiple commands
- **Rate limiting**: Respectful scraping with built-in delays
- **Error handling**: Robust error handling and logging
- **Test coverage**: Comprehensive unit tests

## Store Types Supported

The scraper extracts data from 7 different Finnish grocery store chains:

| Store Type | Count | Description |
|------------|-------|-------------|
| Prisma | ~20 stores | Large hypermarkets |
| S-market | ~20 stores | Supermarkets |
| Alepa | ~20 stores | Convenience stores |
| Sale | ~20 stores | Discount stores |
| Food Market Herkku | 1 store | Gourmet food market |
| Sokos Herkku | 1 store | Department store food section |
| Mestarin Herkku | 1 store | Master chef's gourmet market |

**Total: ~83 individual stores**

## Project Structure

```
ruokahinta/
├── scraper/           # Core scraping functionality
│   ├── __init__.py    # Module exports
│   ├── main.py        # Main scraper implementation
│   ├── selectors.py   # CSS selectors for web scraping
│   └── cli.py         # Command-line interface
├── loader/            # BigQuery loader (Phase 3)
│   └── __init__.py
├── infra/             # Infrastructure as Code (Phase 5)
├── tests/             # Test suite
│   └── test_scraper_updated.py
├── pyproject.toml     # Poetry dependencies
└── README.md          # This file
```

## Installation

1. **Prerequisites**
   - Python 3.12+
   - Poetry (Python dependency manager)

2. **Clone the repository**
   ```bash
   git clone https://github.com/juntunen-ai/ruokahinta.git
   cd ruokahinta
   ```

3. **Install dependencies**
   ```bash
   poetry install
   ```

4. **Install Playwright browsers**
   ```bash
   poetry run playwright install
   ```

## Usage

### Command Line Interface

The scraper provides a comprehensive CLI with multiple commands:

#### Scrape stores
```bash
# Scrape all stores (default: headless browser, JSON output)
poetry run python -m scraper.cli scrape

# Scrape with visible browser
poetry run python -m scraper.cli scrape --browser visible

# Scrape specific store types
poetry run python -m scraper.cli scrape --store-types prisma,alepa

# Limit number of results
poetry run python -m scraper.cli scrape --limit 5

# Export to CSV
poetry run python -m scraper.cli scrape --format csv --output stores.csv

# Verbose output
poetry run python -m scraper.cli scrape --verbose
```

#### Available CLI Commands

1. **scrape**: Main scraping command
   - `--browser`: Browser mode (headless/visible, default: headless)
   - `--output`: Output file path (default: stdout)
   - `--format`: Output format (json/csv, default: json)
   - `--limit`: Limit number of stores to scrape
   - `--store-types`: Comma-separated list of store types to scrape
   - `--verbose`: Enable verbose logging
   - `--quiet`: Suppress all output except errors

2. **validate**: Validate scraped data structure
   ```bash
   poetry run python -m scraper.cli validate scraped_stores.json
   ```

3. **version**: Display version information
   ```bash
   poetry run python -m scraper.cli version
   ```

### Python API

```python
from scraper.main import StoreScraper

# Initialize scraper
scraper = StoreScraper(browser_type="headless")

# Scrape all stores
stores = scraper.scrape_all_stores()

# Scrape specific store types
stores = scraper.scrape_all_stores(store_types=["prisma", "alepa"])
```

## Data Schema

Each scraped store contains the following fields:

```json
{
  "name": "Store Name",
  "address": "Street Address",
  "city": "City Name",
  "postal_code": "12345",
  "hours": "Mon-Fri 8-21, Sat 8-18, Sun 10-18",
  "services": ["Pickup", "Delivery", "Pharmacy"],
  "store_type": "prisma",
  "scraped_at": "2024-01-15T10:30:00"
}
```

## Development

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=scraper

# Run specific test file
poetry run pytest tests/test_scraper_updated.py -v
```

### Code Formatting

```bash
# Format code with Black
poetry run black scraper/ loader/ tests/

# Type checking with MyPy
poetry run mypy scraper/ loader/
```

## Project Roadmap

This project follows a development roadmap:

- ✅ **Phase 1**: Repository bootstrap
- ✅ **Phase 2**: Scraper micro-service
- ✅ **Phase 3**: BigQuery loader micro-service
- ✅ **Phase 4**: Container & Cloud Run deployment
- ~~**Phase 5**: Infrastructure-as-Code with Terraform~~ (Skipped - deployment script sufficient)
- ✅ **Phase 6**: CI/CD with GitHub Actions
- ✅ **Phase 7**: Observability and monitoring
- ⏳ **Phase 8**: Hardening and cost optimization

## Cloud Run Deployment (Phase 4)

The application can be deployed to Google Cloud Run as a containerized REST API service.

### Quick Deploy
```bash
# Deploy to Cloud Run (requires gcloud CLI)
./deploy.sh your-project-id europe-north1
```

### Local Development
```bash
# Start local development server
./dev.sh

# Or with Docker Compose
docker-compose up
```

### API Endpoints

Once deployed, the service provides these REST API endpoints:

- `GET /` - Service health and information
- `GET /health` - Detailed health check
- `GET /stores` - Scrape stores with filtering options
- `GET /store-types` - List available store types
- `POST /bigquery/load` - Scrape and load data to BigQuery
- `GET /bigquery/query` - Query stores from BigQuery
- `GET /bigquery/info` - BigQuery dataset information

### Example API Usage
```bash
# Get service info
curl https://your-service.run.app/

# Scrape 5 Prisma stores
curl "https://your-service.run.app/stores?store_type=prisma&limit=5"

# Load data to BigQuery
curl -X POST "https://your-service.run.app/bigquery/load"

# Query BigQuery data
curl "https://your-service.run.app/bigquery/query?city=Helsinki&limit=10"
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This code is released under the [PolyForm Noncommercial License 1.0.0](./LICENSE).  
**Commercial use requires a separate agreement.**  
Contact <vihreamies.juntunen@gmail.com> for enquiries.

## Acknowledgments

- Finnish grocery delivery services for providing the store data
- Playwright for reliable web scraping capabilities
- Poetry for dependency management