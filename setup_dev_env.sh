#!/bin/bash

# Makoisa AI Development Setup Script
# Version: 1.3.0-dev

set -e

echo "🚀 Setting up Makoisa AI Development Environment v1.3.0-dev"
echo "================================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3.11+ is available
print_status "Checking Python version..."
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ $(echo "$PYTHON_VERSION >= 3.11" | bc -l) -eq 1 ]]; then
        PYTHON_CMD="python3"
    else
        print_error "Python 3.11+ is required. Current version: $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3.11+ is not installed"
    exit 1
fi

print_success "Using Python: $($PYTHON_CMD --version)"

# Check if Poetry is installed
print_status "Checking Poetry installation..."
if ! command -v poetry &> /dev/null; then
    print_warning "Poetry not found. Installing Poetry..."
    curl -sSL https://install.python-poetry.org | $PYTHON_CMD -
    export PATH="$HOME/.local/bin:$PATH"
    
    if ! command -v poetry &> /dev/null; then
        print_error "Failed to install Poetry. Please install manually."
        exit 1
    fi
fi

print_success "Poetry is available: $(poetry --version)"

# Install dependencies
print_status "Installing development dependencies..."
poetry install --extras "dev commercial"

# Set up pre-commit hooks
print_status "Setting up pre-commit hooks..."
poetry run pre-commit install

# Create development directories
print_status "Creating development directories..."
mkdir -p dev_data dev_logs dev_cache dev_temp test_data

# Copy development environment file
print_status "Setting up development environment..."
if [ ! -f .env ]; then
    cp .env.development .env
    print_success "Created .env from development template"
else
    print_warning ".env already exists. Development template available as .env.development"
fi

# Create development database schema (if needed)
print_status "Setting up development database schema..."
# This would typically create development BigQuery datasets
# For now, we'll just create a placeholder script

cat > setup_dev_db.py << 'EOF'
#!/usr/bin/env python3
"""
Development Database Setup Script
Creates development BigQuery datasets and tables.
"""

import os
from google.cloud import bigquery
from dotenv import load_dotenv

def setup_dev_database():
    load_dotenv()
    
    project_id = os.getenv('BIGQUERY_PROJECT_ID')
    if not project_id:
        print("⚠️  BIGQUERY_PROJECT_ID not set in .env")
        return
    
    try:
        client = bigquery.Client(project=project_id)
        
        # Create development dataset
        dataset_id = os.getenv('BIGQUERY_DATASET_ID', 'makoisa_ai_dev')
        dataset_ref = client.dataset(dataset_id)
        
        try:
            client.get_dataset(dataset_ref)
            print(f"✅ Dataset {dataset_id} already exists")
        except:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"
            dataset.description = "Makoisa AI development data"
            client.create_dataset(dataset)
            print(f"✅ Created dataset {dataset_id}")
        
    except Exception as e:
        print(f"⚠️  Could not set up BigQuery: {e}")
        print("   Configure Google Cloud credentials to use BigQuery features")

if __name__ == "__main__":
    setup_dev_database()
EOF

chmod +x setup_dev_db.py

# Set up development services
print_status "Creating development service scripts..."

# API development server script
cat > dev_api.sh << 'EOF'
#!/bin/bash
# Start development API server

echo "🔧 Starting Makoisa AI API (Development Mode)"
export ENVIRONMENT=development
poetry run uvicorn server:app --reload --host localhost --port 8000
EOF

chmod +x dev_api.sh

# React UI development server script
cat > dev_ui.sh << 'EOF'
#!/bin/bash
# Start development UI server

echo "🎨 Starting Recipe UI (Development Mode)"
export ENVIRONMENT=development
cd recipe-ui
npm run dev
EOF

chmod +x dev_ui.sh

# Development testing script
cat > dev_test.sh << 'EOF'
#!/bin/bash
# Run development tests

echo "🧪 Running Development Tests"
export ENVIRONMENT=development

echo "Running unit tests..."
poetry run pytest tests/ -v --cov=./ --cov-report=html

echo "Running linting..."
poetry run black --check .
poetry run flake8 .

echo "Running type checking..."
poetry run mypy . --ignore-missing-imports

echo "✅ All development tests completed"
EOF

chmod +x dev_test.sh

# Create development documentation
print_status "Setting up development documentation..."

cat > DEV_GETTING_STARTED.md << 'EOF'
# Development Getting Started Guide

## Quick Start

1. **Run API Server**:
   ```bash
   ./dev_api.sh
   ```

2. **Run UI Server**:
   ```bash
   ./dev_ui.sh
   ```

3. **Run Tests**:
   ```bash
   ./dev_test.sh
   ```

## Development URLs

- **API Server**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Recipe AI**: http://localhost:8501

## Environment Setup

- Development config: `.env.development`
- Active config: `.env`
- Logs: `./dev_logs/`
- Data: `./dev_data/`

## Development Commands

```bash
# Install dependencies
poetry install --extras "dev commercial"

# Run specific tests
poetry run pytest tests/test_scraper.py -v

# Format code
poetry run black .

# Start services individually
poetry run uvicorn server:app --reload
cd recipe-ui && npm run dev

# Database setup
python3 setup_dev_db.py
```

## Debugging

1. Set `DEBUG=true` in `.env`
2. Use VS Code debugger with provided configurations
3. Check logs in `./dev_logs/`
4. Enable profiling with `ENABLE_PROFILING=true`
EOF

# Git hooks setup
print_status "Configuring Git hooks..."
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash
# Pre-push hook to run tests

echo "🔍 Running pre-push checks..."

# Run quick tests
poetry run pytest tests/ --maxfail=1 -q

# Check code formatting
poetry run black --check . --quiet

if [ $? -eq 0 ]; then
    echo "✅ Pre-push checks passed"
    exit 0
else
    echo "❌ Pre-push checks failed"
    exit 1
fi
EOF

chmod +x .git/hooks/pre-push

# Final setup completion
print_success "Development environment setup completed!"
echo ""
echo "📋 Next Steps:"
echo "  1. Configure your .env file with your credentials"
echo "  2. Run './dev_api.sh' to start the API server"
echo "  3. Run './dev_ui.sh' to start the UI interface"
echo "  4. Run './dev_test.sh' to verify everything works"
echo "  5. Read DEV_GETTING_STARTED.md for detailed instructions"
echo ""
echo "🌐 Development URLs:"
echo "  • API: http://localhost:8000"
echo "  • API Docs: http://localhost:8000/docs"
echo "  • Recipe AI: http://localhost:8501"
echo ""
echo "💡 Tips:"
echo "  • Check DEVELOPMENT_ROADMAP.md for planned features"
echo "  • Use 'poetry shell' to activate the virtual environment"
echo "  • Development logs are saved to ./dev_logs/"
echo ""
print_success "Happy developing! 🚀"
