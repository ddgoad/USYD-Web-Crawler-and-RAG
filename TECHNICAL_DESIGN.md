# USYD Web Crawler and RAG Solution - Technical Design Document

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture Overview](#architecture-overview)
3. [Technology Stack](#technology-stack)
4. [System Requirements](#system-requirements)
5. [Detailed Component Design](#detailed-component-design)
6. [Database Schema](#database-schema)
7. [API Design](#api-design)
8. [User Interface Design](#user-interface-design)
9. [Security Considerations](#security-considerations)
10. [Testing Strategy](#testing-strategy)
11. [Deployment Guide](#deployment-guide)
12. [Infrastructure Requirements](#infrastructure-requirements)
13. [Development Guidelines](#development-guidelines)

## Project Overview

### Purpose
The USYD Web Crawler and RAG (Retrieval-Augmented Generation) solution is a web application that enables users to scrape websites, convert the content into vector embeddings, and interact with the scraped content through an AI-powered chat interface.

### Key Features
- **Web Scraping**: Multiple scraping modes (single page, deep crawl, sitemap-based)
- **Vector Database Management**: Automatic conversion of scraped content to vector embeddings
- **AI Chat Interface**: Interactive Q&A using Azure OpenAI models
- **User Management**: Simple authentication and session management
- **Progress Tracking**: Real-time feedback on scraping and vectorization processes
- **Multi-Model Support**: GPT-4o and o3-mini model options
- **Flexible Search**: Keyword, semantic, and hybrid search capabilities
- **Document Upload**: Support for PDF, Word, and Markdown file uploads
- **Hybrid Content Sources**: Combine web scraped content with uploaded documents
- **Document Processing Pipeline**: Automatic conversion and integration of various file formats

## Solution Architecture Overview

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                USER INTERFACE                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Login/Auth    │  │   Web Scraping  │  │   Vector DB     │  │   Chat/Query    │ │
│  │   Dashboard     │  │   Configuration  │  │   Management    │  │   Interface     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                    HTTP/WebSocket
                                         │
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              FLASK BACKEND API                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Auth Service  │  │  Scraping API   │  │   Vector API    │  │    LLM API      │ │
│  │   Session Mgmt  │  │   Job Mgmt      │  │   DB Creation   │  │   Chat Logic    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
           │                       │                       │                       │
           │                       │                       │                       │
    ┌─────────────┐         ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
    │ PostgreSQL  │         │   Celery    │         │   Redis     │         │   Azure     │
    │ Database    │         │  Workers    │         │   Cache     │         │  Services   │
    │             │         │             │         │ Task Queue  │         │             │
    │• Users      │         │• Async      │         │             │         │• OpenAI     │
    │• Sessions   │         │  Scraping   │         │• Sessions   │         │• AI Search  │
    │• Jobs       │         │• Vector DB  │         │• Progress   │         │• Blob Store │
    │• Metadata   │         │  Creation   │         │  Tracking   │         │             │
    └─────────────┘         │• Document   │         └─────────────┘         └─────────────┘
                            │  Processing │
                            └─────────────┘
                                   │
                            ┌─────────────┐
                            │ Crawl4AI    │
                            │ Web Scraper │
                            │             │
                            │• Single     │
                            │  Page       │
                            │• Deep Crawl │
                            │• Sitemap    │
                            └─────────────┘

                    AZURE-ONLY VECTOR DATABASE ARCHITECTURE

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          CONTENT PROCESSING PIPELINE                               │
│                                                                                     │
│  Web Content Sources          Document Upload Sources         Processing           │
│  ┌─────────────────┐          ┌─────────────────┐             ┌─────────────────┐   │
│  │   Single Page   │          │      PDF        │             │  Content        │   │
│  │   Deep Crawl    │    +     │     Word        │      →      │  Chunking       │   │
│  │   Sitemap       │          │   Markdown      │             │  Embedding      │   │
│  └─────────────────┘          └─────────────────┘             └─────────────────┘   │
│                                                                          │          │
└──────────────────────────────────────────────────────────────────────────┼──────────┘
                                                                           │
                    ┌──────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              AZURE AI SEARCH                                       │
│                                                                                     │
│  Per-Job Dedicated Indexes:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │  usyd-rag-{user_id}-{timestamp}-{job_id}                                   │   │
│  │                                                                             │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │   │
│  │  │   Vector    │  │    Text     │  │  Metadata   │  │   Source    │        │   │
│  │  │   Fields    │  │   Fields    │  │   Fields    │  │ Attribution │        │   │
│  │  │             │  │             │  │             │  │             │        │   │
│  │  │• Embeddings │  │• Content    │  │• Title      │  │• Web URL    │        │   │
│  │  │• Semantic   │  │• Keywords   │  │• Created    │  │• Document   │        │   │
│  │  │  Search     │  │• Full-text  │  │• Updated    │  │  Name       │        │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                 Search Queries
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              AZURE OPENAI                                          │
│                                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                    │
│  │   Embedding     │  │     GPT-4o      │  │    o3-mini      │                    │
│  │   Generation    │  │   Chat Model    │  │   Chat Model    │                    │
│  │                 │  │                 │  │                 │                    │
│  │• text-embed-3   │  │• Context-aware  │  │• Faster         │                    │
│  │• Vector         │  │• Comprehensive  │  │• Cost-effective │                    │
│  │  Creation       │  │• Responses      │  │• Responses      │                    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                    │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### How the Components Work Together

The USYD Web Crawler and RAG solution is designed as a multi-layered architecture where each component serves a specific purpose and integrates seamlessly with others to provide a complete user experience.

#### **Frontend Layer - User Interface**
The user interface is built as a modern, responsive web application using Flask templates with HTML, CSS, and JavaScript. The interface is divided into two main functional areas:

1. **Web Scraping Control Panel**: This section allows users to configure and initiate web scraping operations. Users can specify the target URL, choose scraping modes (single page, deep crawl, or sitemap-based), and set parameters like crawl depth and page limits. When a scraping job is initiated, the interface provides real-time progress feedback through WebSocket connections, showing users exactly what's happening as their content is being processed. Once scraping completes, users can see their completed jobs and manually choose to create vector databases from them.

2. **Vector Database Management**: After scraping jobs complete, users can click "Create Vector Database" and select which completed scraping job to process. This initiates the creation of a dedicated Azure AI Search index. Users can monitor the progress of vector database creation and see when indexes are ready for use. **Enhanced with Document Upload**: Users can now also upload supplementary documents (PDF, Word, Markdown) during vector database creation to enrich the content beyond just scraped web pages.

3. **Chat Interface**: Once vector databases are ready, users can select a specific database and interact with it through an AI-powered chat interface. The interface allows users to choose between different AI models (GPT-4o or o3-mini), adjust search parameters (semantic, keyword, or hybrid search), and modify AI behavior settings like temperature before beginning their query session. The AI can now answer questions using both scraped web content and uploaded documents seamlessly.

#### **Backend API Layer - Business Logic**
The Flask-based backend serves as the orchestration layer that coordinates all system components. It handles user authentication, manages scraping jobs, interfaces with Azure services, and provides RESTful API endpoints for the frontend. The backend is designed to be stateless and scalable, with session management handled through Redis for high availability.

#### **Web Scraping Engine - Content Acquisition**
The scraping engine is built around Crawl4AI, a modern web scraping framework that handles JavaScript-heavy websites, respects robots.txt files, and provides intelligent content extraction. The engine operates in three distinct modes:

- **Single Page Mode**: Extracts content from a specific URL, perfect for scraping individual articles, product pages, or documents
- **Deep Crawl Mode**: Systematically explores a website by following internal links up to a specified depth, ideal for comprehensive site analysis
- **Sitemap Mode**: Uses XML sitemaps to efficiently discover and scrape all important pages on a website

The scraping process is asynchronous, using Celery workers to handle jobs in the background while providing real-time progress updates to users. This ensures the user interface remains responsive and users can continue using other parts of the application while scraping operations are running.

#### **Content Processing Pipeline - Data Transformation**
Once content is scraped, it goes through a sophisticated processing pipeline:

1. **Content Cleaning**: Raw HTML is processed to extract meaningful text, removing navigation elements, advertisements, and boilerplate content
2. **Text Chunking**: Large documents are intelligently split into smaller, semantically coherent chunks that are optimal for embedding and retrieval
3. **Metadata Extraction**: Important metadata like titles, URLs, publication dates, and content structure is preserved for search and citation purposes
4. **Embedding Generation**: Text chunks are converted into high-dimensional vector representations using Azure OpenAI's embedding models

#### **Document Processing Pipeline - Supplementary Content Integration**
To enhance the vector databases with additional context beyond web scraping, the system supports uploading and processing supplementary documents:

1. **Document Upload and Storage**:
   - **Supported Formats**: PDF, Microsoft Word (.docx), and Markdown (.md) files
   - **Azure Blob Storage**: Secure upload and storage of documents in Azure Blob Storage
   - **File Validation**: Format verification, size limits, and content scanning
   - **Metadata Extraction**: Document properties, creation dates, and file information

2. **Document Content Extraction**:
   - **PDF Processing**: Text extraction using PyPDF2/pdfplumber, handling complex layouts and embedded content
   - **Word Document Processing**: Content extraction using python-docx, preserving formatting and structure
   - **Markdown Processing**: Native parsing with metadata preservation
   - **Content Normalization**: Convert all formats to consistent text representation

3. **Hybrid Content Integration**:
   - **Content Merging**: Combine scraped web content with uploaded document content
   - **Source Attribution**: Maintain clear distinction between web sources and uploaded documents
   - **Unified Chunking**: Apply consistent chunking strategy across all content types
   - **Metadata Preservation**: Track content source (web vs. document) for proper citations

4. **Enhanced Processing Pipeline**:
   - **Duplicate Detection**: Identify and handle overlapping content between sources
   - **Content Quality Assessment**: Score and filter content based on relevance and completeness
   - **Batch Processing**: Efficient handling of multiple documents and web pages
   - **Progress Tracking**: Real-time status updates for document processing

#### **Vector Database Layer - Intelligent Storage (Azure-Only Architecture)**
Azure AI Search serves as the exclusive vector database solution, with each scraping job resulting in the programmatic creation of a dedicated Azure AI Search index. This Azure-only architecture ensures all vector storage and processing occurs in the cloud, with no local or SQLite dependencies. Key characteristics:

#### **Per-Job Index Creation**:
- Users manually initiate vector database creation after scraping job completion
- Each user-initiated vector database creation results in a new, uniquely named Azure AI Search index
- Index names follow the pattern: `usyd-rag-{user_id}-{timestamp}-{job_id}`
- Indexes are created programmatically via the Azure Search Management REST API when user clicks "Create Vector Database"
- Each index is configured with appropriate vector field mappings for embeddings

**Azure-Exclusive Vector Processing**:
- All embedding generation uses Azure OpenAI Services
- Vector storage occurs exclusively in Azure AI Search indexes
- No local vector databases or SQLite storage for vectors
- Embeddings are stored directly in Azure AI Search vector fields

**Search Capabilities**:
- **Semantic Search**: Finding content based on meaning and context using Azure AI Search vector capabilities
- **Keyword Search**: Traditional full-text search using Azure AI Search text fields
- **Hybrid Search**: Combining vector and text search for optimal retrieval accuracy
- All search operations execute entirely within Azure infrastructure

#### **AI Integration Layer - Intelligent Responses**
The AI layer uses Azure OpenAI services to provide intelligent responses to user queries. The system implements a Retrieval-Augmented Generation (RAG) approach:

1. **Query Processing**: User questions are analyzed and converted into appropriate search queries
2. **Content Retrieval**: Relevant chunks are retrieved from the vector database using the selected search method
3. **Context Assembly**: Retrieved chunks are assembled into a coherent context for the AI model
4. **Response Generation**: The AI model generates responses based on the retrieved content, ensuring accuracy and relevance
5. **Source Attribution**: Responses include citations and links back to original sources

#### **Background Processing - Scalable Operations**
All heavy computational tasks (web scraping, content processing, embedding generation, vector database creation) are handled by background workers using Celery and Redis. This architecture ensures:

- **Non-Blocking Operations**: Both scraping and vector database creation run asynchronously without freezing the user interface
- **Responsiveness**: The user interface remains responsive during long-running operations
- **Concurrent Operations**: Users can initiate multiple scraping jobs and vector database creations simultaneously
- **Scalability**: Multiple workers can process jobs in parallel
- **Reliability**: Failed jobs can be retried automatically
- **Progress Tracking**: Real-time status updates keep users informed of job progress without blocking the UI

#### **Data Persistence - Reliable Storage**
The system uses PostgreSQL for storing user data, job metadata, and application state. This includes:

- **User Management**: Authentication credentials and user preferences
- **Job Tracking**: Scraping job configurations, status, and results
- **Vector Database Metadata**: Information about created indexes and their contents
- **Chat History**: Conversation logs for user reference and system improvement

#### **Integration Flow - User-Initiated Multi-Step Azure-Only Process**
The complete user journey follows this user-controlled, multi-step Azure-only flow with asynchronous processing:

1. **Authentication**: Users log in through the secure authentication system
2. **Scraping Job Creation**: Users specify scraping parameters and initiate web scraping jobs (asynchronous, non-blocking)
3. **Asynchronous Content Acquisition**: The scraping engine processes websites in the background without blocking the UI, users can continue using the application
4. **User-Initiated Vector Database Creation**: After scraping completes, users manually click "Create Vector Database" and select a completed scraping job (asynchronous, non-blocking)
5. **Azure Index Creation**: The selected job's content is used to programmatically create a new Azure AI Search index with vector field configuration (background processing)
6. **Content Processing and Vector Storage**: Raw content is cleaned, chunked, embedded using Azure OpenAI, and stored exclusively in the newly created Azure AI Search index (asynchronous background processing)
7. **Vector Database Selection**: Users choose which vector database/Azure AI Search index they want to work with
8. **LLM Configuration**: Users select an LLM model (GPT-4o or o3-mini) and configure hyperparameters (temperature, search type)
9. **Interactive Querying**: Users ask questions about the scraped content using their configured Azure-based search and LLM setup
10. **Intelligent Responses**: The AI system provides accurate, source-attributed answers using the user's selected configuration

**Key User Control Points**:
- **Step 2**: User initiates scraping job (asynchronous execution, UI remains responsive)
- **Step 4**: User initiates vector database creation from completed scraping job (asynchronous execution, UI remains responsive)
- **Step 7**: User selects which vector database to use for queries
- **Step 8**: User configures LLM and search parameters

**Asynchronous Benefits**:
- Users can initiate multiple scraping jobs simultaneously
- Users can create multiple vector databases concurrently
- The interface remains responsive during long-running operations
- Real-time progress updates without blocking user interactions

This user-controlled, Azure-exclusive architecture ensures that all vector operations occur entirely within Azure infrastructure while giving users complete control over each step of the process and maintaining a responsive user experience.

## Technology Stack

### Core Technologies
- **Backend Framework**: Flask 3.0+
- **Web Scraping**: Crawl4AI 0.3+
- **Vector Database**: Azure AI Search
- **LLM Provider**: Azure OpenAI
- **Task Queue**: Celery with Redis
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Database**: PostgreSQL (for user data and metadata)
- **Caching**: Redis
- **File Storage**: Azure Blob Storage
- **Document Processing**: PyPDF2, python-docx, python-markdown
- **Deployment**: Azure Container Apps with AZD

### Python Dependencies
The complete requirements.txt file includes all necessary dependencies organized by functionality. See the `requirements.txt` file in the project root for the comprehensive list of over 100 dependencies covering web scraping, AI integration, vector databases, testing, monitoring, and development tools.

### Enhanced Dependencies for Document Processing
```
# Document Processing
PyPDF2==3.0.1
pdfplumber==0.10.0
python-docx==1.1.0
python-markdown==3.5.1

# Azure Storage
azure-storage-blob==12.19.0
azure-identity==1.15.0

# File Processing
python-magic==0.4.27
chardet==5.2.0

# Additional utilities
filetype==1.2.0
validators==0.22.0
```

## System Requirements

### Functional Requirements
1. **User Authentication**
   - Simple login/logout functionality
   - Session management
   - User-specific data isolation

2. **Web Scraping Module**
   - Single page scraping
   - Deep crawling with configurable depth
   - Sitemap-based crawling
   - Content filtering and cleaning
   - Real-time progress tracking

3. **Vector Database Management (Azure-Only)**
   - Programmatic Azure AI Search index creation per scraping job
   - Automatic text chunking and embedding via Azure OpenAI
   - Vector storage exclusively in Azure AI Search indexes
   - Metadata preservation and job-to-index mapping
   - Azure-based search index management (no local vector storage)
   - **Document Upload and Integration**: Support for supplementary documents (PDF, Word, Markdown)
   - **Hybrid Content Processing**: Combine scraped web content with uploaded documents
   - **Azure Storage Integration**: Secure document storage and processing pipeline

4. **Chat Interface**
   - Real-time chat with AI models
   - Context-aware responses
   - Search result integration
   - Conversation history

5. **Configuration Management**
   - LLM model selection
   - Search type configuration
   - Temperature and parameter tuning

### Non-Functional Requirements
- **Performance**: Handle 100+ concurrent users
- **Scalability**: Auto-scaling based on demand
- **Reliability**: 99.9% uptime
- **Security**: Secure data handling and authentication
- **Usability**: Intuitive user interface

## Detailed Component Design

### 1. Authentication Service (`auth.py`)
```python
class AuthService:
    def __init__(self):
        self.users = {}  # Simple in-memory store for demo
    
    def login(self, username: str, password: str) -> bool:
        """Authenticate user credentials"""
        pass
    
    def logout(self, user_id: str) -> bool:
        """End user session"""
        pass
    
    def is_authenticated(self, session) -> bool:
        """Check if user is logged in"""
        pass
```

### 2. Web Scraping Service (`scraper.py`)
```python
from crawl4ai import WebCrawler
from celery import Celery

class ScrapingService:
    def __init__(self):
        self.crawler = WebCrawler()
    
    def scrape_single_page(self, url: str) -> dict:
        """Scrape a single web page"""
        pass
    
    def scrape_website_deep(self, url: str, max_depth: int = 3) -> dict:
        """Deep crawl a website"""
        pass
    
    def scrape_from_sitemap(self, sitemap_url: str) -> dict:
        """Scrape URLs from sitemap"""
        pass
    
    @celery.task
    def process_scraping_job(self, job_config: dict) -> str:
        """Background task for scraping"""
        pass
```

### 3. Document Processing Service (`document_processor.py`)
```python
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import AzureError
import PyPDF2
import docx
import markdown
import os
from typing import Dict, List, Tuple
from celery import Celery

class DocumentProcessingService:
    def __init__(self):
        self.blob_service_client = BlobServiceClient(
            account_url=os.getenv("AZURE_STORAGE_ACCOUNT_URL"),
            credential=os.getenv("AZURE_STORAGE_KEY")
        )
        self.container_name = "user-documents"
    
    def upload_document(self, file_data: bytes, filename: str, user_id: int) -> str:
        """Upload document to Azure Blob Storage"""
        blob_name = f"user_{user_id}/{filename}"
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, 
                blob=blob_name
            )
            blob_client.upload_blob(file_data, overwrite=True)
            return blob_name
        except AzureError as e:
            raise Exception(f"Failed to upload document: {str(e)}")
    
    def validate_document(self, filename: str, file_size: int) -> bool:
        """Validate document format and size"""
        allowed_extensions = ['.pdf', '.docx', '.md']
        max_size = 50 * 1024 * 1024  # 50MB limit
        
        if file_size > max_size:
            raise ValueError("File size exceeds 50MB limit")
        
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise ValueError(f"Unsupported file format. Allowed: {allowed_extensions}")
        
        return True
    
    def extract_text_from_pdf(self, file_path: str) -> Tuple[str, Dict]:
        """Extract text content from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_content = ""
                metadata = {
                    "page_count": len(pdf_reader.pages),
                    "title": pdf_reader.metadata.get('/Title', ''),
                    "author": pdf_reader.metadata.get('/Author', ''),
                    "source_type": "pdf_document"
                }
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    text_content += f"\n--- Page {page_num + 1} ---\n{page_text}"
                
                return text_content.strip(), metadata
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    def extract_text_from_docx(self, file_path: str) -> Tuple[str, Dict]:
        """Extract text content from Word document"""
        try:
            doc = docx.Document(file_path)
            text_content = ""
            metadata = {
                "paragraph_count": len(doc.paragraphs),
                "source_type": "word_document"
            }
            
            # Extract core properties if available
            if hasattr(doc, 'core_properties'):
                metadata.update({
                    "title": doc.core_properties.title or '',
                    "author": doc.core_properties.author or '',
                    "created": str(doc.core_properties.created) if doc.core_properties.created else ''
                })
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content += paragraph.text + "\n"
            
            return text_content.strip(), metadata
        except Exception as e:
            raise Exception(f"Failed to extract text from Word document: {str(e)}")
    
    def extract_text_from_markdown(self, file_path: str) -> Tuple[str, Dict]:
        """Extract text content from Markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Convert markdown to plain text (removing formatting)
            md = markdown.Markdown()
            html = md.convert(content)
            
            # Extract metadata from markdown frontmatter if present
            metadata = {
                "source_type": "markdown_document",
                "original_format": "markdown"
            }
            
            # Simple extraction of text from HTML
            import re
            text_content = re.sub('<[^<]+?>', '', html)
            
            return text_content.strip(), metadata
        except Exception as e:
            raise Exception(f"Failed to extract text from Markdown: {str(e)}")
    
    @celery.task
    def process_uploaded_documents(self, blob_names: List[str], user_id: int) -> List[Dict]:
        """Process uploaded documents asynchronously"""
        processed_documents = []
        
        for blob_name in blob_names:
            try:
                # Download document from blob storage
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=blob_name
                )
                
                # Create temporary file
                filename = os.path.basename(blob_name)
                temp_path = f"/tmp/{filename}"
                
                with open(temp_path, 'wb') as temp_file:
                    download_stream = blob_client.download_blob()
                    temp_file.write(download_stream.readall())
                
                # Extract text based on file type
                file_ext = os.path.splitext(filename)[1].lower()
                
                if file_ext == '.pdf':
                    text_content, metadata = self.extract_text_from_pdf(temp_path)
                elif file_ext == '.docx':
                    text_content, metadata = self.extract_text_from_docx(temp_path)
                elif file_ext == '.md':
                    text_content, metadata = self.extract_text_from_markdown(temp_path)
                else:
                    continue  # Skip unsupported files
                
                # Add document info to metadata
                metadata.update({
                    "filename": filename,
                    "blob_name": blob_name,
                    "user_id": user_id,
                    "content_length": len(text_content)
                })
                
                processed_documents.append({
                    "content": text_content,
                    "metadata": metadata,
                    "source_url": f"document://{filename}",
                    "title": metadata.get("title", filename)
                })
                
                # Clean up temporary file
                os.remove(temp_path)
                
            except Exception as e:
                print(f"Error processing document {blob_name}: {str(e)}")
                continue
        
        return processed_documents
    
    def delete_document(self, blob_name: str) -> bool:
        """Delete document from Azure Blob Storage"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            blob_client.delete_blob()
            return True
        except AzureError as e:
            print(f"Failed to delete document: {str(e)}")
            return False
    
    def chunk_document_content(self, content: str, metadata: Dict, chunk_size: int = 1000) -> List[Dict]:
        """Split document content into chunks suitable for embedding"""
        chunks = []
        words = content.split()
        
        for i in range(0, len(words), chunk_size):
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                "chunk_index": i // chunk_size,
                "chunk_size": len(chunk_words),
                "total_chunks": (len(words) + chunk_size - 1) // chunk_size
            })
            
            chunks.append({
                "content": chunk_text,
                "metadata": chunk_metadata,
                "source_url": metadata.get("source_url", ""),
                "title": f"{metadata.get('title', 'Document')} - Part {chunk_metadata['chunk_index'] + 1}"
            })
        
        return chunks
```

### 4. Vector Database Service (`vector_store.py`) - Azure-Only Implementation
```python
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.core.credentials import AzureKeyCredential
from celery import Celery
import datetime

class VectorStoreService:
    def __init__(self):
        self.index_client = SearchIndexClient(
            endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY"))
        )
    
    def create_job_index(self, user_id: int, job_id: str) -> str:
        """Create a new Azure AI Search index for a specific scraping job"""
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        index_name = f"usyd-rag-{user_id}-{timestamp}-{job_id}"
        
        # Create index with vector field configuration
        # This creates a dedicated Azure AI Search index for this job
        pass
    
    @celery.task
    def create_vector_database_async(self, user_id: int, job_id: str, db_name: str, uploaded_documents: List[str] = None) -> str:
        """Asynchronous task to create vector database from scraping job and optional documents"""
        # This runs in background without blocking the UI
        # 1. Create Azure AI Search index
        # 2. Process and chunk content from scraping job
        # 3. Process uploaded documents (if any)
        # 4. Combine web content and document content
        # 5. Generate embeddings for all content
        # 6. Upload to Azure AI Search index
        # 7. Update database status
        pass
    
    def get_search_client(self, index_name: str) -> SearchClient:
        """Get search client for a specific job's index"""
        return SearchClient(
            endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            index_name=index_name,
            credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY"))
        )
    
    def add_documents_to_job_index(self, index_name: str, documents: List[dict]) -> bool:
        """Add documents to a specific job's Azure AI Search index"""
        search_client = self.get_search_client(index_name)
        # Add documents with embeddings to the job-specific index
        pass
    
    def search_job_index(self, index_name: str, query: str, search_type: str = "semantic") -> List[dict]:
        """Search documents in a specific job's Azure AI Search index"""
        search_client = self.get_search_client(index_name)
        # Perform search within the job-specific index
        pass
    
    def delete_job_index(self, index_name: str) -> bool:
        """Delete a specific job's Azure AI Search index"""
        # Remove the job-specific index from Azure AI Search
        pass
    
    def list_user_indexes(self, user_id: int) -> List[str]:
        """List all Azure AI Search indexes for a specific user"""
        # Return all indexes matching the user's naming pattern
        pass
    
    def get_vector_db_status(self, db_id: str) -> dict:
        """Get current status of vector database creation (non-blocking)"""
        # Return status: building, ready, error with progress information
        pass
    
    def combine_content_sources(self, web_content: List[dict], document_content: List[dict]) -> List[dict]:
        """Combine scraped web content with processed document content"""
        combined_content = []
        
        # Add web content with source attribution
        for item in web_content:
            item['content_source'] = 'web_scraping'
            combined_content.append(item)
        
        # Add document content with source attribution
        for item in document_content:
            item['content_source'] = 'uploaded_document'
            combined_content.append(item)
        
        return combined_content
    
    def create_enhanced_index_schema(self) -> dict:
        """Create Azure AI Search index schema with document support"""
        return {
            "fields": [
                {"name": "id", "type": "Edm.String", "key": True},
                {"name": "content", "type": "Edm.String", "searchable": True},
                {"name": "title", "type": "Edm.String", "searchable": True},
                {"name": "url", "type": "Edm.String", "retrievable": True},
                {"name": "content_vector", "type": "Collection(Edm.Single)", 
                 "searchable": True, "vectorSearchDimensions": 1536},
                {"name": "content_source", "type": "Edm.String", "filterable": True, "facetable": True},
                {"name": "source_type", "type": "Edm.String", "filterable": True, "facetable": True},
                {"name": "filename", "type": "Edm.String", "retrievable": True},
                {"name": "timestamp", "type": "Edm.DateTimeOffset", "filterable": True},
                {"name": "chunk_index", "type": "Edm.Int32", "filterable": True},
                {"name": "metadata", "type": "Edm.String", "retrievable": True}
            ],
            "vectorSearch": {
                "algorithms": [
                    {"name": "vector-config", "kind": "hnsw"}
                ]
            }
        }
```

### 4. LLM Service (`llm_service.py`)
```python
from openai import AzureOpenAI

class LLMService:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
    
    def generate_response(self, query: str, context: str, model: str = "gpt-4o") -> str:
        """Generate AI response based on query and context"""
        pass
    
    def generate_embeddings(self, text: str) -> List[float]:
        """Generate embeddings for text"""
        pass
```

### 5. Main Application (`app.py`)
```python
from flask import Flask, render_template, request, jsonify, session
from flask_login import LoginManager, login_required

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Initialize services
auth_service = AuthService()
scraping_service = ScrapingService()
vector_service = VectorStoreService()
llm_service = LLMService()

@app.route("/")
def index():
    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/api/scrape", methods=["POST"])
@login_required
def start_scraping():
    """Start web scraping job"""
    pass

@app.route("/api/chat", methods=["POST"])
@login_required
def chat():
    """Handle chat requests"""
    pass
```

## Database Schema

### PostgreSQL Tables

#### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

#### Scraping Jobs Table
```sql
CREATE TABLE scraping_jobs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    url VARCHAR(2048) NOT NULL,
    scraping_type VARCHAR(20) NOT NULL, -- 'single', 'deep', 'sitemap'
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    config JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    result_summary JSONB
);
```

#### Vector Databases Table (Azure Index Tracking)
```sql
CREATE TABLE vector_databases (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    job_id INTEGER REFERENCES scraping_jobs(id),
    name VARCHAR(100) NOT NULL,
    source_url VARCHAR(2048) NOT NULL,
    azure_index_name VARCHAR(100) UNIQUE NOT NULL, -- Unique Azure AI Search index name
    document_count INTEGER DEFAULT 0,
    embedding_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'building', -- 'building', 'ready', 'error'
    index_size_mb DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, job_id) -- Each job gets exactly one vector database/index
);
```

#### Chat Sessions Table
```sql
CREATE TABLE chat_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    vector_db_id INTEGER REFERENCES vector_databases(id),
    model_name VARCHAR(50) NOT NULL,
    config JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Chat Messages Table
```sql
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES chat_sessions(id),
    role VARCHAR(10) NOT NULL, -- 'user', 'assistant'
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Uploaded Documents Table
```sql
CREATE TABLE uploaded_documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    vector_db_id INTEGER REFERENCES vector_databases(id),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    file_type VARCHAR(10) NOT NULL, -- 'pdf', 'docx', 'md'
    blob_name VARCHAR(500) NOT NULL, -- Azure Blob Storage reference
    content_length INTEGER,
    processing_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processed', 'failed'
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    metadata JSONB
);
```

## API Design

### Authentication Endpoints
```
POST /api/auth/login
- Body: {"username": "string", "password": "string"}
- Response: {"success": boolean, "user_id": "string"}

POST /api/auth/logout
- Response: {"success": boolean}

GET /api/auth/status
- Response: {"authenticated": boolean, "user": object}
```

### Scraping Endpoints
```
POST /api/scrape/start
- Body: {
    "url": "string",
    "type": "single|deep|sitemap",
    "config": {
      "max_depth": integer,
      "max_pages": integer,
      "delay": integer
    }
  }
- Response: {"job_id": "string", "status": "started"}

GET /api/scrape/status/{job_id}
- Response: {
    "status": "pending|running|completed|failed",
    "progress": integer,
    "message": "string"
  }

GET /api/scrape/jobs
- Response: {"jobs": [array of job objects]}
```

### Vector Database Endpoints
```
GET /api/vector-dbs
- Response: {"databases": [array of vector db objects]}

GET /api/scrape/completed-jobs
- Response: {"jobs": [array of completed scraping jobs available for vector db creation]}

POST /api/vector-dbs/create
- Body: {
    "name": "string", 
    "scraping_job_id": "string",
    "uploaded_files": ["file1", "file2", ...] // Optional file uploads
  }
- Response: {"db_id": "string", "azure_index_name": "string", "status": "building"}

POST /api/documents/upload
- Body: FormData with files
- Response: {
    "uploaded_files": [
      {"filename": "string", "blob_name": "string", "size": integer}
    ]
  }

GET /api/documents/validate
- Query: filename, size
- Response: {"valid": boolean, "error": "string"}

DELETE /api/documents/{blob_name}
- Response: {"success": boolean}

GET /api/vector-dbs/{db_id}/status
- Response: {"status": "building|ready|error", "progress": integer, "document_count": integer}

DELETE /api/vector-dbs/{db_id}
- Response: {"success": boolean}

POST /api/vector-dbs/{db_id}/search
- Body: {
    "query": "string",
    "search_type": "keyword|semantic|hybrid",
    "top_k": integer
  }
- Response: {"results": [array of search results]}
```

### Chat Endpoints
```
POST /api/chat/start
- Body: {
    "vector_db_id": "string",
    "model": "gpt-4o|o3-mini",
    "config": {
      "temperature": float,
      "max_tokens": integer
    }
  }
- Response: {"session_id": "string"}

POST /api/chat/message
- Body: {
    "session_id": "string",
    "message": "string"
  }
- Response: {
    "response": "string",
    "sources": [array of source documents]
  }

GET /api/chat/history/{session_id}
- Response: {"messages": [array of message objects]}
```

## Azure-Only Vector Processing Workflow

### Per-Job Vector Store Creation Architecture

The USYD Web Crawler and RAG solution implements a strict Azure-only architecture where each scraping job results in the creation of a dedicated Azure AI Search index. This design ensures complete isolation between jobs while leveraging Azure's enterprise-grade infrastructure for all vector operations.

#### **Job-to-Index Mapping**
- **User-Controlled Relationship**: Users choose which completed scraping jobs to convert into Azure AI Search indexes
- **One-to-One Relationship**: Each vector database creation creates exactly one Azure AI Search index from one scraping job
- **Unique Naming Convention**: `usyd-rag-{user_id}-{timestamp}-{job_id}`
- **User-Initiated Creation**: Indexes are created via Azure Search Management API only when user clicks "Create Vector Database"
- **Isolated Storage**: No shared indexes between jobs, ensuring data isolation and security

#### **Azure-Exclusive Processing Pipeline**

1. **Content Acquisition Phase**
   - User initiates web scraping job through the interface
   - Web scraping occurs using Celery background workers (asynchronous, non-blocking)
   - Raw content is temporarily stored in PostgreSQL as job results
   - No local file system or SQLite storage for scraped content

2. **User-Initiated Vector Database Creation**
   - User clicks "Create Vector Database" button after scraping job completes
   - User selects which completed scraping job to process
   - System begins asynchronous Azure AI Search index creation process (non-blocking)
   - User interface remains responsive while vector database is being created
   - Progress updates are provided via background polling

3. **Azure AI Search Index Creation**
   ```python
   # User-initiated index creation for selected job
   def create_vector_database_from_job(user_id: int, job_id: str):
       # User has selected a completed scraping job to convert to vector database
       index_name = f"usyd-rag-{user_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{job_id}"
       
       # Create Azure AI Search index with vector field configuration
       index_schema = {
           "fields": [
               {"name": "id", "type": "Edm.String", "key": True},
               {"name": "content", "type": "Edm.String", "searchable": True},
               {"name": "title", "type": "Edm.String", "searchable": True},
               {"name": "url", "type": "Edm.String", "retrievable": True},
               {"name": "content_vector", "type": "Collection(Edm.Single)", 
                "searchable": True, "vectorSearchDimensions": 1536},
               {"name": "timestamp", "type": "Edm.DateTimeOffset", "filterable": True}
           ],
           "vectorSearch": {
               "algorithms": [
                   {"name": "vector-config", "kind": "hnsw"}
               ]
           }
       }
       
       # Create index via Azure Search Management API
       azure_search_client.create_index(index_name, index_schema)
   ```

4. **Embedding Generation and Storage**
   - Text chunks from the selected job are processed asynchronously in background workers
   - Embeddings are generated using Azure OpenAI's text-embedding-ada-002 model
   - Both text content and vector embeddings are stored directly in the Azure AI Search index
   - No local vector storage or caching
   - Progress is tracked and reported to the user interface without blocking

5. **User Selection of Vector Database and LLM Configuration**
   - User chooses which vector database/Azure AI Search index to query
   - User selects LLM model (GPT-4o or o3-mini)
   - User configures hyperparameters (temperature, search type: semantic, keyword, hybrid)

6. **Metadata Tracking**
   - PostgreSQL stores job-to-index mapping and metadata
   - Azure AI Search index name is stored for retrieval operations
   - Document counts and processing status tracked in PostgreSQL

#### **Search and Retrieval Operations**

All search operations are performed exclusively within Azure AI Search:

```python
# Azure-only search implementation
def search_job_content(index_name: str, query: str, search_type: str):
    search_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=index_name,
        credential=AzureKeyCredential(AZURE_SEARCH_KEY)
    )
    
    if search_type == "semantic":
        # Vector similarity search using Azure AI Search
        query_vector = azure_openai_client.create_embedding(query)
        results = search_client.search(
            search_text=None,
            vector_queries=[{
                "vector": query_vector,
                "fields": "content_vector",
                "k": 10
            }]
        )
    elif search_type == "keyword":
        # Full-text search using Azure AI Search
        results = search_client.search(search_text=query)
    elif search_type == "hybrid":
        # Combined vector and text search
        query_vector = azure_openai_client.create_embedding(query)
        results = search_client.search(
            search_text=query,
            vector_queries=[{
                "vector": query_vector,
                "fields": "content_vector",
                "k": 10
            }]
        )
    
    return results
```

#### **Benefits of Azure-Only Architecture**

1. **Enterprise Scalability**: Leverages Azure's global infrastructure for unlimited scaling
2. **Zero Local Dependencies**: No SQLite, local file storage, or embedded vector databases
3. **High Availability**: Built-in redundancy and disaster recovery through Azure
4. **Security**: Enterprise-grade security and compliance through Azure services
5. **Cost Efficiency**: Pay-per-use pricing model with automatic scaling
6. **Maintenance-Free**: No local vector database maintenance or updates required

#### **Index Lifecycle Management**

- **Scraping Job Creation**: User-initiated through web interface (asynchronous execution)
- **Job Completion**: Asynchronous processing, results stored in PostgreSQL, UI remains responsive
- **Vector Database Creation**: User clicks "Create Vector Database" and selects a completed job (asynchronous execution)
- **Index Population**: Real-time during user-initiated vector database creation (background processing)
- **LLM Selection**: User chooses vector database and configures LLM parameters (immediate UI response)
- **Usage**: Available for queries after user selects the vector database
- **Cleanup**: Configurable retention policies for cost management
- **Monitoring**: Azure AI Search metrics for performance tracking

This user-controlled, Azure-exclusive approach ensures that users have complete control over each step while maintaining a responsive interface and the solution scales to enterprise requirements.

## Enhanced Document Integration Workflow

### Complete User Journey with Document Upload

The enhanced USYD Web Crawler and RAG solution now supports a hybrid content approach, allowing users to combine scraped web content with uploaded documents for richer, more comprehensive vector databases.

#### **Step-by-Step Enhanced Process**

1. **Authentication and Setup** (Same as before)
   - Users log in through the secure authentication system
   - Access to personalized dashboard with scraping and document management capabilities

2. **Web Scraping Phase** (Same as before)
   - Users configure and initiate web scraping jobs (single page, deep crawl, or sitemap)
   - Asynchronous processing ensures UI remains responsive
   - Real-time progress tracking and job status updates

3. **Enhanced Vector Database Creation** (New Enhanced Process)
   - **Step 3a**: User clicks "Create Vector Database" button
   - **Step 3b**: Enhanced modal opens with two content source options:
     - **Required**: Select completed scraping job as primary content source
     - **Optional**: Upload supplementary documents (PDF, Word, Markdown)
   
   - **Step 3c**: Document Upload Process (Optional)
     - Drag-and-drop or file browser selection
     - Real-time validation (file type, size limits, duplicate detection)
     - Visual file preview with metadata display
     - Secure upload to Azure Blob Storage
   
   - **Step 3d**: Combined Processing Initiation
     - User submits form to create enhanced vector database
     - System processes both web content and uploaded documents
     - Asynchronous background processing maintains UI responsiveness

4. **Hybrid Content Processing Pipeline** (Enhanced)
   - **Phase 1**: Web content processing (existing pipeline)
     - Content cleaning and text extraction from scraped pages
     - Intelligent chunking and metadata preservation
   
   - **Phase 2**: Document content processing (new)
     - Download documents from Azure Blob Storage
     - Format-specific text extraction (PDF, Word, Markdown)
     - Content normalization to match web content structure
     - Document metadata preservation and source attribution
   
   - **Phase 3**: Content integration and enhancement
     - Combine web content chunks with document chunks
     - Apply consistent embedding generation across all content
     - Maintain source attribution for proper citations
     - Create unified Azure AI Search index with mixed content

5. **Enhanced Vector Database Features** (New Capabilities)
   - **Multi-Source Search**: Query across both web content and uploaded documents
   - **Source Filtering**: Filter results by content source (web vs. documents)
   - **Enhanced Citations**: Proper attribution to web pages or document sections
   - **Richer Context**: More comprehensive knowledge base for AI responses

6. **Chat Interface with Enhanced Context** (Improved)
   - AI can reference both scraped web content and uploaded documents
   - Source citations include document names and page numbers where applicable
   - Enhanced search capabilities across diverse content types
   - Improved answer quality from richer knowledge base

#### **Benefits of Document Integration**

1. **Comprehensive Knowledge Base**
   - Combine public web information with private/proprietary documents
   - Create domain-specific knowledge repositories
   - Supplement web content with detailed technical documentation

2. **Enhanced Search and Discovery**
   - Cross-reference information between web sources and documents
   - Find connections between public information and internal documents
   - Comprehensive coverage of topics across multiple content types

3. **Improved AI Responses**
   - More accurate answers from diverse content sources
   - Better context understanding from multiple perspectives
   - Enhanced ability to provide detailed, well-sourced responses

4. **Flexible Content Management**
   - Easy addition of new documents to existing vector databases
   - Support for various document formats and structures
   - Scalable approach to knowledge base expansion

#### **Example Use Cases**

1. **Research Projects**
   - Scrape academic websites and papers
   - Upload related research documents, notes, and findings
   - Create comprehensive research knowledge base

2. **Business Intelligence**
   - Scrape competitor websites and industry news
   - Upload internal reports, market research, and strategy documents
   - Build comprehensive market analysis database

3. **Technical Documentation**
   - Scrape official API documentation and tutorials
   - Upload internal guides, code documentation, and best practices
   - Create unified technical knowledge repository

4. **Legal and Compliance**
   - Scrape regulatory websites and legal databases
   - Upload internal policies, contracts, and compliance documents
   - Build comprehensive legal reference system

## User Interface Design

### 1. Login Page (`templates/login.html`)
```html
<!DOCTYPE html>
<html>
<head>
    <title>USYD Web Crawler & RAG - Login</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <div class="login-container">
        <h1>USYD Web Crawler & RAG</h1>
        <form id="login-form">
            <input type="text" id="username" placeholder="Username" required>
            <input type="password" id="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    </div>
    <script src="{{ url_for('static', filename='js/login.js') }}"></script>
</body>
</html>
```

### 2. Dashboard Page (`templates/dashboard.html`)
```html
<!DOCTYPE html>
<html>
<head>
    <title>USYD Web Crawler & RAG - Dashboard</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <div class="dashboard">
        <header>
            <h1>USYD Web Crawler & RAG</h1>
            <button id="logout-btn">Logout</button>
        </header>
        
        <div class="main-content">
            <!-- Scraping Section -->
            <div class="section scraping-section">
                <h2>Web Scraping</h2>
                <form id="scraping-form">
                    <div class="form-group">
                        <label>Website URL:</label>
                        <input type="url" id="website-url" required>
                    </div>
                    <div class="form-group">
                        <label>Scraping Type:</label>
                        <select id="scraping-type">
                            <option value="single">Single Page</option>
                            <option value="deep">Deep Crawl</option>
                            <option value="sitemap">Sitemap Based</option>
                        </select>
                    </div>
                    <div class="form-group" id="deep-options" style="display:none;">
                        <label>Max Depth:</label>
                        <input type="number" id="max-depth" value="3" min="1" max="10">
                        <label>Max Pages:</label>
                        <input type="number" id="max-pages" value="100" min="1" max="1000">
                    </div>
                    <button type="submit">Start Scraping</button>
                </form>
                
                <div id="scraping-progress" style="display:none;">
                    <h3>Scraping Progress</h3>
                    <div class="progress-bar">
                        <div id="progress-fill"></div>
                    </div>
                    <p id="progress-text">Starting...</p>
                </div>
            </div>
            
            <!-- Completed Jobs Section -->
            <div class="section completed-jobs-section">
                <h2>Create Vector Databases</h2>
                <div id="completed-jobs-list">
                    <!-- Dynamically populated with completed scraping jobs -->
                </div>
            </div>
            
            <!-- Vector Databases Section -->
            <div class="section vector-dbs-section">
                <h2>Vector Databases</h2>
                <div id="vector-dbs-list">
                    <!-- Dynamically populated -->
                </div>
                
                <div id="chat-interface" style="display:none;">
                    <h3>Chat Interface</h3>
                    <div class="chat-config">
                        <select id="model-select">
                            <option value="gpt-4o">GPT-4o</option>
                            <option value="o3-mini">o3-mini</option>
                        </select>
                        <select id="search-type">
                            <option value="semantic">Semantic Search</option>
                            <option value="keyword">Keyword Search</option>
                            <option value="hybrid">Hybrid Search</option>
                        </select>
                        <input type="range" id="temperature" min="0" max="1" step="0.1" value="0.7">
                        <label>Temperature: <span id="temp-value">0.7</span></label>
                    </div>
                    
                    <div id="chat-messages"></div>
                    <div class="chat-input">
                        <input type="text" id="chat-input" placeholder="Ask a question...">
                        <button id="send-btn">Send</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="{{ url_for('static', filename='js/dashboard.js') }}"></script>
</body>
</html>
```

### 3. CSS Styles (`static/css/style.css`)
```css
/* Modern CSS with responsive design */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
}

.login-container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 100vh;
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
}

.dashboard {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    background: white;
    min-height: 100vh;
    box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
}

.main-content {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 20px;
    margin-top: 30px;
}

.section {
    background: #f8f9fa;
    padding: 25px;
    border-radius: 12px;
    border: 1px solid #e9ecef;
}

.progress-bar {
    width: 100%;
    height: 20px;
    background: #e9ecef;
    border-radius: 10px;
    overflow: hidden;
    margin: 10px 0;
}

#progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #28a745, #20c997);
    width: 0%;
    transition: width 0.3s ease;
}

.chat-messages {
    height: 400px;
    overflow-y: auto;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 15px;
    margin: 15px 0;
    background: white;
}

.message {
    margin-bottom: 15px;
    padding: 10px;
    border-radius: 8px;
}

.message.user {
    background: #007bff;
    color: white;
    margin-left: 20%;
}

.message.assistant {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    margin-right: 20%;
}

.completed-job-item, .vector-db-item {
    background: white;
    padding: 15px;
    margin: 10px 0;
    border-radius: 8px;
    border: 1px solid #e9ecef;
}

.completed-job-item button, .vector-db-item button {
    background: #007bff;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
    margin-top: 10px;
}

.completed-job-item button:hover, .vector-db-item button:hover {
    background: #0056b3;
}

@media (max-width: 1200px) {
    .main-content {
        grid-template-columns: 1fr 1fr;
    }
}

@media (max-width: 768px) {
    .main-content {
        grid-template-columns: 1fr;
    }
}
```

### 4. JavaScript Frontend (`static/js/dashboard.js`)
```javascript
class Dashboard {
    constructor() {
        this.currentSession = null;
        this.vectorDbs = [];
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadVectorDatabases();
        this.loadCompletedJobs();
        this.setupWebSocket();
    }
    
    bindEvents() {
        // Scraping form submission
        document.getElementById('scraping-form').addEventListener('submit', this.startScraping.bind(this));
        
        // Chat input
        document.getElementById('send-btn').addEventListener('click', this.sendMessage.bind(this));
        document.getElementById('chat-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        
        // Model and search type changes
        document.getElementById('scraping-type').addEventListener('change', this.toggleDeepOptions.bind(this));
        document.getElementById('temperature').addEventListener('input', this.updateTemperatureDisplay.bind(this));
    }
    
    async startScraping(e) {
        e.preventDefault();
        const formData = {
            url: document.getElementById('website-url').value,
            type: document.getElementById('scraping-type').value,
            config: {}
        };
        
        if (formData.type === 'deep') {
            formData.config.max_depth = parseInt(document.getElementById('max-depth').value);
            formData.config.max_pages = parseInt(document.getElementById('max-pages').value);
        }
        
        try {
            const response = await fetch('/api/scrape/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(formData)
            });
            
            const result = await response.json();
            if (result.job_id) {
                this.trackScrapingProgress(result.job_id);
            }
        } catch (error) {
            console.error('Scraping failed:', error);
            alert('Failed to start scraping');
        }
    }
    
    trackScrapingProgress(jobId) {
        const progressDiv = document.getElementById('scraping-progress');
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');
        
        progressDiv.style.display = 'block';
        
        const checkProgress = async () => {
            try {
                const response = await fetch(`/api/scrape/status/${jobId}`);
                const status = await response.json();
                
                progressFill.style.width = `${status.progress}%`;
                progressText.textContent = status.message;
                
                if (status.status === 'completed') {
                    progressText.textContent = 'Scraping completed! You can now create a vector database.';
                    this.loadCompletedJobs(); // Load jobs available for vector database creation
                } else if (status.status === 'failed') {
                    progressText.textContent = 'Scraping failed!';
                } else {
                    setTimeout(checkProgress, 2000);
                }
            } catch (error) {
                console.error('Failed to check progress:', error);
            }
        };
        
        checkProgress();
    }
    
    async loadCompletedJobs() {
        try {
            const response = await fetch('/api/scrape/completed-jobs');
            const data = await response.json();
            this.completedJobs = data.jobs;
            this.renderCompletedJobs();
        } catch (error) {
            console.error('Failed to load completed jobs:', error);
        }
    }
    
    renderCompletedJobs() {
        const container = document.getElementById('completed-jobs-list');
        if (!container) return; // Container might not exist yet
        
        container.innerHTML = '<h3>Completed Scraping Jobs</h3>';
        
        this.completedJobs.forEach(job => {
            const jobElement = document.createElement('div');
            jobElement.className = 'completed-job-item';
            jobElement.innerHTML = `
                <h4>${job.url}</h4>
                <p>Type: ${job.scraping_type}</p>
                <p>Pages: ${job.result_summary?.pages_scraped || 0}</p>
                <p>Completed: ${new Date(job.completed_at).toLocaleString()}</p>
                <button onclick="dashboard.createVectorDatabase('${job.id}', '${job.url}')">
                    Create Vector Database
                </button>
            `;
            container.appendChild(jobElement);
        });
    }
    
    async createVectorDatabase(jobId, sourceUrl) {
        const name = prompt(`Enter a name for this vector database (source: ${sourceUrl}):`);
        if (!name) return;
        
        try {
            // Initiate asynchronous vector database creation
            const response = await fetch('/api/vector-dbs/create', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    name: name,
                    scraping_job_id: jobId
                })
            });
            
            const result = await response.json();
            if (result.db_id) {
                alert('Vector database creation started in background! The interface remains responsive while processing.');
                this.loadVectorDatabases();
                this.trackVectorDatabaseCreation(result.db_id);
            }
        } catch (error) {
            console.error('Failed to create vector database:', error);
            alert('Failed to create vector database');
        }
    }
    
    async trackVectorDatabaseCreation(dbId) {
        // Non-blocking status checking via polling
        const checkStatus = async () => {
            try {
                const response = await fetch(`/api/vector-dbs/${dbId}/status`);
                const status = await response.json();
                
                if (status.status === 'ready') {
                    this.loadVectorDatabases(); // Refresh the list
                    alert('Vector database is ready for use!');
                } else if (status.status === 'error') {
                    alert('Vector database creation failed!');
                } else {
                    // Still building, check again in 5 seconds (non-blocking)
                    setTimeout(checkStatus, 5000);
                }
            } catch (error) {
                console.error('Failed to check vector database status:', error);
            }
        };
        
        checkStatus();
    }
    
    async loadVectorDatabases() {
        try {
            const response = await fetch('/api/vector-dbs');
            const data = await response.json();
            this.vectorDbs = data.databases;
            this.renderVectorDatabases();
        } catch (error) {
            console.error('Failed to load vector databases:', error);
        }
    }
    
    renderVectorDatabases() {
        const container = document.getElementById('vector-dbs-list');
        container.innerHTML = '';
        
        this.vectorDbs.forEach(db => {
            const dbElement = document.createElement('div');
            dbElement.className = 'vector-db-item';
            dbElement.innerHTML = `
                <h4>${db.name}</h4>
                <p>Source: ${db.source_url}</p>
                <p>Status: <span class="status ${db.status}">${db.status}</span></p>
                <p>Documents: ${db.document_count}</p>
                ${db.status === 'ready' ? 
                    `<button onclick="dashboard.selectDatabase('${db.id}')">Use for Chat</button>` : 
                    '<span>Building...</span>'
                }
            `;
            container.appendChild(dbElement);
        });
    }
    
    async selectDatabase(dbId) {
        const config = {
            vector_db_id: dbId,
            model: document.getElementById('model-select').value,
            config: {
                temperature: parseFloat(document.getElementById('temperature').value)
            }
        };
        
        try {
            const response = await fetch('/api/chat/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(config)
            });
            
            const result = await response.json();
            this.currentSession = result.session_id;
            document.getElementById('chat-interface').style.display = 'block';
            this.clearChatMessages();
        } catch (error) {
            console.error('Failed to start chat session:', error);
        }
    }
    
    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message || !this.currentSession) return;
        
        this.addMessage('user', message);
        input.value = '';
        
        try {
            const response = await fetch('/api/chat/message', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    session_id: this.currentSession,
                    message: message
                })
            });
            
            const result = await response.json();
            this.addMessage('assistant', result.response, result.sources);
        } catch (error) {
            console.error('Failed to send message:', error);
            this.addMessage('assistant', 'Sorry, I encountered an error processing your request.');
        }
    }
    
    addMessage(role, content, sources = []) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        let sourceText = '';
        if (sources && sources.length > 0) {
            sourceText = `<div class="sources"><strong>Sources:</strong><ul>`;
            sources.forEach(source => {
                sourceText += `<li><a href="${source.url}" target="_blank">${source.title}</a></li>`;
            });
            sourceText += `</ul></div>`;
        }
        
        messageDiv.innerHTML = `
            <div class="message-content">${content}</div>
            ${sourceText}
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    clearChatMessages() {
        document.getElementById('chat-messages').innerHTML = '';
    }
    
    toggleDeepOptions() {
        const type = document.getElementById('scraping-type').value;
        const options = document.getElementById('deep-options');
        options.style.display = type === 'deep' ? 'block' : 'none';
    }
    
    updateTemperatureDisplay() {
        const temp = document.getElementById('temperature').value;
        document.getElementById('temp-value').textContent = temp;
    }
}

// Initialize dashboard when page loads
const dashboard = new Dashboard();
```

### Enhanced UI Components for Document Upload

#### File Upload Modal Enhancement
```html
<!-- Enhanced Create Vector DB Modal with Document Upload -->
<div id="create-db-modal" class="modal" style="display: none;">
    <div class="modal-content large-modal">
        <div class="modal-header">
            <h3>Create Enhanced Vector Database</h3>
            <button class="close-modal-btn" onclick="closeModal('create-db-modal')">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="modal-body">
            <form id="create-db-form" enctype="multipart/form-data">
                <div class="form-group">
                    <label>Database Name:</label>
                    <input type="text" id="db-name" required placeholder="Enter a descriptive name">
                </div>
                
                <div class="form-group">
                    <label>Source Scraping Job:</label>
                    <select id="source-job" required>
                        <option value="">Select a completed scraping job</option>
                        <!-- Populated dynamically -->
                    </select>
                </div>
                
                <div class="form-group document-upload-section">
                    <label>Supplementary Documents (Optional):</label>
                    <div class="upload-area">
                        <input type="file" id="document-files" multiple 
                               accept=".pdf,.docx,.md" style="display: none;">
                        
                        <div class="file-drop-zone" id="file-drop-zone">
                            <div class="drop-zone-content">
                                <i class="fas fa-cloud-upload-alt fa-3x"></i>
                                <h4>Drag & Drop Documents Here</h4>
                                <p>or</p>
                                <button type="button" id="select-files-btn" class="file-select-btn">
                                    <i class="fas fa-folder-open"></i> Browse Files
                                </button>
                            </div>
                        </div>
                        
                        <div class="file-upload-info">
                            <div class="supported-formats">
                                <strong>Supported formats:</strong>
                                <span class="format-badge">PDF</span>
                                <span class="format-badge">Word (.docx)</span>
                                <span class="format-badge">Markdown (.md)</span>
                            </div>
                            <div class="upload-limits">
                                <small><i class="fas fa-info-circle"></i> Max size: 50MB per file | Max files: 10</small>
                            </div>
                        </div>
                        
                        <div id="selected-files-list" class="selected-files">
                            <!-- Dynamically populated with selected files -->
                        </div>
                        
                        <div id="upload-progress" class="upload-progress" style="display: none;">
                            <div class="progress-bar">
                                <div class="progress-fill" id="upload-progress-fill"></div>
                            </div>
                            <div class="progress-text" id="upload-progress-text">Uploading...</div>
                        </div>
                    </div>
                </div>
                
                <div class="form-actions">
                    <button type="button" class="cancel-btn" onclick="closeModal('create-db-modal')">
                        Cancel
                    </button>
                    <button type="submit" id="create-db-submit-btn" class="submit-btn">
                        <i class="fas fa-database"></i> Create Vector Database
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
```

#### Enhanced CSS for Document Upload
```css
/* Document Upload Styles */
.large-modal .modal-content {
    max-width: 600px;
    width: 90%;
}

.document-upload-section {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    border: 2px dashed #dee2e6;
    margin: 15px 0;
}

.file-drop-zone {
    border: 2px dashed #007bff;
    border-radius: 8px;
    padding: 40px 20px;
    text-align: center;
    background: #f8f9ff;
    transition: all 0.3s ease;
    cursor: pointer;
}

.file-drop-zone:hover {
    border-color: #0056b3;
    background: #e7f3ff;
}

.file-drop-zone.drag-over {
    border-color: #28a745;
    background: #e8f5e8;
}

.drop-zone-content i {
    color: #007bff;
    margin-bottom: 15px;
}

.file-select-btn {
    background: #007bff;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
    transition: background 0.3s ease;
}

.file-select-btn:hover {
    background: #0056b3;
}

.supported-formats {
    margin: 15px 0 10px 0;
}

.format-badge {
    display: inline-block;
    background: #e9ecef;
    color: #495057;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    margin-right: 8px;
    font-weight: 500;
}

.selected-files {
    margin-top: 15px;
}

.file-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: white;
    padding: 12px 15px;
    border-radius: 6px;
    border: 1px solid #dee2e6;
    margin-bottom: 8px;
}

.file-info {
    display: flex;
    align-items: center;
    flex-grow: 1;
}

.file-icon {
    margin-right: 10px;
    font-size: 18px;
}

.file-icon.pdf { color: #dc3545; }
.file-icon.docx { color: #0066cc; }
.file-icon.md { color: #6f42c1; }

.file-details {
    flex-grow: 1;
}

.file-name {
    font-weight: 500;
    margin-bottom: 2px;
}

.file-size {
    font-size: 12px;
    color: #6c757d;
}

.file-remove {
    background: #dc3545;
    color: white;
    border: none;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
}

.upload-progress {
    margin-top: 15px;
    padding: 15px;
    background: #e3f2fd;
    border-radius: 6px;
}

.form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid #dee2e6;
}

.cancel-btn {
    background: #6c757d;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    cursor: pointer;
}

.submit-btn {
    background: #28a745;
    color: white;
    border: none;
    padding: 10px 25px;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
}

.submit-btn:disabled {
    background: #6c757d;
    cursor: not-allowed;
}
```

#### Enhanced JavaScript for Document Upload
```javascript
// Enhanced Dashboard class with document upload support
class EnhancedDashboard extends Dashboard {
    constructor() {
        super();
        this.selectedFiles = [];
        this.uploadedDocuments = [];
        this.initDocumentUpload();
    }
    
    initDocumentUpload() {
        // File selection button
        document.getElementById('select-files-btn').addEventListener('click', () => {
            document.getElementById('document-files').click();
        });
        
        // File input change
        document.getElementById('document-files').addEventListener('change', (e) => {
            this.handleFileSelection(e.target.files);
        });
        
        // Drag and drop functionality
        const dropZone = document.getElementById('file-drop-zone');
        
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });
        
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('drag-over');
        });
        
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            this.handleFileSelection(e.dataTransfer.files);
        });
        
        // Click to select files
        dropZone.addEventListener('click', (e) => {
            if (e.target === dropZone || e.target.closest('.drop-zone-content')) {
                document.getElementById('document-files').click();
            }
        });
    }
    
    handleFileSelection(files) {
        const maxFiles = 10;
        const maxSize = 50 * 1024 * 1024; // 50MB
        const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/markdown'];
        
        // Convert FileList to Array
        const newFiles = Array.from(files);
        
        // Validate file count
        if (this.selectedFiles.length + newFiles.length > maxFiles) {
            this.showErrorMessage(`Maximum ${maxFiles} files allowed`);
            return;
        }
        
        // Validate and add files
        newFiles.forEach(file => {
            // Check file type
            if (!allowedTypes.includes(file.type) && !file.name.endsWith('.md')) {
                this.showErrorMessage(`Unsupported file type: ${file.name}`);
                return;
            }
            
            // Check file size
            if (file.size > maxSize) {
                this.showErrorMessage(`File too large: ${file.name} (max 50MB)`);
                return;
            }
            
            // Check for duplicates
            if (this.selectedFiles.some(f => f.name === file.name && f.size === file.size)) {
                this.showWarningMessage(`File already selected: ${file.name}`);
                return;
            }
            
            this.selectedFiles.push(file);
        });
        
        this.renderSelectedFiles();
    }
    
    renderSelectedFiles() {
        const container = document.getElementById('selected-files-list');
        
        if (this.selectedFiles.length === 0) {
            container.innerHTML = '';
            return;
        }
        
        container.innerHTML = `
            <h4>Selected Documents (${this.selectedFiles.length})</h4>
            ${this.selectedFiles.map((file, index) => `
                <div class="file-item" data-index="${index}">
                    <div class="file-info">
                        <div class="file-icon ${this.getFileIcon(file.name)}">
                            <i class="fas ${this.getFileIconClass(file.name)}"></i>
                        </div>
                        <div class="file-details">
                            <div class="file-name">${file.name}</div>
                            <div class="file-size">${this.formatFileSize(file.size)}</div>
                        </div>
                    </div>
                    <button type="button" class="file-remove" onclick="dashboard.removeFile(${index})">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `).join('')}
        `;
    }
    
    removeFile(index) {
        this.selectedFiles.splice(index, 1);
        this.renderSelectedFiles();
    }
    
    getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        return ext; // Returns 'pdf', 'docx', or 'md'
    }
    
    getFileIconClass(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        switch (ext) {
            case 'pdf': return 'fa-file-pdf';
            case 'docx': return 'fa-file-word';
            case 'md': return 'fa-file-alt';
            default: return 'fa-file';
        }
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    async uploadDocuments() {
        if (this.selectedFiles.length === 0) {
            return [];
        }
        
        const formData = new FormData();
        this.selectedFiles.forEach((file, index) => {
            formData.append(`document_${index}`, file);
        });
        
        try {
            this.showUploadProgress(0);
            
            const response = await fetch('/api/documents/upload', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('Upload failed');
            }
            
            const result = await response.json();
            this.hideUploadProgress();
            
            return result.uploaded_files;
        } catch (error) {
            this.hideUploadProgress();
            this.showErrorMessage('Failed to upload documents: ' + error.message);
            return [];
        }
    }
    
    showUploadProgress(percent) {
        const progressDiv = document.getElementById('upload-progress');
        const progressFill = document.getElementById('upload-progress-fill');
        const progressText = document.getElementById('upload-progress-text');
        
        progressDiv.style.display = 'block';
        progressFill.style.width = `${percent}%`;
        progressText.textContent = `Uploading documents... ${percent}%`;
    }
    
    hideUploadProgress() {
        document.getElementById('upload-progress').style.display = 'none';
    }
    
    async handleEnhancedCreateVectorDB(e) {
        e.preventDefault();
        
        const submitBtn = document.getElementById('create-db-submit-btn');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        
        try {
            // Upload documents first if any are selected
            let uploadedFiles = [];
            if (this.selectedFiles.length > 0) {
                uploadedFiles = await this.uploadDocuments();
                if (uploadedFiles.length !== this.selectedFiles.length) {
                    throw new Error('Some documents failed to upload');
                }
            }
            
            // Create vector database with optional documents
            const formData = new FormData(e.target);
            const data = {
                name: formData.get('name'),
                scraping_job_id: formData.get('scraping_job_id'),
                uploaded_files: uploadedFiles.map(f => f.blob_name)
            };
            
            const response = await fetch('/api/vector-dbs/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showSuccessMessage('Enhanced vector database creation started! Processing web content and documents...');
                this.closeModal('create-db-modal');
                this.resetCreateForm();
                
                // Track creation progress
                setTimeout(() => {
                    this.loadVectorDatabases();
                    this.loadVectorDatabaseStats();
                }, 1000);
            } else {
                throw new Error(result.error || 'Failed to create vector database');
            }
        } catch (error) {
            this.showErrorMessage(error.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-database"></i> Create Vector Database';
        }
    }
    
    resetCreateForm() {
        document.getElementById('create-db-form').reset();
        this.selectedFiles = [];
        this.renderSelectedFiles();
        this.hideUploadProgress();
    }
    
    showWarningMessage(message) {
        this.showToast(message, 'warning');
    }
}

// Replace the original dashboard initialization
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new EnhancedDashboard();
});
```

## Security Considerations

### Authentication & Authorization
- Implement secure session management
- Use HTTPS for all communications
- Validate and sanitize all user inputs
- Implement rate limiting for API endpoints

### Data Protection
- Encrypt sensitive data at rest
- Use Azure Key Vault for secrets management
- Implement proper access controls
- Regular security audits

### Web Scraping Ethics
- Respect robots.txt files
- Implement appropriate delays between requests
- Monitor and limit resource usage
- Comply with website terms of service

## Comprehensive Testing Strategy

### Testing Philosophy and Approach

The testing strategy for the USYD Web Crawler and RAG solution emphasizes **real-world validation over simulated testing**. All tests must use actual websites, real data, and genuine user interactions to ensure the system works reliably in production environments.

### **CRITICAL TESTING REQUIREMENT: No Simulated Data**
**All testing must be performed using real websites, actual scraped content, and genuine AI model responses. Mock data and simulated responses are prohibited except for unit tests of isolated utility functions.**

### Complete Functionality Testing Checklist

#### **1. Web Scraping Engine Testing**
**Objective**: Verify that the scraping engine can handle diverse real-world websites with different technologies, structures, and content types.

**Required Test Cases**:
- [ ] **Single Page Scraping**
  - [ ] Static HTML pages (news articles, blog posts)
  - [ ] JavaScript-heavy single-page applications (React, Vue, Angular sites)
  - [ ] E-commerce product pages with dynamic content loading
  - [ ] Academic papers and research documentation
  - [ ] Government and institutional websites
  - [ ] Pages with various encoding formats (UTF-8, Latin-1, etc.)
  - [ ] Pages with embedded media (images, videos, PDFs)
  - [ ] Password-protected content (with proper credentials)
  - [ ] Pages with CAPTCHA protection (should handle gracefully)
  - [ ] Mobile-optimized responsive designs

- [ ] **Deep Crawling Testing**
  - [ ] Small websites (10-50 pages) with various link structures
  - [ ] Medium websites (100-500 pages) with complex navigation
  - [ ] Websites with infinite scroll and pagination
  - [ ] Sites with dynamic URL parameters and query strings
  - [ ] Multi-language websites with different URL structures
  - [ ] Sites with broken internal links (should handle gracefully)
  - [ ] Websites with redirect chains and canonical URLs
  - [ ] Sites with different authentication requirements per section
  - [ ] Websites with rate limiting and anti-bot measures
  - [ ] Sites with mixed HTTP/HTTPS content

- [ ] **Sitemap-Based Scraping**
  - [ ] XML sitemaps with standard format
  - [ ] Compressed sitemap files (.gz format)
  - [ ] Sitemap index files pointing to multiple sitemaps
  - [ ] Sitemaps with invalid or inaccessible URLs
  - [ ] Large sitemaps (1000+ URLs)
  - [ ] Sitemaps with non-standard extensions or formats
  - [ ] Sites where sitemap doesn't match actual content
  - [ ] Multilingual sitemaps with hreflang annotations

- [ ] **Content Processing Validation**
  - [ ] HTML content with complex formatting and nested elements
  - [ ] PDF documents embedded in web pages
  - [ ] Content in multiple languages (English, Spanish, French, Chinese, Arabic)
  - [ ] Scientific and technical content with formulas and symbols
  - [ ] Content with tables, lists, and structured data
  - [ ] Pages with minimal text content (image-heavy pages)
  - [ ] Content with special characters and Unicode symbols
  - [ ] Legal documents and terms of service pages
  - [ ] News articles with timestamps and author information
  - [ ] Blog posts with comments and social media integration

#### **2. Vector Database and Search Testing**
**Objective**: Ensure that content is properly embedded, stored, and retrievable through different search methods.

**Required Test Cases**:
- [ ] **Index Creation and Management**
  - [ ] Create indexes for different content types and sizes
  - [ ] Handle index creation failures and recovery
  - [ ] Delete and recreate indexes without data loss
  - [ ] Manage multiple concurrent index operations
  - [ ] Test index size limits and performance degradation
  - [ ] Verify index metadata and schema correctness

- [ ] **Embedding Generation Testing**
  - [ ] Generate embeddings for various content lengths (short, medium, long)
  - [ ] Test embedding generation for different languages
  - [ ] Handle special characters and formatting in embeddings
  - [ ] Verify embedding consistency across multiple generations
  - [ ] Test embedding generation failure scenarios
  - [ ] Validate embedding storage and retrieval accuracy

- [ ] **Search Functionality Testing**
  - [ ] **Semantic Search Testing**:
    - [ ] Questions that require understanding context and meaning
    - [ ] Queries with synonyms and related concepts
    - [ ] Abstract questions requiring inference
    - [ ] Multi-part questions requiring synthesis of information
    - [ ] Questions in different languages matching English content
    - [ ] Conceptual queries without exact keyword matches
  
  - [ ] **Keyword Search Testing**:
    - [ ] Exact phrase matching with quotes
    - [ ] Boolean queries with AND, OR, NOT operators
    - [ ] Wildcard and fuzzy matching
    - [ ] Case-sensitive and case-insensitive searches
    - [ ] Searches with special characters and symbols
    - [ ] Technical term and jargon searches
  
  - [ ] **Hybrid Search Testing**:
    - [ ] Combination queries requiring both semantic and keyword matching
    - [ ] Verify ranking and relevance scoring accuracy
    - [ ] Test search result diversity and coverage
    - [ ] Performance comparison between search types
    - [ ] Edge cases where one search type fails but hybrid succeeds

#### **3. AI Integration and Chat Interface Testing**
**Objective**: Verify that the AI models provide accurate, relevant, and properly sourced responses using real scraped content.

**Required Test Cases**:
- [ ] **Model Performance Testing**
  - [ ] **GPT-4o Model Testing**:
    - [ ] Complex analytical questions requiring deep reasoning
    - [ ] Requests for summaries and synthesis of multiple sources
    - [ ] Creative questions requiring inference and extrapolation
    - [ ] Technical questions requiring specific domain knowledge
    - [ ] Comparative analysis questions across multiple documents
  
  - [ ] **o3-mini Model Testing**:
    - [ ] Simple factual questions with direct answers
    - [ ] Definition and explanation requests
    - [ ] Quick reference and lookup queries
    - [ ] Performance and response time comparison with GPT-4o

- [ ] **Response Quality Validation**
  - [ ] **Accuracy Testing**: Verify all factual claims in AI responses against source material
  - [ ] **Source Attribution**: Ensure all responses include proper citations and links
  - [ ] **Relevance Testing**: Confirm responses directly address user questions
  - [ ] **Completeness Testing**: Verify comprehensive answers for complex queries
  - [ ] **Consistency Testing**: Ask the same question multiple times and verify consistent responses
  
- [ ] **Configuration Parameter Testing**
  - [ ] Temperature settings (0.1, 0.5, 0.7, 0.9, 1.0) and their impact on response creativity
  - [ ] Max token limits and response truncation handling
  - [ ] Context window limitations and long conversation management
  - [ ] System prompt effectiveness and response formatting

- [ ] **Edge Case and Error Handling**
  - [ ] Questions about content not in the vector database
  - [ ] Inappropriate or harmful questions (content filtering)
  - [ ] Questions in languages not supported by the scraped content
  - [ ] Extremely long or complex queries
  - [ ] Rapid-fire question sequences (rate limiting testing)
  - [ ] Conversation context management over long sessions

#### **4. User Interface Testing (Browser-Based)**
**Objective**: Ensure the complete user interface works flawlessly across different browsers, devices, and user interaction patterns.

**Required Test Cases**:
- [ ] **Cross-Browser Compatibility**
  - [ ] Google Chrome (latest and previous version)
  - [ ] Mozilla Firefox (latest and previous version)
  - [ ] Microsoft Edge (latest version)
  - [ ] Safari (latest version on macOS)
  - [ ] Mobile browsers (Chrome Mobile, Safari Mobile)

- [ ] **Responsive Design Testing**
  - [ ] Desktop displays (1920x1080, 1366x768, 2560x1440)
  - [ ] Tablet displays (iPad, Android tablets)
  - [ ] Mobile devices (iPhone, Android phones)
  - [ ] Ultrawide monitors and different aspect ratios
  - [ ] High DPI/Retina displays

- [ ] **Login and Authentication Flow**
  - [ ] Successful login with valid credentials
  - [ ] Failed login attempts with invalid credentials
  - [ ] Session management and automatic logout
  - [ ] Password visibility toggle functionality
  - [ ] Browser password manager integration
  - [ ] Remember me functionality (if implemented)

- [ ] **Web Scraping Interface Testing**
  - [ ] URL input validation and error handling
  - [ ] Scraping type selection and option visibility
  - [ ] Progress bar accuracy and real-time updates
  - [ ] Cancel scraping job functionality
  - [ ] Form submission with various URL formats
  - [ ] Deep crawl parameter validation (depth, page limits)
  - [ ] Error message display for failed scraping jobs

- [ ] **Vector Database Management Interface**
  - [ ] Database list display and refresh functionality
  - [ ] Database selection and activation
  - [ ] Database status indicators (building, ready, error)
  - [ ] Database deletion and confirmation dialogs
  - [ ] Database metadata display (document count, creation date)

- [ ] **Chat Interface Testing**
  - [ ] Model selection dropdown functionality
  - [ ] Search type configuration options
  - [ ] Temperature slider and value display
  - [ ] Message input and send functionality
  - [ ] Enter key message submission
  - [ ] Message display formatting and scrolling
  - [ ] Source link functionality and new tab opening
  - [ ] Chat history persistence and retrieval
  - [ ] Long message handling and text wrapping
  - [ ] Emoji and special character support in messages

- [ ] **Real-Time Updates and WebSocket Testing**
  - [ ] Progress updates during scraping operations
  - [ ] Status changes in vector database list
  - [ ] Connection recovery after network interruptions
  - [ ] Multiple browser tab synchronization
  - [ ] Server restart recovery and reconnection

#### **5. Integration Testing with Real Data**
**Objective**: Validate the complete end-to-end workflow using diverse real-world websites and use cases.

**Required Test Scenarios**:
- [ ] **Complete User Workflows**
  - [ ] **Academic Research Scenario**:
    - [ ] Scrape university research pages or academic journals
    - [ ] Create vector database from scraped research content
    - [ ] Ask complex research questions requiring synthesis
    - [ ] Verify accurate citations and source attribution
  
  - [ ] **News and Media Analysis**:
    - [ ] Scrape news websites with articles from different time periods
    - [ ] Test search across multiple news sources
    - [ ] Ask questions about current events and trends
    - [ ] Verify temporal context and date accuracy
  
  - [ ] **Product Documentation**:
    - [ ] Scrape technical documentation sites (APIs, software manuals)
    - [ ] Test technical questions requiring specific implementation details
    - [ ] Verify code examples and technical accuracy
    - [ ] Test multi-format content (text, code, diagrams)
  
  - [ ] **Corporate Website Analysis**:
    - [ ] Scrape company websites with various page types
    - [ ] Test questions about company policies, products, services
    - [ ] Verify business information accuracy
    - [ ] Test navigation across different website sections

- [ ] **Performance and Scalability Testing**
  - [ ] Test with small websites (10-50 pages)
  - [ ] Test with medium websites (100-500 pages)
  - [ ] Test with large websites (1000+ pages, if feasible)
  - [ ] Measure scraping speed and resource usage
  - [ ] Test concurrent user sessions
  - [ ] Monitor system performance under load
  - [ ] Test database query performance with large datasets

- [ ] **Error Recovery and Resilience Testing**
  - [ ] Network interruption during scraping
  - [ ] Invalid URLs and inaccessible websites
  - [ ] Rate limiting and access denied scenarios
  - [ ] Azure service outages and failover behavior
  - [ ] Database connection failures and recovery
  - [ ] Large file handling and memory management

#### **6. Security and Ethics Testing**
**Objective**: Ensure the system behaves ethically and securely when scraping websites and handling user data.

**Required Test Cases**:
- [ ] **Web Scraping Ethics**
  - [ ] Robots.txt compliance verification
  - [ ] Rate limiting and respectful crawling behavior
  - [ ] Terms of service compliance checking
  - [ ] GDPR and privacy regulation compliance
  - [ ] Content copyright and usage rights verification

- [ ] **Security Testing**
  - [ ] SQL injection prevention in all input fields
  - [ ] Cross-site scripting (XSS) prevention
  - [ ] Authentication bypass attempts
  - [ ] Session hijacking prevention
  - [ ] Input validation and sanitization
  - [ ] Secure storage of API keys and credentials

#### **7. Load and Performance Testing**
**Objective**: Validate system performance under realistic usage patterns and load conditions.

**Required Test Cases**:
- [ ] **User Load Testing**
  - [ ] Single user with multiple concurrent scraping jobs
  - [ ] 10 concurrent users with mixed activities
  - [ ] 50 concurrent users (target system capacity)
  - [ ] 100+ concurrent users (stress testing)
  - [ ] Peak usage scenario simulation

- [ ] **Data Volume Testing**
  - [ ] Small content volumes (1-100 pages)
  - [ ] Medium content volumes (100-1,000 pages)
  - [ ] Large content volumes (1,000-10,000 pages)
  - [ ] Memory usage and garbage collection monitoring
  - [ ] Database performance under various data sizes

### **Testing Tools and Infrastructure**

#### **Automated Testing Tools**
- **Playwright**: For comprehensive browser-based UI testing
- **Locust**: For load testing and performance validation
- **pytest**: For unit and integration testing
- **Selenium**: For additional browser automation where needed

#### **Real Website Test Suite**
Maintain a curated list of real websites covering different technologies and content types:
- **News Sites**: BBC, CNN, Reuters, local news sites
- **Academic**: University websites, research institution pages
- **Technical**: GitHub, Stack Overflow, API documentation sites
- **E-commerce**: Product pages, catalog sites
- **Government**: Official government websites and documents
- **Multilingual**: Sites in different languages and character sets

#### **Testing Data Management**
- **No Mock Data**: All tests use real scraped content
- **Test Result Archiving**: Save test results for regression analysis
- **Performance Baselines**: Establish performance benchmarks with real data
- **Content Validation**: Verify scraped content accuracy against original sources

### **Continuous Testing Process**
1. **Pre-deployment Testing**: Full test suite execution before any deployment
2. **Regression Testing**: Automated testing of all functionality after code changes
3. **User Acceptance Testing**: Real user testing with actual use cases
4. **Performance Monitoring**: Continuous monitoring of system performance in production
5. **Security Audits**: Regular security testing and vulnerability assessments

This comprehensive testing strategy ensures that the USYD Web Crawler and RAG solution is thoroughly validated with real-world data and usage patterns, providing confidence in its production reliability and user experience.

## Deployment Guide

### Prerequisites
- Azure CLI installed and configured
- Azure Developer CLI (AZD) installed
- Docker installed (for local development)
- Python 3.9+ installed

### Recommended AZD Template
Start with the **`azure-search-openai-demo`** template as the foundation:

```bash
azd init --template azure-search-openai-demo
```

### Infrastructure Customizations Required

#### 1. Azure Container Apps Configuration (`infra/containerapp.bicep`)
```bicep
@description('Container App Configuration')
param containerAppName string
param location string = resourceGroup().location
param environmentId string
param imageName string
param azureOpenAIKey string
param azureSearchKey string
param databaseUrl string
param redisUrl string
param secretKey string

resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  properties: {
    managedEnvironmentId: environmentId
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 5000
        allowInsecure: false
        traffic: [
          {
            weight: 100
            latestRevision: true
          }
        ]
      }
      secrets: [
        {
          name: 'azure-openai-key'
          value: azureOpenAIKey
        }
        {
          name: 'azure-search-key'
          value: azureSearchKey
        }
        {
          name: 'database-url'
          value: databaseUrl
        }
        {
          name: 'redis-url'  
          value: redisUrl
        }
        {
          name: 'secret-key'
          value: secretKey
        }
      ]
    }
    template: {
      containers: [
        {
          image: imageName
          name: 'usyd-web-crawler'
          env: [
            {
              name: 'AZURE_OPENAI_KEY'
              secretRef: 'azure-openai-key'
            }
            {
              name: 'AZURE_SEARCH_KEY'
              secretRef: 'azure-search-key'
            }
            {
              name: 'DATABASE_URL'
              secretRef: 'database-url'
            }
            {
              name: 'REDIS_URL'
              secretRef: 'redis-url'
            }
            {
              name: 'FLASK_SECRET_KEY'
              secretRef: 'secret-key'
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: 'https://${azureOpenAIServiceName}.openai.azure.com/'
            }
            {
              name: 'AZURE_SEARCH_ENDPOINT'
              value: 'https://${azureSearchServiceName}.search.windows.net'
            }
            {
              name: 'FLASK_ENV'
              value: 'production'
            }
          ]
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 10
        rules: [
          {
            name: 'http-rule'
            http: {
              metadata: {
                concurrentRequests: '100'
              }
            }
          }
        ]
      }
    }
  }
  tags: {
    'azd-service-name': 'web'
  }
}

output containerAppUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
```

#### 2. PostgreSQL Database (`infra/database.bicep`)
```bicep
@description('PostgreSQL Flexible Server')
param serverName string
param location string = resourceGroup().location
param administratorLogin string
@secure()
param administratorPassword string
param tags object = {}

resource postgresServer 'Microsoft.DBforPostgreSQL/flexibleServers@2022-12-01' = {
  name: serverName
  location: location
  tags: tags
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    administratorLogin: administratorLogin
    administratorLoginPassword: administratorPassword
    version: '14'
    storage: {
      storageSizeGB: 32
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
  }
}

resource database 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2022-12-01' = {
  parent: postgresServer
  name: 'usydrag'
  properties: {
    charset: 'UTF8'
    collation: 'en_US.UTF8'
  }
}

// Allow Azure services to access the database
resource firewallRule 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2022-12-01' = {
  parent: postgresServer
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

output databaseUrl string = 'postgresql://${administratorLogin}:${administratorPassword}@${postgresServer.properties.fullyQualifiedDomainName}:5432/usydrag?sslmode=require'
output serverName string = postgresServer.name
output databaseName string = database.name
```

#### 3. Redis Cache (`infra/redis.bicep`)
```bicep
@description('Azure Cache for Redis')
param cacheName string
param location string = resourceGroup().location
param tags object = {}

resource redisCache 'Microsoft.Cache/redis@2023-08-01' = {
  name: cacheName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'Basic'
      family: 'C'
      capacity: 0
    }
    redisConfiguration: {
      maxmemory-reserved: '30'
      maxfragmentationmemory-reserved: '30'
    }
    enableNonSslPort: false
    redisVersion: '6'
  }
}

