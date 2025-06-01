# Use Python 3.12 slim image for smaller size
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy poetry files
COPY pyproject.toml poetry.lock* ./

# Configure poetry: don't create a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --only=main --no-interaction --no-ansi --no-root

# Copy application code
COPY . .

# Create a non-root user and set ownership
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app

# Install Playwright dependencies as root (system packages)
RUN playwright install-deps chromium

# Switch to app user
USER app

# Install Playwright browsers as app user so they're in the right location
RUN playwright install chromium

# Expose port for Cloud Run
EXPOSE 8080

# Default command - run the web server
CMD ["python", "server.py"]
