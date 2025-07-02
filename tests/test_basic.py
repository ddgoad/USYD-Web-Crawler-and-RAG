#!/usr/bin/env python3
"""
Basic functionality test for USYD Web Crawler and RAG Application
Tests core components without requiring external services
"""

import os
import sys
import logging
import tempfile
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_models():
    """Test model classes"""
    try:
        from models.user import User
        
        # Test User model
        user = User(
            id=1,
            username="test_user",
            password_hash="test_hash",
            created_at=datetime.utcnow()
        )
        
        assert user.get_id() == "1"
        assert user.is_authenticated() == True
        assert user.is_active() == True
        assert user.is_anonymous() == False
        
        user_dict = user.to_dict()
        assert user_dict['username'] == "test_user"
        
        logger.info("✓ Model tests passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Model tests failed: {e}")
        return False

def test_flask_app_structure():
    """Test Flask app can be imported and has correct structure"""
    try:
        # Test importing the app
        import app
        
        # Check that app has required attributes
        assert hasattr(app, 'app')
        assert hasattr(app, 'auth_service')
        assert hasattr(app, 'scraping_service')
        assert hasattr(app, 'vector_service')
        assert hasattr(app, 'llm_service')
        
        # Test that routes are defined
        flask_app = app.app
        route_names = [rule.endpoint for rule in flask_app.url_map.iter_rules()]
        
        required_routes = [
            'index', 'login', 'logout', 'dashboard',
            'auth_status', 'start_scraping', 'scraping_status',
            'vector_databases', 'create_vector_database',
            'start_chat', 'chat_message', 'health_check'
        ]
        
        missing_routes = [route for route in required_routes if route not in route_names]
        if missing_routes:
            logger.error(f"Missing routes: {missing_routes}")
            return False
        
        logger.info("✓ Flask app structure tests passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Flask app structure tests failed: {e}")
        return False

def test_service_imports():
    """Test that all service modules can be imported"""
    try:
        from services.auth import AuthService
        from services.scraper import ScrapingService
        from services.vector_store import VectorStoreService
        from services.llm_service import LLMService
        
        # Test service instantiation (without database connections)
        logger.info("✓ Service import tests passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Service import tests failed: {e}")
        return False

def test_template_files():
    """Test that template files exist and have basic structure"""
    try:
        template_dir = "templates"
        required_templates = ["login.html", "dashboard.html", "error.html"]
        
        for template in required_templates:
            template_path = os.path.join(template_dir, template)
            if not os.path.exists(template_path):
                logger.error(f"Template file missing: {template_path}")
                return False
            
            # Check basic HTML structure
            with open(template_path, 'r') as f:
                content = f.read()
                if not content.strip().startswith('<!DOCTYPE html>'):
                    logger.error(f"Template {template} doesn't start with DOCTYPE")
                    return False
        
        logger.info("✓ Template file tests passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Template file tests failed: {e}")
        return False

def test_static_files():
    """Test that static files exist"""
    try:
        static_files = [
            "static/css/style.css",
            "static/js/login.js",
            "static/js/dashboard.js"
        ]
        
        for static_file in static_files:
            if not os.path.exists(static_file):
                logger.error(f"Static file missing: {static_file}")
                return False
        
        logger.info("✓ Static file tests passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Static file tests failed: {e}")
        return False

def test_infrastructure_files():
    """Test that infrastructure files exist and are valid"""
    try:
        infra_files = [
            "infra/main.bicep",
            "infra/main.parameters.json",
            "infra/containerapp.bicep",
            "infra/database.bicep",
            "infra/redis.bicep",
            "infra/openai.bicep",
            "infra/search.bicep",
            "infra/container-apps-environment.bicep"
        ]
        
        for infra_file in infra_files:
            if not os.path.exists(infra_file):
                logger.error(f"Infrastructure file missing: {infra_file}")
                return False
        
        # Test JSON parameter file
        with open("infra/main.parameters.json", 'r') as f:
            params = json.load(f)
            if 'parameters' not in params:
                logger.error("Invalid parameters file structure")
                return False
        
        logger.info("✓ Infrastructure file tests passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Infrastructure file tests failed: {e}")
        return False

def test_script_files():
    """Test that script files exist and are executable"""
    try:
        script_files = [
            "scripts/init_db.py",
            "scripts/setup_search_indexes.py", 
            "scripts/validate_deployment.py"
        ]
        
        for script_file in script_files:
            if not os.path.exists(script_file):
                logger.error(f"Script file missing: {script_file}")
                return False
            
            # Check if file is executable
            if not os.access(script_file, os.X_OK):
                logger.error(f"Script file not executable: {script_file}")
                return False
        
        logger.info("✓ Script file tests passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Script file tests failed: {e}")
        return False

def test_configuration_files():
    """Test configuration files"""
    try:
        config_files = [
            "azure.yaml",
            "Dockerfile",
            ".env.example",
            "requirements.txt"
        ]
        
        for config_file in config_files:
            if not os.path.exists(config_file):
                logger.error(f"Configuration file missing: {config_file}")
                return False
        
        logger.info("✓ Configuration file tests passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Configuration file tests failed: {e}")
        return False

def run_all_tests():
    """Run all basic functionality tests"""
    
    logger.info("🚀 Starting USYD Web Crawler and RAG basic functionality tests...")
    logger.info("=" * 60)
    
    tests = [
        ("Model Classes", test_models),
        ("Flask App Structure", test_flask_app_structure),
        ("Service Imports", test_service_imports),
        ("Template Files", test_template_files),
        ("Static Files", test_static_files),
        ("Infrastructure Files", test_infrastructure_files),
        ("Script Files", test_script_files),
        ("Configuration Files", test_configuration_files),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running {test_name} test...")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"✗ {test_name} test crashed: {e}")
            failed += 1
    
    logger.info("\n" + "=" * 60)
    logger.info(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("🎉 All basic functionality tests passed!")
        return True
    else:
        logger.error(f"❌ {failed} test(s) failed. Please fix the issues.")
        return False

def main():
    """Main test function"""
    try:
        success = run_all_tests()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Tests interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"💥 Unexpected error during testing: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())