output redisUrl string = 'rediss://:${redisCache.listKeys().primaryKey}@${redisCache.properties.hostName}:${redisCache.properties.sslPort}/0'
output redisHostName string = redisCache.properties.hostName
output redisPrimaryKey string = redisCache.listKeys().primaryKey
```

#### 4. Azure OpenAI Service (`infra/openai.bicep`)
```bicep
@description('Azure OpenAI Service')
param openaiServiceName string
param location string = resourceGroup().location
param tags object = {}

resource openaiService 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: openaiServiceName
  location: location
  tags: tags
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: openaiServiceName
    publicNetworkAccess: 'Enabled'
  }
}

// Deploy GPT-4o model
resource gpt4oDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: openaiService
  name: 'gpt-4o'
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-05-13'
    }
    scaleSettings: {
      scaleType: 'Standard'
      capacity: 10
    }
  }
}

// Deploy o3-mini model
resource o3miniDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: openaiService
  name: 'o3-mini'
  properties: {
    model: {
      format: 'OpenAI'
      name: 'o3-mini'
      version: '2024-09-12'
    }
    scaleSettings: {
      scaleType: 'Standard'
      capacity: 10
    }
  }
  dependsOn: [gpt4oDeployment]
}

// Deploy text embedding model
resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: openaiService
  name: 'text-embedding-3-small'
  properties: {
    model: {
      format: 'OpenAI'
      name: 'text-embedding-3-small'
      version: '1'
    }
    scaleSettings: {
      scaleType: 'Standard'
      capacity: 10
    }
  }
  dependsOn: [o1miniDeployment]
}

