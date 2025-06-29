# USD RAG - Development Makefile

.PHONY: help install install-dev test format lint type-check clean setup-env run-api run-web run-notebook docker-build docker-run

help: ## Show this help message
	@echo "USD RAG - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install -r .devcontainer/requirements-dev.txt

test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

format: ## Format code with black and isort
	black src/ tests/
	isort src/ tests/

lint: ## Lint code with flake8
	flake8 src/ tests/

type-check: ## Type check with mypy
	mypy src/

clean: ## Clean temporary files and caches
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +

setup-env: ## Create .env file from template
	@if [ ! -f .env ]; then \
		echo "Creating .env file from template..."; \
		cp .env.example .env || echo "No .env.example found. Please create .env manually."; \
	else \
		echo ".env file already exists"; \
	fi

run-api: ## Run FastAPI development server
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

run-web: ## Run Streamlit web interface
	streamlit run src/app.py --server.port 8501

run-gradio: ## Run Gradio web interface
	python src/gradio_app.py

run-notebook: ## Start Jupyter Lab
	jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root

docker-build: ## Build Docker image
	docker build -t usyd-rag .

docker-run: ## Run Docker container
	docker run -p 8000:8000 -p 8501:8501 --env-file .env usyd-rag

install-spacy-models: ## Download spaCy language models
	python -m spacy download en_core_web_sm
	python -m spacy download en_core_web_md

install-playwright: ## Install Playwright browsers
	playwright install
	playwright install-deps

check-all: format lint type-check test ## Run all checks (format, lint, type-check, test)

dev-setup: install-dev install-spacy-models install-playwright setup-env ## Complete development setup

crawl-example: ## Run example crawling script
	python scripts/example_crawl.py

embed-example: ## Run example embedding generation
	python scripts/example_embeddings.py

rag-example: ## Run example RAG query
	python scripts/example_rag.py

logs: ## Show recent logs
	tail -f logs/app.log

# Azure specific commands
az-login: ## Login to Azure CLI
	az login

az-deploy: ## Deploy to Azure using azd
	azd up

az-logs: ## Show Azure application logs
	az webapp log tail --name your-app-name --resource-group your-resource-group

# Database management
db-migrate: ## Run database migrations
	alembic upgrade head

db-reset: ## Reset database
	alembic downgrade base
	alembic upgrade head

# Monitoring
health-check: ## Check application health
	curl -f http://localhost:8000/health || echo "API not running"

# Documentation
docs-build: ## Build documentation
	cd docs && make html

docs-serve: ## Serve documentation locally
	cd docs/_build/html && python -m http.server 8080
