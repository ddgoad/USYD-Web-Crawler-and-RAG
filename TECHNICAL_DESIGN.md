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

## Solution Architecture Overview

### How the Components Work Together

The USYD Web Crawler and RAG solution is designed as a multi-layered architecture where each component serves a specific purpose and integrates seamlessly with others to provide a complete user experience.

#### **Frontend Layer - User Interface**
The user interface is built as a modern, responsive web application using Flask templates with HTML, CSS, and JavaScript. The interface is divided into two main functional areas:

1. **Web Scraping Control Panel**: This section allows users to configure and initiate web scraping operations. Users can specify the target URL, choose scraping modes (single page, deep crawl, or sitemap-based), and set parameters like crawl depth and page limits. When a scraping job is initiated, the interface provides real-time progress feedback through WebSocket connections, showing users exactly what's happening as their content is being processed.

2. **Chat Interface**: Once vector databases are created from scraped content, users can select a database and interact with it through an AI-powered chat interface. The interface allows users to choose between different AI models (GPT-4o or o3-mini), adjust search parameters (semantic, keyword, or hybrid search), and modify AI behavior settings like temperature.

#### **Backend API Layer - Business Logic**
The Flask-based backend serves as the orchestration layer that coordinates all system components. It handles user authentication, manages scraping jobs, interfaces with Azure services, and provides RESTful API endpoints for the frontend. The backend is designed to be stateless and scalable, with session management handled through Redis for high availability.

#### **Web Scraping Engine - Content Acquisition**
The scraping engine is built around Crawl4AI, a modern web scraping framework that handles JavaScript-heavy websites, respects robots.txt files, and provides intelligent content extraction. The engine operates in three distinct modes:

- **Single Page Mode**: Extracts content from a specific URL, perfect for scraping individual articles, product pages, or documents
- **Deep Crawl Mode**: Systematically explores a website by following internal links up to a specified depth, ideal for comprehensive site analysis
- **Sitemap Mode**: Uses XML sitemaps to efficiently discover and scrape all important pages on a website

The scraping process is asynchronous, using Celery workers to handle jobs in the background while providing real-time progress updates to users.

#### **Content Processing Pipeline - Data Transformation**
Once content is scraped, it goes through a sophisticated processing pipeline:

1. **Content Cleaning**: Raw HTML is processed to extract meaningful text, removing navigation elements, advertisements, and boilerplate content
2. **Text Chunking**: Large documents are intelligently split into smaller, semantically coherent chunks that are optimal for embedding and retrieval
3. **Metadata Extraction**: Important metadata like titles, URLs, publication dates, and content structure is preserved for search and citation purposes
4. **Embedding Generation**: Text chunks are converted into high-dimensional vector representations using Azure OpenAI's embedding models

#### **Vector Database Layer - Intelligent Storage**
Azure AI Search serves as the vector database, providing both traditional keyword search and semantic vector search capabilities. The system creates separate search indexes for each scraping job, allowing users to maintain multiple knowledge bases. The vector database supports:

- **Semantic Search**: Finding content based on meaning and context rather than exact keyword matches
- **Keyword Search**: Traditional full-text search for precise term matching
- **Hybrid Search**: Combining both approaches for optimal retrieval accuracy

#### **AI Integration Layer - Intelligent Responses**
The AI layer uses Azure OpenAI services to provide intelligent responses to user queries. The system implements a Retrieval-Augmented Generation (RAG) approach:

1. **Query Processing**: User questions are analyzed and converted into appropriate search queries
2. **Content Retrieval**: Relevant chunks are retrieved from the vector database using the selected search method
3. **Context Assembly**: Retrieved chunks are assembled into a coherent context for the AI model
4. **Response Generation**: The AI model generates responses based on the retrieved content, ensuring accuracy and relevance
5. **Source Attribution**: Responses include citations and links back to original sources

#### **Background Processing - Scalable Operations**
All heavy computational tasks (web scraping, content processing, embedding generation) are handled by background workers using Celery and Redis. This architecture ensures:

- **Responsiveness**: The user interface remains responsive during long-running operations
- **Scalability**: Multiple workers can process jobs in parallel
- **Reliability**: Failed jobs can be retried automatically
- **Progress Tracking**: Real-time status updates keep users informed of job progress

#### **Data Persistence - Reliable Storage**
The system uses PostgreSQL for storing user data, job metadata, and application state. This includes:

- **User Management**: Authentication credentials and user preferences
- **Job Tracking**: Scraping job configurations, status, and results
- **Vector Database Metadata**: Information about created indexes and their contents
- **Chat History**: Conversation logs for user reference and system improvement

#### **Integration Flow - End-to-End Process**
The complete user journey follows this integrated flow:

1. **Authentication**: Users log in through the secure authentication system
2. **Job Configuration**: Users specify scraping parameters through the intuitive interface
3. **Content Acquisition**: The scraping engine processes websites according to user specifications
4. **Content Processing**: Raw content is cleaned, chunked, and embedded automatically
5. **Index Creation**: Processed content is stored in Azure AI Search with appropriate metadata
6. **Interactive Querying**: Users can immediately begin asking questions about the scraped content
7. **Intelligent Responses**: The AI system provides accurate, source-attributed answers
8. **Continuous Learning**: The system learns from user interactions to improve future responses

This integrated architecture ensures that users have a seamless experience from content discovery to intelligent interaction, while the system maintains high performance, reliability, and scalability.

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
- **Deployment**: Azure Container Apps with AZD

### Python Dependencies
The complete requirements.txt file includes all necessary dependencies organized by functionality. See the `requirements.txt` file in the project root for the comprehensive list of over 100 dependencies covering web scraping, AI integration, vector databases, testing, monitoring, and development tools.

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

3. **Vector Database Management**
   - Automatic text chunking and embedding
   - Vector storage in Azure AI Search
   - Metadata preservation
   - Search index management

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

### 3. Vector Database Service (`vector_store.py`)
```python
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

class VectorStoreService:
    def __init__(self):
        self.search_client = SearchClient(
            endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            index_name=os.getenv("AZURE_SEARCH_INDEX"),
            credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY"))
        )
    
    def create_index(self, index_name: str) -> bool:
        """Create a new search index"""
        pass
    
    def add_documents(self, documents: List[dict]) -> bool:
        """Add documents to vector store"""
        pass
    
    def search(self, query: str, search_type: str = "semantic") -> List[dict]:
        """Search documents in vector store"""
        pass
    
    def delete_index(self, index_name: str) -> bool:
        """Delete a search index"""
        pass
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

#### Vector Databases Table
```sql
CREATE TABLE vector_databases (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(100) NOT NULL,
    source_url VARCHAR(2048) NOT NULL,
    azure_index_name VARCHAR(100) NOT NULL,
    document_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'building', -- 'building', 'ready', 'error'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

POST /api/vector-dbs/create
- Body: {"name": "string", "scraping_job_id": "string"}
- Response: {"db_id": "string", "status": "created"}

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
    grid-template-columns: 1fr 1fr;
    gap: 30px;
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
                    progressText.textContent = 'Scraping completed! Building vector database...';
                    this.loadVectorDatabases();
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