output openaiEndpoint string = openaiService.properties.endpoint
output openaiKey string = openaiService.listKeys().key1
output openaiServiceName string = openaiService.name
```

#### 5. Azure AI Search Service (`infra/search.bicep`)
```bicep
@description('Azure AI Search Service')
param searchServiceName string
param location string = resourceGroup().location
param tags object = {}

resource searchService 'Microsoft.Search/searchServices@2023-11-01' = {
  name: searchServiceName
  location: location
  tags: tags
  sku: {
    name: 'basic'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
    publicNetworkAccess: 'enabled'
    networkRuleSet: {
      ipRules: []
    }
  }
}

output searchEndpoint string = 'https://${searchService.name}.search.windows.net'
output searchKey string = searchService.listAdminKeys().primaryKey
output searchServiceName string = searchService.name
```

#### 6. Container Apps Environment (`infra/container-apps-environment.bicep`)
```bicep
@description('Container Apps Environment')
param environmentName string
param location string = resourceGroup().location
param logAnalyticsWorkspaceName string
param tags object = {}

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsWorkspaceName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: environmentName
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.properties.customerId
        sharedKey: logAnalyticsWorkspace.listKeys().primarySharedKey
      }
    }
  }
}

output environmentId string = containerAppsEnvironment.id
output environmentName string = containerAppsEnvironment.name
output logAnalyticsWorkspaceId string = logAnalyticsWorkspace.id
```

#### 7. Main Infrastructure Template (`infra/main.bicep`)
```bicep
targetScope = 'subscription'

