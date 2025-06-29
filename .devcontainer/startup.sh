#!/bin/bash

echo "🚀 Setting up USD RAG development environment..."

# Set the workspace folder name dynamically
WORKSPACE_NAME=$(basename "/workspaces/$(ls /workspaces/ | head -1)")
WORKSPACE_PATH="/workspaces/$WORKSPACE_NAME"

echo "📁 Working in: $WORKSPACE_PATH"

# Update system packages
echo "📦 Updating system packages..."
sudo apt-get update -qq

# Ensure pip is up to date
echo "🐍 Updating pip and essential tools..."
python -m pip install --upgrade pip setuptools wheel

# Install Python requirements
echo "📚 Installing Python requirements..."
if [ -f "$WORKSPACE_PATH/requirements.txt" ]; then
    pip install -r "$WORKSPACE_PATH/requirements.txt"
    echo "✅ Main requirements successfully installed!"
else
    echo "⚠️  Warning: requirements.txt file not found at $WORKSPACE_PATH/requirements.txt"
fi

# Install development requirements
echo "🛠️  Installing development requirements..."
if [ -f "$WORKSPACE_PATH/.devcontainer/requirements-dev.txt" ]; then
    pip install -r "$WORKSPACE_PATH/.devcontainer/requirements-dev.txt"
    echo "✅ Development requirements successfully installed!"
else
    echo "⚠️  Warning: requirements-dev.txt file not found"
fi

# Install and setup Playwright browsers
echo "🎭 Installing Playwright browsers..."
playwright install chromium firefox webkit
playwright install-deps

# Download spaCy language models
echo "📝 Downloading spaCy language models..."
python -m spacy download en_core_web_sm
python -m spacy download en_core_web_md

# Verify CLI tools installation
echo "☁️  Verifying Azure CLI..."
az version

echo "🔧 Verifying Azure Developer CLI..."
azd version

echo "🐙 Verifying GitHub CLI..."
gh version

# Set up Git configuration placeholders
echo "🔧 Setting up Git configuration..."
if [ -z "$(git config --global user.name)" ]; then
    echo "ℹ️  Git user.name not set. Set it with: git config --global user.name 'Your Name'"
fi
if [ -z "$(git config --global user.email)" ]; then
    echo "ℹ️  Git user.email not set. Set it with: git config --global user.email 'your.email@example.com'"
fi

# Create project directory structure
echo "📁 Creating USD RAG project directories..."
mkdir -p "$WORKSPACE_PATH/src"
mkdir -p "$WORKSPACE_PATH/src/crawlers"
mkdir -p "$WORKSPACE_PATH/src/processors"
mkdir -p "$WORKSPACE_PATH/src/embeddings"
mkdir -p "$WORKSPACE_PATH/src/retrieval"
mkdir -p "$WORKSPACE_PATH/src/generation"
mkdir -p "$WORKSPACE_PATH/src/api"
mkdir -p "$WORKSPACE_PATH/tests"
mkdir -p "$WORKSPACE_PATH/docs"
mkdir -p "$WORKSPACE_PATH/data/raw"
mkdir -p "$WORKSPACE_PATH/data/processed"
mkdir -p "$WORKSPACE_PATH/data/embeddings"
mkdir -p "$WORKSPACE_PATH/logs"
mkdir -p "$WORKSPACE_PATH/scripts"
mkdir -p "$WORKSPACE_PATH/configs"
mkdir -p "$WORKSPACE_PATH/notebooks"

# Set Python path
echo "🐍 Setting Python path..."
export PYTHONPATH="$WORKSPACE_PATH:$PYTHONPATH"
echo "export PYTHONPATH=\"$WORKSPACE_PATH:\$PYTHONPATH\"" >> ~/.bashrc

# Create sample configuration files
if [ ! -f "$WORKSPACE_PATH/.env" ]; then
    echo "📝 Creating sample .env file..."
    cat > "$WORKSPACE_PATH/.env" << EOF
