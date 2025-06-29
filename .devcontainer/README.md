# USD RAG Dev Container

This dev container provides a complete development environment for the USD RAG (Retrieval Augmented Generation) project, optimized for Python development, web scraping, AI/ML workloads, and Azure deployment.

## Features

### Base Environment
- **Python 3.11** with latest pip, setuptools, and wheel
- **Ubuntu/Debian** based container with AI/ML system dependencies
- **Docker-in-Docker** support for containerization tasks

### Development Tools
- **Azure CLI** - Azure command-line interface
- **Azure Developer CLI (azd)** - Modern Azure deployment tool
- **GitHub CLI** - GitHub command-line interface
- **Node.js LTS** - For frontend tooling and build processes

### AI/ML & RAG Stack
- **LangChain** - LLM application development framework
- **OpenAI & Azure OpenAI** - Large language model APIs
- **Transformers** - HuggingFace model library
- **Sentence Transformers** - Text embedding models
- **Multiple Vector Databases** - ChromaDB, FAISS, Pinecone, Weaviate, Qdrant
- **spaCy & NLTK** - Natural language processing

### Web Scraping & Document Processing
- **Playwright** - Modern browser automation (Chromium, Firefox, WebKit)
- **Selenium** - Traditional browser automation
- **BeautifulSoup4** - HTML/XML parsing
- **Trafilatura** - Web content extraction
- **PDF/Document Processing** - PyPDF2, pdfplumber, python-docx

### Web Frameworks & APIs
- **FastAPI** - Modern, fast web framework for building APIs
- **Streamlit** - Rapid web app development for ML/data science
- **Gradio** - Machine learning model interfaces
- **Flask** - Lightweight web framework for custom applications

### Azure Integration
- **Azure SDK** - Complete Azure service integration
- **Azure Cognitive Services** - AI/ML services integration
- **Azure Storage** - Blob and Data Lake storage support
- **Azure Search** - Cognitive search integration
- **Azure Cosmos DB** - NoSQL database support
- **Azure Key Vault** - Secrets management
- **Azure Monitor** - Logging and telemetry

### Data Processing & Analysis
- **Pandas** - Data manipulation and analysis
- **NumPy** - Numerical computing
- **Matplotlib/Seaborn** - Data visualization
- **OpenPyXL** - Excel file processing

### Development & Testing
- **pytest** - Advanced testing framework with async support
- **black** - Code formatting
- **isort** - Import sorting
- **flake8** - Code linting
- **mypy** - Type checking and static analysis
- **pre-commit** - Git hooks for code quality

## Quick Start

1. **Open in VS Code**: Open this folder in VS Code and click "Reopen in Container" when prompted.

2. **Wait for Setup**: The container will build and run the startup script automatically.

3. **Configure Environment**: 
   - Edit `.env` file with your API keys and configuration
   - Set up Git configuration if needed:
     ```bash
     git config --global user.name "Your Name"
     git config --global user.email "your.email@example.com"
     ```

4. **Start Development**: Your environment is ready! Common commands:
   ```bash
   # Run Streamlit web interface
   streamlit run src/app.py
   
   # Run FastAPI server
   uvicorn src.api.main:app --reload
   
   # Run tests
   pytest
   
   # Format code
   black . && isort .
   
   # Type check
   mypy src/
   
   # Install additional packages
   pip install package-name
   ```

## Project Structure

The startup script creates the following USD RAG project structure:
- `src/` - Source code with RAG components
  - `crawlers/` - Web crawling implementations
  - `processors/` - Document processing and chunking
  - `embeddings/` - Embedding generation and management
  - `retrieval/` - Vector search and retrieval logic
  - `generation/` - LLM-based response generation
  - `api/` - FastAPI backend services
- `tests/` - Test files
- `docs/` - Documentation
- `data/` - Data storage
  - `raw/` - Original crawled data
  - `processed/` - Processed documents
  - `embeddings/` - Vector embeddings
