# USD RAG Development Container
# Optimized for Python, Azure, GenAI, and Retrieval Augmented Generation
FROM mcr.microsoft.com/devcontainers/python:3.11-bullseye

# Install system dependencies for AI/ML, web scraping, and development
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        # Browser dependencies for Playwright
        libnss3-dev \
        libatk-bridge2.0-dev \
        libdrm-dev \
        libxkbcommon-dev \
        libgtk-3-dev \
        libgbm-dev \
        libasound2-dev \
        # AI/ML system dependencies
        libgl1-mesa-glx \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender-dev \
        libgomp1 \
        # Additional development utilities
        curl \
        wget \
        git \
        build-essential \
        # For handling certificates and SSL
        ca-certificates \
        gnupg \
        lsb-release \
        # Text processing tools
        poppler-utils \
        tesseract-ocr \
        # Database clients
        postgresql-client \
        default-mysql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for AI/ML development
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/home/vscode/.cache/huggingface \
    TRANSFORMERS_CACHE=/home/vscode/.cache/huggingface/transformers \
    LANGCHAIN_TRACING_V2=true

# Set working directory
WORKDIR /workspace

# Upgrade pip and install essential Python tools
RUN python -m pip install --upgrade pip setuptools wheel

# Set the default shell to bash
SHELL ["/bin/bash", "-c"]