# Azure Configuration
AZURE_SUBSCRIPTION_ID=
AZURE_TENANT_ID=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
AZURE_RESOURCE_GROUP=
AZURE_STORAGE_ACCOUNT=
AZURE_STORAGE_CONTAINER=
AZURE_SEARCH_SERVICE=
AZURE_SEARCH_INDEX=
AZURE_SEARCH_API_KEY=

# OpenAI Configuration
OPENAI_API_KEY=
OPENAI_ORG_ID=
OPENAI_MODEL=gpt-4

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_API_VERSION=2023-12-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=

# LangChain Configuration
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=
LANGCHAIN_PROJECT=usyd-rag

# Vector Database Configuration
CHROMA_HOST=localhost
CHROMA_PORT=8000
PINECONE_API_KEY=
PINECONE_ENVIRONMENT=

# Application Configuration
LOG_LEVEL=INFO
MAX_CONCURRENT_REQUESTS=10
REQUEST_DELAY=1
USER_AGENT=USYDRag/1.0

# Database Configuration
DATABASE_URL=
REDIS_URL=

# Web Interface Configuration
STREAMLIT_SERVER_PORT=8501
GRADIO_SERVER_PORT=7860
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
EOF
fi

# Create basic project structure files
if [ ! -f "$WORKSPACE_PATH/pyproject.toml" ]; then
    echo "📝 Creating pyproject.toml..."
    cat > "$WORKSPACE_PATH/pyproject.toml" << EOF
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "usyd-rag"
version = "0.1.0"
description = "USD Web Crawler and Retrieval Augmented Generation System"
authors = [{name = "USD RAG Team"}]
license = {text = "MIT"}
readme = "README.md"
requires-python = ">=3.11"
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
]

[project.urls]
Homepage = "https://github.com/yourusername/usyd-rag"
Documentation = "https://github.com/yourusername/usyd-rag/docs"
Repository = "https://github.com/yourusername/usyd-rag"

[tool.black]
line-length = 88
target-version = ['py311']

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
EOF
fi

# Create a basic README if it doesn't exist
if [ ! -f "$WORKSPACE_PATH/README.md" ]; then
    echo "📝 Creating README.md..."
    cat > "$WORKSPACE_PATH/README.md" << EOF
# USD RAG - Web Crawler and Retrieval Augmented Generation

A comprehensive system for web crawling, document processing, and retrieval-augmented generation (RAG) using Azure services and modern AI technologies.

## Features

- 🕷️ Advanced web crawling with multiple strategies
- 📄 Multi-format document processing (PDF, DOCX, HTML, etc.)
- 🔍 Intelligent text chunking and embedding generation
- 🏪 Multiple vector database support (Chroma, Pinecone, FAISS, etc.)
- 🤖 RAG-based question answering with multiple LLM providers
- ☁️ Azure integration for scalable deployment
- 🚀 FastAPI backend with Streamlit/Gradio frontends

## Quick Start

1. Copy \`.env.example\` to \`.env\` and configure your API keys
2. Install dependencies: \`pip install -r requirements.txt\`
3. Run the web interface: \`streamlit run src/app.py\`

## Development

This project uses a dev container for consistent development environments.
Open in VS Code and select "Reopen in Container" when prompted.

## Architecture

- \`src/crawlers/\` - Web crawling implementations
- \`src/processors/\` - Document processing and chunking
- \`src/embeddings/\` - Embedding generation and management
- \`src/retrieval/\` - Vector search and retrieval logic
- \`src/generation/\` - LLM-based response generation
- \`src/api/\` - FastAPI backend services

## License

MIT License
EOF
fi

echo "✨ USD RAG development environment setup complete!"
echo ""
echo "🔗 Quick start commands:"
echo "  - Install requirements: pip install -r requirements.txt"
echo "  - Run web interface: streamlit run src/app.py"
echo "  - Run API server: uvicorn src.api.main:app --reload"
echo "  - Run tests: pytest"
echo "  - Format code: black ."
echo "  - Type check: mypy src/"
echo ""
echo "📖 Next steps:"
echo "  - Configure your .env file with API keys and endpoints"
echo "  - Review the project structure in src/ directory"
echo "  - Check out the notebooks/ directory for examples"
echo "  - Set up Git configuration if needed"
echo ""
echo "🎯 Ready to build your RAG system!"