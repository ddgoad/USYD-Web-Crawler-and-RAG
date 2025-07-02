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
        this.initializeScrapingForm();
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
        
        // Model selection change handler
        document.getElementById('model-select').addEventListener('change', (e) => {
            this.onModelSelectionChange(e.target.value);
        });
        
        // Dynamic event delegation for buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('.chat-btn')) {
                const dbId = e.target.dataset.dbId;
                this.startChatSession(dbId);
            } else if (e.target.matches('.delete-btn')) {
                const dbId = e.target.dataset.dbId;
                this.deleteVectorDatabase(dbId);
            } else if (e.target.matches('.delete-scraping-job-btn')) {
                const jobId = e.target.dataset.jobId;
                this.deleteScrapingJob(jobId);
            }
        });
        
        // Cleanup databases button
        document.getElementById('cleanup-dbs-btn')?.addEventListener('click', () => {
            this.cleanupUnusedIndexes();
        });
        
        // Refresh stats button
        document.getElementById('refresh-stats-btn')?.addEventListener('click', () => {
            this.loadVectorDatabaseStats();
        });
    }
    
    async loadInitialData() {
        await Promise.all([
            this.loadScrapingJobs(),
            this.loadVectorDatabases(),
            this.loadVectorDatabaseStats()
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
                // Show appropriate notification based on scraping type
                if (scrapingType === 'single') {
                    this.showSuccessMessage('Single page scraping started - check the jobs list for status updates.');
                } else {
                    this.showSuccessMessage('Scraping job started successfully!');
                    // Show progress modal for deep crawling and sitemap
                    this.showProgressModal(result.job_id);
                }
                
                e.target.reset();
                // Reset scraping options visibility to default
                this.toggleScrapingOptions('single');
                
                // Reload jobs list immediately to show the new job
                this.loadScrapingJobs();
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
                <div class="job-actions">
                    <div class="job-status status-${job.status}">
                        ${job.status}
                    </div>
                    <button class="delete-scraping-job-btn" data-job-id="${job.id}" title="Delete Job">
                        🗑️
                    </button>
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
            // Check stats first to warn user if quota is low
            const statsResponse = await fetch('/api/vector-dbs/stats');
            const stats = await statsResponse.json();
            
            if (statsResponse.ok && stats.indexes_available <= 0) {
                const shouldCleanup = confirm(
                    'Index quota exceeded! Would you like to cleanup unused indexes first?'
                );
                if (shouldCleanup) {
                    await this.cleanupUnusedIndexes();
                    // Refresh stats after cleanup
                    const newStatsResponse = await fetch('/api/vector-dbs/stats');
                    const newStats = await newStatsResponse.json();
                    if (newStatsResponse.ok && newStats.indexes_available <= 0) {
                        this.showErrorMessage('Still no indexes available after cleanup. Please delete some vector databases manually.');
                        return;
                    }
                }
            }
            
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
                
                // Reload vector databases and stats
                setTimeout(() => {
                    this.loadVectorDatabases();
                    this.loadVectorDatabaseStats();
                }, 1000);
            } else {
                // Handle specific error messages
                let errorMessage = result.error || 'Failed to create vector database';
                if (errorMessage.includes('quota') || errorMessage.includes('exceeded')) {
                    errorMessage += ' Try cleaning up unused databases first.';
                }
                this.showErrorMessage(errorMessage);
            }
        } catch (error) {
            console.error('Error creating vector database:', error);
            this.showErrorMessage('An error occurred while creating the vector database');
        }
    }
    
    async handleCreateVectorDBFromJob(jobId, jobUrl) {
        // Prompt user for vector database name
        const name = prompt(`Enter a name for the vector database from:\n${jobUrl}`, `Vector DB - ${new URL(jobUrl).hostname}`);
        
        if (!name) {
            return; // User cancelled
        }
        
        try {
            const response = await fetch('/api/vector-dbs/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: name,
                    scraping_job_id: jobId
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showSuccessMessage('Vector database creation started! You can monitor progress in the Vector Databases section.');
                
                // Start tracking the progress
                this.trackVectorDatabaseCreation(result.db_id);
                
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
    
    trackVectorDatabaseCreation(dbId) {
        // Poll for status updates every 5 seconds
        const pollStatus = async () => {
            try {
                const response = await fetch(`/api/vector-dbs/${dbId}/status`);
                const statusData = await response.json();
                
                if (response.ok) {
                    // Update the UI to show progress
                    const statusElement = document.querySelector(`[data-db-id="${dbId}"] .db-status`);
                    if (statusElement) {
                        statusElement.textContent = statusData.status;
                        statusElement.className = `db-status status-${statusData.status}`;
                    }
                    
                    // If still building, continue polling
                    if (statusData.status === 'building') {
                        setTimeout(pollStatus, 5000);
                    } else {
                        // Reload vector databases when complete
                        this.loadVectorDatabases();
                    }
                }
            } catch (error) {
                console.error('Error checking vector database status:', error);
            }
        };
        
        // Start polling
        setTimeout(pollStatus, 2000);
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
    
    async deleteScrapingJob(jobId) {
        if (!confirm('Are you sure you want to delete this scraping job? This will also remove all associated data.')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/scrape/jobs/${jobId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showSuccessMessage('Scraping job deleted successfully!');
                this.loadScrapingJobs(); // Reload the jobs list
            } else {
                this.showErrorMessage(result.error || 'Failed to delete scraping job');
            }
        } catch (error) {
            console.error('Error deleting scraping job:', error);
            this.showErrorMessage('An error occurred while deleting the scraping job');
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
    
    onModelSelectionChange(selectedModel) {
        // Provide feedback about the selected model
        const modelDescriptions = {
            'gpt-4o': 'Advanced reasoning and comprehensive responses',
            'o3-mini': 'Fast, efficient responses with good accuracy'
        };
        
        // Show a brief notification about the model change
        this.showInfoMessage(`Selected ${selectedModel.toUpperCase()}: ${modelDescriptions[selectedModel]}`);
        
        // If there's an active chat session, inform the user that the model will apply to new messages
        if (this.currentChatSession) {
            this.addSystemMessage(`Model changed to ${selectedModel.toUpperCase()}. This will apply to your next message.`);
        }
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
    
    showProgressMessage(message) {
        this.showToast(message, 'info');
    }
    
    showSuccessMessage(message) {
        this.showToast(message, 'success');
    }
    
    showErrorMessage(message) {
        this.showToast(message, 'error');
    }
    
    showInfoMessage(message) {
        this.showToast(message, 'info');
    }
    
    showToast(message, type) {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
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
            backgroundColor: type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6',
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
    
    addSystemMessage(message) {
        if (!this.currentChatSession) return;
        
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message system-message';
        messageDiv.innerHTML = `
            <div class="message-content">
                <i class="fas fa-info-circle"></i>
                ${message}
            </div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    async cleanupUnusedIndexes() {
        if (!confirm('This will clean up unused search indexes. Are you sure?')) {
            return;
        }
        
        try {
            this.showProgressMessage('Cleaning up unused indexes...');
            
            const response = await fetch('/api/vector-dbs/cleanup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showSuccessMessage(
                    `Cleanup completed! Deleted ${result.deleted_count} unused indexes. ` +
                    `Found ${result.orphaned_found} orphaned indexes total.`
                );
                // Refresh the stats and vector database list
                this.loadVectorDatabaseStats();
                this.loadVectorDatabases();
            } else {
                this.showErrorMessage(result.error || 'Failed to cleanup indexes');
            }
        } catch (error) {
            console.error('Error during cleanup:', error);
            this.showErrorMessage('An error occurred during cleanup');
        }
    }
    
    async loadVectorDatabaseStats() {
        try {
            const response = await fetch('/api/vector-dbs/stats');
            const stats = await response.json();
            
            if (response.ok) {
                this.displayVectorDatabaseStats(stats);
            } else {
                console.error('Failed to load stats:', stats.error);
            }
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }
    
    displayVectorDatabaseStats(stats) {
        const statsContainer = document.getElementById('vector-db-stats');
        if (!statsContainer) return;
        
        const availableColor = stats.indexes_available > 5 ? 'text-success' : 
                              stats.indexes_available > 2 ? 'text-warning' : 'text-danger';
        
        statsContainer.innerHTML = `
            <div class="stats-row">
                <div class="stat-item">
                    <span class="stat-value">${stats.azure_index_count}</span>
                    <span class="stat-label">Indexes Used</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value ${availableColor}">${stats.indexes_available}</span>
                    <span class="stat-label">Available</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${stats.active_databases}</span>
                    <span class="stat-label">Active DBs</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${stats.error_databases}</span>
                    <span class="stat-label">Error DBs</span>
                </div>
            </div>
            ${stats.indexes_available <= 2 ? 
                '<div class="alert alert-warning mt-2">' +
                '<strong>Warning:</strong> Low index quota! Consider cleaning up unused databases.' +
                '</div>' : ''}
        `;
    }
    
    initializeScrapingForm() {
        // Set initial scraping type to 'single' and hide options
        const scrapingTypeSelect = document.getElementById('scraping-type');
        scrapingTypeSelect.value = 'single';
        this.toggleScrapingOptions('single');
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