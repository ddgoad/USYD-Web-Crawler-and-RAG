/**
 * Login page JavaScript functionality
 * Handles user authentication and form submission
 */

document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('login-form');
    const loginBtn = document.getElementById('login-btn');
    const btnText = loginBtn.querySelector('.btn-text');
    const btnLoading = loginBtn.querySelector('.btn-loading');
    
    // Handle form submission
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        
        if (!username || !password) {
            showError('Please enter both username and password');
            return;
        }
        
        // Show loading state
        setLoadingState(true);
        
        try {
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);
            
            const response = await fetch('/login', {
                method: 'POST',
                body: formData
            });
            
            if (response.redirected) {
                // Successful login - redirect to dashboard
                window.location.href = response.url;
            } else {
                // Handle error - reload page to show flash message
                window.location.reload();
            }
            
        } catch (error) {
            console.error('Login error:', error);
            showError('An error occurred during login. Please try again.');
        } finally {
            setLoadingState(false);
        }
    });
    
    // Handle Enter key in password field
    document.getElementById('password').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            loginForm.dispatchEvent(new Event('submit'));
        }
    });
    
    // Auto-dismiss flash messages
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 5000);
    });
    
    function setLoadingState(loading) {
        if (loading) {
            loginBtn.disabled = true;
            btnText.style.display = 'none';
            btnLoading.style.display = 'flex';
        } else {
            loginBtn.disabled = false;
            btnText.style.display = 'block';
            btnLoading.style.display = 'none';
        }
    }
    
    function showError(message) {
        // Remove existing error messages
        const existingErrors = document.querySelectorAll('.flash-error');
        existingErrors.forEach(error => error.remove());
        
        // Create new error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'flash-message flash-error';
        errorDiv.textContent = message;
        
        // Insert after login form
        loginForm.parentNode.insertBefore(errorDiv, loginForm.nextSibling);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            errorDiv.style.opacity = '0';
            setTimeout(() => {
                errorDiv.remove();
            }, 300);
        }, 5000);
    }
});