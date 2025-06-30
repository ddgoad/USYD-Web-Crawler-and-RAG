#!/bin/bash

# Startup script for USYD Web Crawler and RAG application
# This script ensures proper initialization and provides better error handling

set -e  # Exit on any error

echo "🚀 Starting USYD Web Crawler and RAG Application..."

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs data/raw data/processed data/embeddings

# Set proper permissions
echo "🔧 Setting proper permissions..."
chmod -R 755 logs data

# Verify Python environment
echo "🐍 Verifying Python environment..."
python --version
pip --version

# Test critical imports
echo "📦 Testing critical dependencies..."
python -c "
import sys
print('Python path:', sys.path)

try:
    import flask
    print('✓ Flask imported successfully')
except ImportError as e:
    print('❌ Flask import failed:', e)
    sys.exit(1)

try:
    import werkzeug
    print('✓ Werkzeug imported successfully')
except ImportError as e:
    print('❌ Werkzeug import failed:', e)
    sys.exit(1)

try:
    import psycopg2
    print('✓ Psycopg2 imported successfully')
except ImportError as e:
    print('❌ Psycopg2 import failed:', e)
    sys.exit(1)

try:
    import redis
    print('✓ Redis imported successfully')
except ImportError as e:
    print('❌ Redis import failed:', e)
    sys.exit(1)

try:
    import openai
    print('✓ OpenAI imported successfully')
except ImportError as e:
    print('❌ OpenAI import failed:', e)
    sys.exit(1)

try:
    import gunicorn
    print('✓ Gunicorn imported successfully')
except ImportError as e:
    print('❌ Gunicorn import failed:', e)
    sys.exit(1)

print('All critical dependencies verified successfully!')
"

# Test database connectivity (non-blocking)
echo "🗄️ Testing database connectivity..."
python -c "
import os
import sys

database_url = os.getenv('DATABASE_URL', '')
if database_url:
    print(f'Database URL configured: {database_url[:20]}...')
    try:
        if database_url.startswith('postgresql'):
            import psycopg2
            # Just test if we can parse the URL, don't actually connect yet
            print('✓ PostgreSQL driver available')
        else:
            print('✓ Using SQLite (default)')
    except Exception as e:
        print(f'⚠️  Database test warning: {e}')
else:
    print('⚠️  No DATABASE_URL configured, will use SQLite default')
"

# Test Redis connectivity (non-blocking)
echo "📡 Testing Redis connectivity..."
python -c "
import os
import sys

redis_url = os.getenv('REDIS_URL', '')
if redis_url:
    print(f'Redis URL configured: {redis_url[:20]}...')
    try:
        import redis
        print('✓ Redis client available')
    except Exception as e:
        print(f'⚠️  Redis test warning: {e}')
else:
    print('⚠️  No REDIS_URL configured, will use default')
"

# Environment validation
echo "🌍 Validating environment configuration..."
python -c "
import os

required_vars = ['PORT', 'FLASK_ENV']
optional_vars = ['DATABASE_URL', 'REDIS_URL', 'AZURE_OPENAI_ENDPOINT', 'AZURE_OPENAI_KEY']

print('Required environment variables:')
for var in required_vars:
    value = os.getenv(var, 'NOT SET')
    status = '✓' if value != 'NOT SET' else '❌'
    print(f'  {status} {var}: {value}')

print('Optional environment variables:')
for var in optional_vars:
    value = os.getenv(var, 'NOT SET')
    status = '✓' if value != 'NOT SET' else '⚠️ '
    display_value = value[:20] + '...' if len(value) > 20 else value
    print(f'  {status} {var}: {display_value}')
"

# Start the application with Gunicorn
echo "🎯 Starting application with Gunicorn..."
echo "Using Gunicorn configuration: gunicorn.conf.py"
echo "WSGI entry point: app:create_app()"

# Check if gunicorn.conf.py exists
if [ ! -f "gunicorn.conf.py" ]; then
    echo "❌ gunicorn.conf.py not found!"
    exit 1
fi

# Start with Gunicorn
exec gunicorn -c gunicorn.conf.py "app:create_app()"