- `logs/` - Application logs
- `scripts/` - Utility scripts
- `configs/` - Configuration files
- `notebooks/` - Jupyter notebooks for experimentation

## AI/ML Model Support

Pre-configured for multiple AI providers:
- **OpenAI** - GPT-4, GPT-3.5, text-embedding-ada-002
- **Azure OpenAI** - Azure-hosted OpenAI models
- **Anthropic** - Claude models
- **HuggingFace** - Open-source models via Transformers
- **Local Models** - Support for local LLM inference

## Vector Database Support

Multiple vector database options:
- **ChromaDB** - Local vector database
- **FAISS** - Facebook AI Similarity Search
- **Pinecone** - Managed vector database
- **Weaviate** - Open-source vector database
- **Qdrant** - Vector similarity search engine

## Browser Support

Playwright browsers are pre-installed and configured:
- Chromium (optimized for scraping)
- Firefox
- WebKit (Safari engine)

## Azure Deployment Ready

This container is optimized for Azure deployment:
- Azure Container Apps support
- Azure Functions compatibility
- Pre-configured Azure tools and SDKs
- Environment variable and secrets management
- Azure Monitor integration

## Ports

The following ports are forwarded:
- `8000` - FastAPI server
- `8080` - Alternative API server
- `5000` - Flask server (if used)
- `3000` - Frontend development server
- `8501` - Streamlit interface
- `7860` - Gradio interface

## Volume Mounts and Caching

Optimized for AI/ML development:
- Workspace files mounted at `/workspaces/`
- Docker socket forwarded for container operations
- Pip cache persisted across rebuilds
- Playwright browser cache persisted
- HuggingFace model cache persisted
- Azure CLI cache persisted

## Environment Configuration

Key environment variables for USD RAG:
- **OPENAI_API_KEY** - OpenAI API access
- **AZURE_OPENAI_ENDPOINT** - Azure OpenAI service
- **LANGCHAIN_API_KEY** - LangSmith tracing
- **PINECONE_API_KEY** - Pinecone vector database
- **AZURE_SUBSCRIPTION_ID** - Azure resources

## Customization

- **Add AI models**: Update `requirements.txt` with new model libraries
- **Add vector databases**: Install additional vector database clients
- **Add scrapers**: Extend the crawlers directory
- **Add VS Code extensions**: Update `devcontainer.json`
- **Add system packages**: Update `Dockerfile`
- **Modify startup**: Update `startup.sh`

## Development Workflow

Recommended development workflow:
1. Configure `.env` with your API keys
2. Test crawling: `python scripts/example_crawl.py`
3. Generate embeddings: `python scripts/example_embeddings.py`
4. Test RAG pipeline: `python scripts/example_rag.py`
5. Launch web interface: `streamlit run src/app.py`

## Troubleshooting

### Playwright Issues
If Playwright browsers aren't working:
```bash
playwright install
playwright install-deps
```

### Model Download Issues
For HuggingFace models:
```bash
export HF_HOME=/home/vscode/.cache/huggingface
huggingface-cli login
```

### Azure CLI Authentication
To authenticate with Azure:
```bash
az login
az account set --subscription "your-subscription-id"
```

### Vector Database Connection
For local ChromaDB issues:
```bash
# Ensure proper permissions
sudo chown -R vscode:vscode data/embeddings/
```

## Performance Optimization

The container includes several optimizations:
- Persistent caches for models and embeddings
- Multi-process capability for concurrent operations
- Memory-mapped files for large datasets
- GPU support (if available on host)

## Contributing

When adding new dependencies:
1. Add to `requirements.txt` for production dependencies
2. Add to `.devcontainer/requirements-dev.txt` for development-only dependencies
3. Update this README if adding new major features
4. Rebuild the container to test changes

For RAG-specific contributions:
- Test with multiple document types
- Verify embedding quality with different models
- Ensure retrieval accuracy across domains
- Test generation quality with various prompts