@description('Name of the resource group')
@minLength(1)
param resourceGroupName string

@description('Location for all resources')
param location string = 'australiaeast'

@description('Environment name (e.g., dev, staging, prod)')
param environmentName string = 'dev'

@description('Unique suffix for resource names')
param resourceToken string = uniqueString(subscription().id, resourceGroupName, location)

@description('Database administrator login')
param databaseAdminLogin string = 'usydadmin'

@description('Database administrator password')
@secure()
param databaseAdminPassword string

@description('Flask secret key')
@secure()
param flaskSecretKey string

var tags = {
  'azd-env-name': environmentName
  'azd-project-name': 'usyd-web-crawler-rag'
}

// Create resource group
resource resourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

// Deploy Log Analytics and Container Apps Environment
module containerAppsEnvironment 'container-apps-environment.bicep' = {
  name: 'container-apps-environment'
  scope: resourceGroup
  params: {
    environmentName: 'cae-${resourceToken}'
    location: location
    logAnalyticsWorkspaceName: 'log-${resourceToken}'
    tags: tags
  }
}

// Deploy PostgreSQL Database
module database 'database.bicep' = {
  name: 'database'
  scope: resourceGroup
  params: {
    serverName: 'psql-${resourceToken}'
    location: location
    administratorLogin: databaseAdminLogin
    administratorPassword: databaseAdminPassword
    tags: tags
  }
}

