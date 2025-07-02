## Web Crawler and RAG Solution

![Azure](https://img.shields.io/badge/azure-%230072C6.svg?style=for-the-badge&logo=microsoftazure&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-74aa9c?style=for-the-badge&logo=openai&logoColor=white)

![Screenshot 2025-07-01 195748](https://github.com/user-attachments/assets/df0e601b-5b0b-48d7-bcd0-d19787e653ee)

A comprehensive web application that enables users to scrape websites, convert content to vector databases from multiple sources (uploaded and scrapped), and interact with AI agents based on scraped and uploaded content. Built with modern cloud-native architecture on Azure.

## 🌟 Features

### 🕷️ Intelligent Web Scraping
- **Single Page Scraping**: Extract content from individual URLs
- **Deep Crawling**: Systematically explore websites with configurable depth
- **Sitemap-Based Scraping**: Efficient discovery using XML sitemaps
- **Real-time Progress Tracking**: Live updates during scraping operations
- **Ethical Scraping**: Respects robots.txt and implements rate limiting

### 🧠 AI-Powered Knowledge Base
- **Vector Database Creation**: Automatic conversion of scraped content to embeddings
- **Multiple Search Types**: Semantic, keyword, and hybrid search capabilities
- **Source Attribution**: All AI responses include proper citations and links
- **Model Selection**: Choose between GPT-4o and o3-mini models
- **Configurable Parameters**: Adjust temperature, token limits, and search settings

### 💬 Interactive Chat Interface
- **Real-time Messaging**: Instant responses with WebSocket support
- **Conversation History**: Persistent chat sessions and context management
- **Source Integration**: Clickable links to original content
- **Multi-format Support**: Handles text, code, and technical documentation

### 🔐 Enterprise-Ready Security
- **User Authentication**: Secure login and session management
- **Data Isolation**: User-specific content and vector databases
- **Azure Key Vault**: Secure secrets and API key management
- **Input Validation**: Comprehensive sanitization and security measures

## 🏗️ Architecture

The application follows a modern, scalable architecture deployed on Azure:

- **Frontend**: Responsive web interface with HTML5, CSS3, and JavaScript
- **Backend**: Flask-based API with RESTful endpoints
- **Web Scraping**: Crawl4AI for intelligent content extraction
- **Vector Database**: Azure AI Search for semantic and keyword search
- **AI Integration**: Azure OpenAI with GPT-4o and o3-mini models
- **Database**: PostgreSQL for user data and metadata
- **Caching**: Redis for session management and task queues
- **Hosting**: Azure Container Apps with auto-scaling
- **Deployment**: Azure Developer CLI (AZD) for infrastructure as code

## 🚀 Quick Start

### Prerequisites

**Required Tools:**
- Python 3.9 or higher
- pip package manager
- Git
- Docker (for containerization)

**For Azure Deployment:**
- Azure CLI
- Azure Developer CLI (azd)
- Active Azure subscription

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/ddgoad/USYD-Web-Crawler-and-RAG.git
   cd USYD-Web-Crawler-and-RAG
   ```

2. **Run the automated setup script**
   ```bash
   python setup_dev.py
   ```

3. **Configure environment variables**
   ```bash
   # Edit .env file with your actual configuration values
   nano .env
   ```

4. **Initialize the database**
   ```bash
   python scripts/init_db.py
   ```

5. **Start the application**
   ```bash
   # Terminal 1: Start the Flask app
   python app.py

   # Terminal 2: Start the Celery worker (for background tasks)
   python worker.py
   ```

6. **Open your browser**
   Navigate to `http://localhost:5000`
   
   **Default credentials**: `admin` / `admin123`

### Azure Deployment

1. **Login to Azure**
   ```bash
   azd auth login
   az login
   ```

2. **Deploy the infrastructure and application**
   ```bash
   azd up
   ```

3. **Validate the deployment**
   ```bash
   python scripts/validate_deployment.py
   ```

## 🚀 Quick Start

### Prerequisites

- **Azure Subscription** with sufficient credits
- **Azure CLI** and **Azure Developer CLI (AZD)** installed
- **Docker** for local development
- **Python 3.9+** for local testing

### Deployment

1. **Clone the Repository**
   ```bash
   git clone https://github.com/ddgoad/USYD-Web-Crawler-and-RAG.git
   cd USYD-Web-Crawler-and-RAG
   ```

2. **Initialize AZD Environment**
   ```bash
   azd auth login
   azd init
   ```

3. **Configure Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with your Azure configuration
   ```

4. **Deploy to Azure**
   ```bash
   azd up
   ```

5. **Access the Application**
   - The deployment will provide a URL to access your application
   - Default credentials: `admin` / `admin123` (change in production)

## 📖 Documentation

### For Developers
- **[Technical Design Document](./TECHNICAL_DESIGN.md)** - Comprehensive architecture and implementation guide
- **[Implementation Issue](../../issues/1)** - Detailed requirements for building the application

### For Users
- **Web Interface**: Access through the deployed Azure Container App URL
- **API Documentation**: RESTful endpoints for programmatic access
- **Configuration Guide**: Environment variables and settings

## 🔧 Technology Stack

### Core Technologies
- **Backend**: Flask 3.0+, Python 3.9+
- **Web Scraping**: Crawl4AI 0.3+
- **AI Services**: Azure OpenAI (GPT-4o, o3-mini, text-embedding-3-small)
- **Vector Database**: Azure AI Search
- **Database**: PostgreSQL (Azure Database for PostgreSQL)
- **Caching**: Redis (Azure Cache for Redis)
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)

### Azure Services
- **Azure Container Apps** - Scalable application hosting
- **Azure OpenAI Service** - AI model access and embeddings
- **Azure AI Search** - Vector database and search capabilities
- **Azure Database for PostgreSQL** - User data and metadata storage
- **Azure Cache for Redis** - Session management and task queues
- **Azure Key Vault** - Secure secrets management
- **Azure Application Insights** - Monitoring and logging

## 📊 Use Cases

### Academic Research
- Scrape university websites and research papers
- Create searchable knowledge bases from academic content
- Ask complex research questions requiring synthesis
- Get accurate citations and source attribution

### News and Media Analysis
- Monitor news websites and extract articles
- Search across multiple news sources
- Analyze trends and current events
- Track temporal context and publication dates

### Technical Documentation
- Scrape API documentation and software manuals
- Create searchable technical knowledge bases
- Get specific implementation details and code examples
- Access multi-format content (text, code, diagrams)

### Business Intelligence
- Analyze company websites and policies
- Extract product and service information
- Monitor competitor information
- Create business knowledge repositories

## 🛡️ Security and Compliance

- **Data Encryption**: All data encrypted at rest and in transit
- **Authentication**: Secure user authentication and session management
- **Input Validation**: Comprehensive sanitization of all user inputs
- **Rate Limiting**: Protection against abuse and excessive usage
- **Ethical Scraping**: Respects robots.txt and website terms of service
- **Privacy Compliance**: GDPR and privacy regulation adherence

## 📈 Performance and Scalability

- **Auto-scaling**: Handles 1-10 container instances based on demand
- **Concurrent Users**: Supports 100+ simultaneous users
- **Response Times**: Sub-2-second search queries for typical datasets
- **Large Datasets**: Efficiently handles 1,000-10,000+ pages
- **Real-time Updates**: WebSocket-based progress tracking and notifications

## 🧪 Testing Strategy

The application emphasizes **real-world validation** with comprehensive testing:

- **Real Website Testing**: All scraping tested with actual websites (no mock data)
- **Browser Compatibility**: Chrome, Firefox, Edge, Safari support
- **Mobile Responsiveness**: Tablet and mobile device optimization
- **Load Testing**: Performance validation under realistic usage patterns
- **Security Testing**: Penetration testing and vulnerability assessments
- **Accessibility**: WCAG 2.1 AA compliance verification

## 🤝 Contributing

This repository contains the complete technical specification and requirements for the USYD Web Crawler and RAG solution. The implementation is designed to be built by autonomous coding agents following the detailed specifications in the [Technical Design Document](./TECHNICAL_DESIGN.md).

### For Coder Agents
1. Read the complete [Technical Design Document](./TECHNICAL_DESIGN.md)
2. Follow the implementation phases outlined in the document
3. Refer to the [GitHub Issue](../../issues/1) for detailed requirements
4. Use only real websites and data for testing (no simulated data)
5. Implement all security and performance requirements

### Development Guidelines
- Follow Python PEP 8 style guidelines
- Implement comprehensive error handling and logging
- Use real data for all testing and validation
- Ensure cross-browser compatibility and mobile responsiveness
- Include proper documentation and code comments

## 📋 Project Status

- ✅ **Architecture Design** - Complete technical specification
- ✅ **Infrastructure Templates** - Azure deployment configuration
- ✅ **Requirements Documentation** - Comprehensive implementation guide
- 🔄 **Implementation** - Ready for autonomous development
- ⏳ **Testing** - Awaiting implementation completion
- ⏳ **Deployment** - Awaiting implementation completion

## 📞 Support

For questions, issues, or contributions:

- **Technical Questions**: Refer to the [Technical Design Document](./TECHNICAL_DESIGN.md)
- **Implementation Issues**: Check the [GitHub Issues](../../issues)
- **Architecture Clarifications**: Review the design document sections

## 📄 License

This project is developed as part of the USYD Web Crawler and RAG solution. Please ensure compliance with all applicable laws and regulations when scraping websites and handling user data.

## 🙏 Acknowledgments

- **Azure OpenAI Service** for providing advanced AI capabilities
- **Crawl4AI** for intelligent web scraping functionality
- **Azure Cloud Platform** for scalable infrastructure
- **Open Source Community** for the foundational technologies and libraries

---

**Built with ❤️ for intelligent web content analysis and AI-powered knowledge discovery**
