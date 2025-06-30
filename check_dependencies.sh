#!/bin/bash
# Pre-deployment dependency check script

echo "🔍 Pre-deployment dependency validation..."
echo "=============================================="

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python version
echo "🐍 Checking Python version..."
python3 --version

# Check if pip is available
if ! command_exists pip; then
    echo "❌ pip is not installed"
    exit 1
fi

# Validate requirements.txt syntax
echo "📋 Validating requirements.txt syntax..."
if python3 validate_requirements.py; then
    echo "✅ Requirements validation passed"
else
    echo "❌ Requirements validation failed"
    exit 1
fi

# Check if all packages can be resolved (dry run)
echo "📦 Checking package availability..."
if pip install --dry-run --no-deps -r requirements.txt >/dev/null 2>&1; then
    echo "✅ All packages can be resolved"
else
    echo "❌ Some packages cannot be resolved"
    echo "Running detailed check..."
    pip install --dry-run --no-deps -r requirements.txt
    exit 1
fi

# Check Docker (for azd deployment)
echo "🐳 Checking Docker..."
if command_exists docker; then
    docker --version
    if docker info >/dev/null 2>&1; then
        echo "✅ Docker is running"
    else
        echo "⚠️  Docker is installed but not running"
    fi
else
    echo "❌ Docker is not installed"
fi

# Check Azure CLI
echo "☁️  Checking Azure CLI..."
if command_exists az; then
    az --version | head -1
    echo "✅ Azure CLI is available"
else
    echo "❌ Azure CLI is not installed"
fi

# Check AZD
echo "🚀 Checking Azure Developer CLI..."
if command_exists azd; then
    azd version
    echo "✅ Azure Developer CLI is available"
else
    echo "❌ Azure Developer CLI is not installed"
fi

echo "=============================================="
echo "✅ Pre-deployment checks completed!"
echo "You can now run: azd up"