// Deploy Redis Cache
module redis 'redis.bicep' = {
  name: 'redis'
  scope: resourceGroup
  params: {
    cacheName: 'redis-${resourceToken}'
    location: location
    tags: tags
  }
}

// Deploy Azure OpenAI Service
module openai 'openai.bicep' = {
  name: 'openai'
  scope: resourceGroup
  params: {
    openaiServiceName: 'oai-${resourceToken}'
    location: location
    tags: tags
  }
}

// Deploy Azure AI Search Service
module search 'search.bicep' = {
  name: 'search'
  scope: resourceGroup
  params: {
    searchServiceName: 'srch-${resourceToken}'
    location: location
    tags: tags
  }
}

// Deploy Container App
module containerApp 'containerapp.bicep' = {
  name: 'container-app'
  scope: resourceGroup
  params: {
    containerAppName: 'ca-usyd-${resourceToken}'
    location: location
    environmentId: containerAppsEnvironment.outputs.environmentId
    imageName: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest' // This will be updated during deployment
    azureOpenAIKey: openai.outputs.openaiKey
    azureSearchKey: search.outputs.searchKey
    databaseUrl: database.outputs.databaseUrl
    redisUrl: redis.outputs.redisUrl
    secretKey: flaskSecretKey
  }
  dependsOn: [
    containerAppsEnvironment
    database
    redis
    openai
    search
  ]
}

