#!/usr/bin/env python3
"""
Development setup script for USYD Web Crawler and RAG Application
Sets up the local development environment
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_command(command, description):
    """Run a shell command and log the result"""
    logger.info(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        logger.info(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ {description} failed: {e.stderr}")
        return False

def check_prerequisites():
    """Check if prerequisites are installed"""
    logger.info("🔍 Checking prerequisites...")
    
    prerequisites = [
        ("python3", "Python 3.9+"),
        ("pip", "pip package manager"),
        ("docker", "Docker (optional)"),
        ("git", "Git version control")
    ]
    
    all_good = True
    for cmd, desc in prerequisites:
        try:
            subprocess.run([cmd, "--version"], check=True, capture_output=True)
            logger.info(f"✓ {desc} is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            if cmd == "docker":
                logger.warning(f"⚠ {desc} not found (optional)")
            else:
                logger.error(f"✗ {desc} not found")
                all_good = False
    
    return all_good

def setup_virtual_environment():
    """Set up Python virtual environment"""
    if not os.path.exists("venv"):
        return run_command("python3 -m venv venv", "Creating virtual environment")
    else:
        logger.info("✓ Virtual environment already exists")
        return True

def install_dependencies():
    """Install Python dependencies"""
    commands = [
        ("pip install --upgrade pip", "Upgrading pip"),
        ("pip install -r requirements.txt", "Installing Python dependencies"),
        ("playwright install chromium", "Installing Playwright browser"),
        ("playwright install-deps chromium", "Installing Playwright dependencies")
    ]
    
    for cmd, desc in commands:
        if not run_command(cmd, desc):
            return False
    
    return True

def create_env_file():
    """Create .env file from template"""
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            logger.info("📝 Creating .env file from template...")
            run_command("cp .env.example .env", "Copying environment template")
            logger.info("📋 Please edit .env file with your actual configuration values")
        else:
            logger.warning("⚠ .env.example not found, cannot create .env file")
    else:
        logger.info("✓ .env file already exists")

def create_directories():
    """Create necessary directories"""
    directories = [
        "logs",
        "data/raw",
        "data/processed", 
        "data/embeddings"
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            logger.info(f"✓ Created directory: {directory}")
        else:
            logger.info(f"✓ Directory already exists: {directory}")

def setup_development_environment():
    """Main setup function"""
    logger.info("🚀 Setting up USYD Web Crawler and RAG development environment...")
    logger.info("=" * 60)
    
    if not check_prerequisites():
        logger.error("❌ Prerequisites check failed. Please install missing tools.")
        return False
    
    if not setup_virtual_environment():
        logger.error("❌ Virtual environment setup failed")
        return False
    
    if not install_dependencies():
        logger.error("❌ Dependency installation failed")
        return False
    
    create_env_file()
    create_directories()
    
    logger.info("\n" + "=" * 60)
    logger.info("🎉 Development environment setup completed!")
    logger.info("\n📋 Next steps:")
    logger.info("1. Edit .env file with your Azure service configurations")
    logger.info("2. Set up PostgreSQL and Redis locally or use Azure services")
    logger.info("3. Run: python scripts/init_db.py to initialize the database")
    logger.info("4. Run: python app.py to start the Flask application")
    logger.info("5. Run: python worker.py to start the Celery worker (in separate terminal)")
    logger.info("\n📖 For Azure deployment:")
    logger.info("1. Install Azure CLI and Azure Developer CLI (azd)")
    logger.info("2. Run: azd auth login")
    logger.info("3. Run: azd up to deploy to Azure")
    
    return True

def main():
    """Main function"""
    try:
        success = setup_development_environment()
        return 0 if success else 1
    except KeyboardInterrupt:
        logger.info("\n🛑 Setup interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"💥 Unexpected error during setup: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())