/**
 * Dashboard JavaScript functionality
 * Handles web scraping, vector database management, and chat interface
 */

class Dashboard {
    constructor() {
        this.currentChatSession = null;
        this.currentVectorDB = null;
        this.scrapingJobs = new Map();
        this.pollInterval = null;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadInitialData();
        this.startPolling();
    }
    
    bindEvents() {
        // Logout
        document.getElementById('logout-btn').addEventListener('click', () => {
            window.location.href = '/logout';
        });
        
        // Scraping form
        document.getElementById('scraping-form').addEventListener('submit', (e) => {
            this.handleScrapingSubmit(e);
        });
        
        // Scraping type change
        document.getElementById('scraping-type').addEventListener('change', (e) => {
            this.toggleScrapingOptions(e.target.value);
        });
        
        // Vector database creation
        document.getElementById('create-vector-db-btn').addEventListener('click', () => {
            this.showCreateVectorDBModal();
        });
        
        document.getElementById('create-db-form').addEventListener('submit', (e) => {
            this.handleCreateVectorDB(e);
        });
        
        // Chat functionality
        document.getElementById('send-message-btn').addEventListener('click', () => {
            this.sendChatMessage();
        });
        
        document.getElementById('chat-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendChatMessage();
            }
        });
        
        document.getElementById('close-chat-btn').addEventListener('click', () => {
            this.closeChatInterface();
        });
        
        // Dynamic event delegation for buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('.chat-btn')) {
                const dbId = e.target.dataset.dbId;
                this.startChatSession(dbId);
            } else if (e.target.matches('.delete-btn')) {
                const dbId = e.target.dataset.dbId;
                this.deleteVectorDatabase(dbId);
            }
        });
    }
    
    async loadInitialData() {
        await Promise.all([
            this.loadScrapingJobs(),
            this.loadVectorDatabases()
        ]);
    }
    
    startPolling() {
        // Poll for job status updates every 5 seconds
        this.pollInterval = setInterval(() => {
            this.updateJobStatuses();
        }, 5000);
    }
    
    toggleScrapingOptions(type) {
        const deepOptions = document.getElementById('deep-crawl-options');
        const sitemapOptions = document.getElementById('sitemap-options');
        
        deepOptions.style.display = type === 'deep' ? 'block' : 'none';
        sitemapOptions.style.display = type === 'sitemap' ? 'block' : 'none';
    }
    
    async handleScrapingSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const scrapingType = formData.get('type');
        
        const config = {};
        if (scrapingType === 'deep') {
            config.max_depth = parseInt(document.getElementById('max-depth').value);
            config.max_pages = parseInt(document.getElementById('max-pages').value);
        } else if (scrapingType === 'sitemap') {
            config.max_pages = parseInt(document.getElementById('sitemap-max-pages').value);
        }
        
        const data = {
            url: formData.get('url'),
            type: scrapingType,
            config: config
        };
        
        try {
            const response = await fetch('/api/scrape/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showSuccessMessage('Scraping job started successfully!');
                this.showProgressModal(result.job_id);
                e.target.reset();
                
                // Reload jobs list
                setTimeout(() => {
                    this.loadScrapingJobs();
                }, 1000);
            } else {
                this.showErrorMessage(result.error || 'Failed to start scraping job');
            }
        } catch (error) {
            console.error('Error starting scraping job:', error);
            this.showErrorMessage('An error occurred while starting the scraping job');
        }
    }
    
    showProgressModal(jobId) {
        const modal = document.getElementById('progress-modal');
        modal.style.display = 'flex';
        
        // Track progress
        const trackProgress = async () => {
            try {
                const response = await fetch(`/api/scrape/status/${jobId}`);
                const status = await response.json();
                
                if (response.ok) {
                    const progressFill = document.getElementById('progress-fill');
                    const progressMessage = document.getElementById('progress-message');
                    
                    progressFill.style.width = `${status.progress || 0}%`;
                    progressMessage.textContent = status.message || 'Processing...';
                    
                    if (status.status === 'completed' || status.status === 'failed') {
                        setTimeout(() => {
                            modal.style.display = 'none';
                            if (status.status === 'completed') {
                                this.showSuccessMessage('Scraping completed successfully!');
                            } else {
                                this.showErrorMessage('Scraping failed: ' + status.message);
                            }
                            this.loadScrapingJobs();
                        }, 2000);
                        return;
                    }
                }
            } catch (error) {
                console.error('Error tracking progress:', error);
            }
            
            // Continue tracking
            setTimeout(trackProgress, 2000);
        };
        
        trackProgress();
    }
    
    async loadScrapingJobs() {
        try {
            const response = await fetch('/api/scrape/jobs');
            const data = await response.json();
            
            if (response.ok) {
                this.renderScrapingJobs(data.jobs);
            }
        } catch (error) {
            console.error('Error loading scraping jobs:', error);
        }
    }
    
    renderScrapingJobs(jobs) {
        const container = document.getElementById('scraping-jobs');
        
        if (jobs.length === 0) {
            container.innerHTML = '<p class="text-secondary">No scraping jobs yet. Start your first job above!</p>';
            return;
        }
        
        container.innerHTML = jobs.map(job => `
            <div class="job-item" data-job-id="${job.id}">
                <div class="job-info">
                    <div class="job-url">${job.url}</div>
                    <div class="job-meta">
                        <span class="job-type">${job.scraping_type}</span>
                        <span class="job-date">${new Date(job.created_at).toLocaleDateString()}</span>
                    </div>
                </div>
                <div class="job-status status-${job.status}">
                    ${job.status}
                </div>
            </div>
        `).join('');
    }
    
    async updateJobStatuses() {
        const runningJobs = document.querySelectorAll('.status-running, .status-pending');
        
        for (const jobElement of runningJobs) {
            const jobId = jobElement.closest('.job-item').dataset.jobId;
            
            try {
                const response = await fetch(`/api/scrape/status/${jobId}`);
                const status = await response.json();
                
                if (response.ok && status.status !== jobElement.textContent.trim()) {
                    // Reload the entire jobs list if status changed
                    this.loadScrapingJobs();
                    break;
                }
            } catch (error) {
                console.error('Error updating job status:', error);
            }
        }
    }
    
    async loadVectorDatabases() {
        try {
            const response = await fetch('/api/vector-dbs');
            const data = await response.json();
            
            if (response.ok) {
                this.renderVectorDatabases(data.databases);
            }
        } catch (error) {
            console.error('Error loading vector databases:', error);
        }
    }
    
    renderVectorDatabases(databases) {
        const container = document.getElementById('vector-databases');
        
        if (databases.length === 0) {
            container.innerHTML = '<p class="text-secondary">No vector databases yet. Create one from a completed scraping job!</p>';
            return;
        }
        
        container.innerHTML = databases.map(db => `
            <div class="vector-db-item" data-db-id="${db.id}">
                <div class="db-info">
                    <div class="db-name">${db.name}</div>
                    <div class="db-meta">
                        <span class="db-docs">${db.document_count} docs</span>
                        <span class="db-date">${new Date(db.created_at).toLocaleDateString()}</span>
                    </div>
                </div>
                <div class="db-status status-${db.status}">
                    ${db.status}
                </div>
                <div class="db-actions">
                    ${db.status === 'ready' ? `
                        <button class="chat-btn" data-db-id="${db.id}">
                            <i class="fas fa-comments"></i>
                            Chat
                        </button>
                    ` : ''}
                    <button class="delete-btn" data-db-id="${db.id}">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    async showCreateVectorDBModal() {
        // Load completed scraping jobs for selection
        try {
            const response = await fetch('/api/scrape/jobs');
            const data = await response.json();
            
            if (response.ok) {
                const completedJobs = data.jobs.filter(job => job.status === 'completed');
                const select = document.getElementById('source-job');
                
                select.innerHTML = '<option value="">Select a completed scraping job</option>' +
                    completedJobs.map(job => `
                        <option value="${job.id}">${job.url} (${job.scraping_type})</option>
                    `).join('');
                
                document.getElementById('create-db-modal').style.display = 'flex';
            }
        } catch (error) {
            console.error('Error loading scraping jobs:', error);
            this.showErrorMessage('Failed to load scraping jobs');
        }
    }
    
    async handleCreateVectorDB(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const data = {
            name: formData.get('name'),
            scraping_job_id: formData.get('scraping_job_id')
        };
        
        try {
            const response = await fetch('/api/vector-dbs/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showSuccessMessage('Vector database creation started!');
                this.closeModal('create-db-modal');
                e.target.reset();
                
                // Reload vector databases
                setTimeout(() => {
                    this.loadVectorDatabases();
                }, 1000);
            } else {
                this.showErrorMessage(result.error || 'Failed to create vector database');
            }
        } catch (error) {
            console.error('Error creating vector database:', error);
            this.showErrorMessage('An error occurred while creating the vector database');
        }
    }
    
    async deleteVectorDatabase(dbId) {
        if (!confirm('Are you sure you want to delete this vector database? This action cannot be undone.')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/vector-dbs/${dbId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                this.showSuccessMessage('Vector database deleted successfully');
                this.loadVectorDatabases();
                
                // Close chat if this database was being used
                if (this.currentVectorDB === dbId) {
                    this.closeChatInterface();
                }
            } else {
                const result = await response.json();
                this.showErrorMessage(result.error || 'Failed to delete vector database');
            }
        } catch (error) {
            console.error('Error deleting vector database:', error);
            this.showErrorMessage('An error occurred while deleting the vector database');
        }
    }
    
    async startChatSession(dbId) {
        const model = document.getElementById('model-select').value || 'gpt-4o';
        
        const data = {
            vector_db_id: dbId,
            model: model,
            config: {
                temperature: 0.7,
                max_tokens: 2000
            }
        };
        
        try {
            const response = await fetch('/api/chat/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.currentChatSession = result.session_id;
                this.currentVectorDB = dbId;
                this.showChatInterface();
            } else {
                this.showErrorMessage(result.error || 'Failed to start chat session');
            }
        } catch (error) {
            console.error('Error starting chat session:', error);
            this.showErrorMessage('An error occurred while starting the chat session');
        }
    }
    
    showChatInterface() {
        const chatSection = document.getElementById('chat-section');
        chatSection.style.display = 'block';
        
        // Clear previous messages except system message
        const messagesContainer = document.getElementById('chat-messages');
        const systemMessage = messagesContainer.querySelector('.system-message');
        messagesContainer.innerHTML = '';
        messagesContainer.appendChild(systemMessage);
        
        // Focus on input
        document.getElementById('chat-input').focus();
    }
    
    closeChatInterface() {
        document.getElementById('chat-section').style.display = 'none';
        this.currentChatSession = null;
        this.currentVectorDB = null;
    }
    
    async sendChatMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message || !this.currentChatSession) {
            return;
        }
        
        // Disable input and button
        const sendBtn = document.getElementById('send-message-btn');
        input.disabled = true;
        sendBtn.disabled = true;
        
        // Add user message to chat
        this.addChatMessage('user', message);
        input.value = '';
        
        try {
            const response = await fetch('/api/chat/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.currentChatSession,
                    message: message
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                // Add assistant response
                this.addChatMessage('assistant', result.response, result.sources);
            } else {
                this.addChatMessage('assistant', 'Sorry, I encountered an error processing your message: ' + (result.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error sending chat message:', error);
            this.addChatMessage('assistant', 'Sorry, I encountered a network error. Please try again.');
        } finally {
            // Re-enable input and button
            input.disabled = false;
            sendBtn.disabled = false;
            input.focus();
        }
    }
    
    addChatMessage(role, content, sources = null) {
        const messagesContainer = document.getElementById('chat-messages');
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${role}-message`;
        
        let messageHTML = `<div class="message-content">${this.formatMessageContent(content)}</div>`;
        
        if (sources && sources.length > 0) {
            messageHTML += `
                <div class="message-sources">
                    <h4>Sources:</h4>
                    ${sources.map(source => `
                        <div class="source-item">
                            <a href="${source.url}" target="_blank" rel="noopener noreferrer">
                                ${source.title || source.url}
                            </a>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        messageDiv.innerHTML = messageHTML;
        messagesContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    formatMessageContent(content) {
        // Basic markdown-like formatting
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }
    
    closeModal(modalId) {
        document.getElementById(modalId).style.display = 'none';
    }
    
    showSuccessMessage(message) {
        this.showToast(message, 'success');
    }
    
    showErrorMessage(message) {
        this.showToast(message, 'error');
    }
    
    showToast(message, type) {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
                <span>${message}</span>
            </div>
        `;
        
        // Add styles for toast (since we don't have them in CSS yet)
        Object.assign(toast.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '12px 16px',
            borderRadius: '8px',
            color: 'white',
            fontWeight: '500',
            zIndex: '9999',
            minWidth: '300px',
            backgroundColor: type === 'success' ? '#10b981' : '#ef4444',
            boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
            animation: 'slideInRight 0.3s ease-out'
        });
        
        toast.querySelector('.toast-content').style.display = 'flex';
        toast.querySelector('.toast-content').style.alignItems = 'center';
        toast.querySelector('.toast-content').style.gap = '8px';
        
        document.body.appendChild(toast);
        
        // Remove after 5 seconds
        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 5000);
    }
}

// Global functions for modal handling
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new Dashboard();
});

// Add CSS animations dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);