// Outputs for the application
output AZURE_LOCATION string = location
output AZURE_RESOURCE_GROUP_NAME string = resourceGroup.name
output AZURE_CONTAINER_APP_NAME string = containerApp.outputs.containerAppUrl
output AZURE_OPENAI_ENDPOINT string = openai.outputs.openaiEndpoint
output AZURE_OPENAI_SERVICE_NAME string = openai.outputs.openaiServiceName
output AZURE_SEARCH_ENDPOINT string = search.outputs.searchEndpoint
output AZURE_SEARCH_SERVICE_NAME string = search.outputs.searchServiceName
output DATABASE_URL string = database.outputs.databaseUrl
output REDIS_URL string = redis.outputs.redisUrl
```

#### 8. Main Parameters File (`infra/main.parameters.json`)
```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "resourceGroupName": {
      "value": "${AZURE_RESOURCE_GROUP_NAME}"
    },
    "location": {
      "value": "${AZURE_LOCATION}"
    },
    "environmentName": {
      "value": "${AZURE_ENV_NAME}"
    },
    "databaseAdminLogin": {
      "value": "${DATABASE_ADMIN_LOGIN}"
    },
    "databaseAdminPassword": {
      "value": "${DATABASE_ADMIN_PASSWORD}"
    },
    "flaskSecretKey": {
      "value": "${FLASK_SECRET_KEY}"
    }
  }
}
```

### Complete AZD Configuration Files

#### 1. Azure.yaml Configuration
```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/Azure/azure-dev/main/schemas/v1.0/azure.yaml.json

