# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    gcc \
    g++ \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Verify critical dependencies are installed
RUN python -c "import flask, werkzeug, psycopg2, redis, celery, openai; print('Core dependencies verified')"

# Install Playwright browsers for web scraping
RUN playwright install chromium && \
    playwright install-deps chromium

# Copy application code and startup script
COPY . .
COPY start.sh /app/start.sh

# Create necessary directories
RUN mkdir -p logs data/raw data/processed data/embeddings

# Set proper permissions
RUN chmod +x /app/start.sh && \
    chmod +x scripts/*.py && \
    chmod -R 755 logs data

# Expose port
EXPOSE 5000

# Add health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run the application using the startup script
CMD ["/app/start.sh"]