name: usyd-web-crawler-rag
metadata:
  template: usyd-web-crawler-rag@0.0.1-beta

services:
  web:
    project: ./src
    language: python
    host: containerapp
    docker:
      path: ./Dockerfile
      context: ./src

hooks:
  predeploy:
    shell: sh
    run: |
      echo "Setting up pre-deployment environment..."
      # Ensure all environment variables are set
      if [ -z "$DATABASE_ADMIN_PASSWORD" ]; then
        echo "Generating database admin password..."
        export DATABASE_ADMIN_PASSWORD=$(openssl rand -base64 32)
      fi
      if [ -z "$FLASK_SECRET_KEY" ]; then
        echo "Generating Flask secret key..."
        export FLASK_SECRET_KEY=$(openssl rand -base64 32)
      fi
      echo "Pre-deployment setup complete."
      
  postdeploy:
    shell: sh
    run: |
      echo "Running post-deployment configuration..."
      echo "Creating database tables..."
      python scripts/init_db.py
      echo "Setting up search indexes..."
      python scripts/setup_search_indexes.py
      echo "Validating deployment..."
      python scripts/validate_deployment.py
      echo "Post-deployment configuration complete."
```

#### 2. Environment Configuration Template (`.env.example`)
```bash
# Azure Configuration
AZURE_SUBSCRIPTION_ID=
AZURE_LOCATION=australiaeast
AZURE_RESOURCE_GROUP_NAME=rg-usyd-web-crawler-rag
AZURE_ENV_NAME=usyd-rag-dev

# Database Configuration
DATABASE_ADMIN_LOGIN=usydadmin
DATABASE_ADMIN_PASSWORD=
DATABASE_URL=

# Azure Services
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_KEY=
AZURE_OPENAI_SERVICE_NAME=
AZURE_SEARCH_ENDPOINT=
AZURE_SEARCH_KEY=
AZURE_SEARCH_SERVICE_NAME=

# Redis Configuration
REDIS_URL=

# Application Configuration
FLASK_SECRET_KEY=
FLASK_ENV=production
FLASK_DEBUG=false

# Web Scraping Configuration
CRAWL4AI_USER_AGENT=USYD-Web-Crawler/1.0
CRAWL4AI_DELAY=2
CRAWL4AI_MAX_DEPTH=5
CRAWL4AI_MAX_PAGES=1000

# AI Configuration
DEFAULT_MODEL=gpt-4o
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=1000
EMBEDDING_MODEL=text-embedding-3-small

# Vector Database Configuration
DEFAULT_CHUNK_SIZE=1000
DEFAULT_CHUNK_OVERLAP=200
DEFAULT_TOP_K=5
```

#### 3. Complete Dockerfile
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    unzip \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set Chrome binary path for Selenium and web scraping
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_DRIVER=/usr/bin/chromedriver
ENV DISPLAY=:99

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Create necessary directories
RUN mkdir -p /app/logs /app/data/temp

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Start application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "--keep-alive", "2", "--max-requests", "1000", "--max-requests-jitter", "100", "app:app"]
```

#### 4. Database Initialization Script (`scripts/init_db.py`)
```python
#!/usr/bin/env python3
"""
Database initialization script for USYD Web Crawler and RAG application.
This script creates all necessary database tables and initial data.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database_tables():
    """Create all database tables"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)
    
    try:
        # Create database engine
        engine = create_engine(database_url)
        
        # SQL statements to create tables
        create_tables_sql = """
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        );
        
        -- Scraping jobs table
        CREATE TABLE IF NOT EXISTS scraping_jobs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            url VARCHAR(2048) NOT NULL,
            scraping_type VARCHAR(20) NOT NULL CHECK (scraping_type IN ('single', 'deep', 'sitemap')),
            status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
            config JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            result_summary JSONB,
            error_message TEXT
        );
        
        -- Vector databases table
        CREATE TABLE IF NOT EXISTS vector_databases (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            name VARCHAR(100) NOT NULL,
            source_url VARCHAR(2048) NOT NULL,
            azure_index_name VARCHAR(100) NOT NULL UNIQUE,
            document_count INTEGER DEFAULT 0,
            status VARCHAR(20) DEFAULT 'building' CHECK (status IN ('building', 'ready', 'error')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Chat sessions table
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            vector_db_id INTEGER REFERENCES vector_databases(id) ON DELETE CASCADE,
            model_name VARCHAR(50) NOT NULL,
            config JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Chat messages table
        CREATE TABLE IF NOT EXISTS chat_messages (
            id SERIAL PRIMARY KEY,
            session_id INTEGER REFERENCES chat_sessions(id) ON DELETE CASCADE,
            role VARCHAR(10) NOT NULL CHECK (role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_scraping_jobs_user_id ON scraping_jobs(user_id);
        CREATE INDEX IF NOT EXISTS idx_scraping_jobs_status ON scraping_jobs(status);
        CREATE INDEX IF NOT EXISTS idx_vector_databases_user_id ON vector_databases(user_id);
        CREATE INDEX IF NOT EXISTS idx_vector_databases_status ON vector_databases(status);
        CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
        CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);
        
        -- Create trigger to update updated_at timestamp
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        CREATE TRIGGER update_vector_databases_updated_at 
            BEFORE UPDATE ON vector_databases 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
        
        # Execute the SQL statements
        with engine.connect() as connection:
            # Split and execute each statement
            statements = create_tables_sql.split(';')
            for statement in statements:
                statement = statement.strip()
                if statement:
                    connection.execute(text(statement))
            
            connection.commit()
        
        logger.info("Database tables created successfully")
        
        # Create default admin user if it doesn't exist
        create_default_user(engine)
        
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

def create_default_user(engine):
    """Create a default admin user"""
    try:
        import bcrypt
        
        # Default credentials (change these in production)
        default_username = os.getenv('DEFAULT_ADMIN_USERNAME', 'admin')
        default_password = os.getenv('DEFAULT_ADMIN_PASSWORD', 'admin123')
        
        # Hash the password
        password_hash = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        with engine.connect() as connection:
            # Check if user already exists
            result = connection.execute(
                text("SELECT id FROM users WHERE username = :username"),
                {"username": default_username}
            )
            
            if result.fetchone() is None:
                # Create the default user
                connection.execute(
                    text("INSERT INTO users (username, password_hash) VALUES (:username, :password_hash)"),
                    {"username": default_username, "password_hash": password_hash}
                )
                connection.commit()
                logger.info(f"Default admin user '{default_username}' created")
            else:
                logger.info(f"Default admin user '{default_username}' already exists")
                
    except Exception as e:
        logger.warning(f"Could not create default user: {e}")

if __name__ == "__main__":
    logger.info("Initializing database...")
    create_database_tables()
    logger.info("Database initialization complete")
```

#### 5. Search Index Setup Script (`scripts/setup_search_indexes.py`)
```python
#!/usr/bin/env python3
"""
Azure AI Search index setup script for USYD Web Crawler and RAG application.
This script creates the necessary search indexes with proper schemas.
"""

import os
import sys
import logging
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SearchField, SearchFieldDataType, SimpleField, 
    SearchableField, VectorSearch, VectorSearchProfile,
    HnswAlgorithmConfiguration, VectorSearchAlgorithmConfiguration
)
from azure.core.credentials import AzureKeyCredential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_search_indexes():
    """Create Azure AI Search indexes with proper vector configuration"""
    
    # Get Azure Search configuration from environment
    search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    search_key = os.getenv('AZURE_SEARCH_KEY')
    
    if not search_endpoint or not search_key:
        logger.error("Azure Search configuration not found in environment variables")
        sys.exit(1)
    
    try:
        # Create search index client
        credential = AzureKeyCredential(search_key)
        index_client = SearchIndexClient(endpoint=search_endpoint, credential=credential)
        
        # Define the search index schema
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="content", type=SearchFieldDataType.String, analyzer_name="en.microsoft"),
            SearchableField(name="title", type=SearchFieldDataType.String, analyzer_name="en.microsoft"),
            SimpleField(name="url", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="source_type", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="created_at", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
            SimpleField(name="user_id", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="vector_db_id", type=SearchFieldDataType.String, filterable=True),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,  # text-embedding-3-small dimension
                vector_search_profile_name="default-vector-profile"
            ),
            SearchableField(name="metadata", type=SearchFieldDataType.String, analyzer_name="keyword")
        ]
        
        # Configure vector search
        vector_search = VectorSearch(
            profiles=[
                VectorSearchProfile(
                    name="default-vector-profile",
                    algorithm_configuration_name="default-hnsw-config"
                )
            ],
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="default-hnsw-config",
                    parameters={
                        "m": 4,
                        "efConstruction": 400,
                        "efSearch": 500,
                        "metric": "cosine"
                    }
                )
            ]
        )
        
        # Create the base index for document storage
        base_index = SearchIndex(
            name="usyd-documents-base",
            fields=fields,
            vector_search=vector_search
        )
        
        # Create or update the index
        logger.info("Creating base search index...")
        index_client.create_or_update_index(base_index)
        logger.info("Base search index created successfully")
        
        # Test the index
        test_search_index(index_client, "usyd-documents-base")
        
    except Exception as e:
        logger.error(f"Error creating search indexes: {e}")
        sys.exit(1)

def test_search_index(index_client, index_name):
    """Test the created search index"""
    try:
        # Get the index to verify it was created
        index = index_client.get_index(index_name)
        logger.info(f"Index '{index_name}' verified successfully")
        logger.info(f"Index has {len(index.fields)} fields")
        
        # List all indexes
        indexes = list(index_client.list_indexes())
        logger.info(f"Total indexes in service: {len(indexes)}")
        
    except Exception as e:
        logger.error(f"Error testing search index: {e}")

if __name__ == "__main__":
    logger.info("Setting up Azure AI Search indexes...")
    create_search_indexes()
    logger.info("Search index setup complete")
```

#### 6. Deployment Validation Script (Enhanced)
```python
#!/usr/bin/env python3
"""
Enhanced deployment validation script for USYD Web Crawler and RAG application.
This script validates all Azure services and application components.
"""

import os
import sys
import logging
import requests
import time
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
import psycopg2
import redis

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_environment():
    """Validate all required services are accessible"""
    logger.info("Starting deployment validation...")
    
    errors = []
    warnings = []
    
    # Validate environment variables
    required_vars = [
        'DATABASE_URL', 'REDIS_URL', 'AZURE_OPENAI_ENDPOINT', 
        'AZURE_OPENAI_KEY', 'AZURE_SEARCH_ENDPOINT', 'AZURE_SEARCH_KEY'
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")
    
    if errors:
        logger.error("Environment validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        return False
    
    # Test database connection
    if not test_database_connection():
        errors.append("Database connection failed")
    
    # Test Redis connection
    if not test_redis_connection():
        errors.append("Redis connection failed")
    
    # Test Azure OpenAI connection
    if not test_azure_openai_connection():
        errors.append("Azure OpenAI connection failed")
    
    # Test Azure Search connection
    if not test_azure_search_connection():
        errors.append("Azure Search connection failed")
    
    # Test application health endpoint
    if not test_application_health():
        warnings.append("Application health endpoint not accessible (may be normal during deployment)")
    
    # Report results
    if errors:
        logger.error("❌ Validation failed with errors:")
        for error in errors:
            logger.error(f"  - {error}")
        return False
    
    if warnings:
        logger.warning("⚠️  Validation completed with warnings:")
        for warning in warnings:
            logger.warning(f"  - {warning}")
    
    logger.info("✅ All critical services validated successfully!")
    return True

def test_database_connection():
    """Test PostgreSQL database connection"""
    try:
        database_url = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(database_url)
        
        # Test basic query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        logger.info("✓ Database connection successful")
        logger.info(f"  Database version: {version[0]}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False

def test_redis_connection():
    """Test Redis connection"""
    try:
        redis_url = os.getenv('REDIS_URL')
        r = redis.from_url(redis_url)
        
        # Test basic operations
        r.ping()
        r.set('test_key', 'test_value', ex=10)
        value = r.get('test_key')
        r.delete('test_key')
        
        logger.info("✓ Redis connection successful")
        logger.info(f"  Redis test operation completed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Redis connection failed: {e}")
        return False

def test_azure_openai_connection():
    """Test Azure OpenAI connection and models"""
    try:
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version="2024-02-01",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
        # Test text embedding
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input="This is a test embedding"
        )
        
        if response.data and len(response.data) > 0:
            embedding_dim = len(response.data[0].embedding)
            logger.info("✓ Azure OpenAI connection successful")
            logger.info(f"  Embedding model working, dimension: {embedding_dim}")
            
            # Test GPT-4o model
            try:
                chat_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": "Hello, this is a test."}],
                    max_tokens=10
                )
                logger.info("✓ GPT-4o model accessible")
            except Exception as e:
                logger.warning(f"⚠️  GPT-4o model test failed: {e}")
            
            # Test o3-mini model
            try:
                chat_response = client.chat.completions.create(
                    model="o3-mini",
                    messages=[{"role": "user", "content": "Hello, this is a test."}],
                    max_tokens=10
                )
                logger.info("✓ o3-mini model accessible")
            except Exception as e:
                logger.warning(f"⚠️  o3-mini model test failed: {e}")
            
            return True
        else:
            logger.error("✗ Azure OpenAI embedding test failed - no data returned")
            return False
            
    except Exception as e:
        logger.error(f"✗ Azure OpenAI connection failed: {e}")
        return False

def test_azure_search_connection():
    """Test Azure AI Search connection"""
    try:
        search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        search_key = os.getenv("AZURE_SEARCH_KEY")
        
        credential = AzureKeyCredential(search_key)
        index_client = SearchIndexClient(endpoint=search_endpoint, credential=credential)
        
        # List indexes
        indexes = list(index_client.list_indexes())
        logger.info("✓ Azure Search connection successful")
        logger.info(f"  Found {len(indexes)} search indexes")
        
        # Check for base index
        base_index_exists = any(idx.name == "usyd-documents-base" for idx in indexes)
        if base_index_exists:
            logger.info("✓ Base search index found")
        else:
            logger.warning("⚠️  Base search index not found - may need to run setup script")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Azure Search connection failed: {e}")
        return False

def test_application_health():
    """Test application health endpoint"""
    try:
        # Try to determine the application URL
        app_url = os.getenv('AZURE_CONTAINER_APP_URL')
        if not app_url:
            # Try localhost for local testing
            app_url = "http://localhost:5000"
        
        # Test health endpoint
        health_url = f"{app_url}/api/health"
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            logger.info("✓ Application health endpoint accessible")
            return True
        else:
            logger.warning(f"⚠️  Application health endpoint returned status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.warning(f"⚠️  Application health endpoint not accessible: {e}")
        return False
    except Exception as e:
        logger.warning(f"⚠️  Application health test failed: {e}")
        return False

if __name__ == "__main__":
    success = validate_environment()
    
    if success:
        logger.info("🎉 Deployment validation completed successfully!")
        sys.exit(0)
    else:
        logger.error("💥 Deployment validation failed!")
        sys.exit(1)
```

### AZD Deployment Instructions for Coder Agents

When implementing the USYD Web Crawler and RAG application, coder agents must create all the above infrastructure files in addition to the application code. The deployment process follows these steps:

1. **Create Infrastructure Directory Structure**:
   ```
   infra/
   ├── main.bicep
   ├── main.parameters.json
   ├── containerapp.bicep
   ├── database.bicep
   ├── redis.bicep
   ├── openai.bicep
   ├── search.bicep
   └── container-apps-environment.bicep
   ```

2. **Create Scripts Directory**:
   ```
   scripts/
   ├── init_db.py
   ├── setup_search_indexes.py
   └── validate_deployment.py
   ```

3. **Create Configuration Files**:
   - `azure.yaml` - AZD configuration
   - `Dockerfile` - Container configuration
   - `.env.example` - Environment template

4. **Deploy Using AZD**:
   ```bash
   azd init
   azd up
   ```

The infrastructure files provide:
- **Complete resource provisioning** for all Azure services
- **Proper security configuration** with secrets management
- **Scalable architecture** with auto-scaling capabilities
- **Monitoring and logging** integration
- **Database initialization** and setup scripts
- **Service validation** and health checks

All these files are **mandatory** for a successful deployment and must be created by the coder agent as part of the complete implementation.
