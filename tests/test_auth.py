#!/usr/bin/env python3
"""
Test script to verify authentication credentials and debug login issues
"""

import sys
import os
sys.path.append('.')

from services.auth import AuthService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_authentication():
    """Test the authentication service and default credentials"""
    print("🔐 Testing Authentication Service...")
    
    try:
        # Initialize auth service
        auth_service = AuthService()
        print("✓ AuthService initialized successfully")
        
        # Test default credentials
        test_credentials = [
            ("USYDScrapper", "USYDRocks!"),
            ("usydscrapper", "USYDRocks!"),  # lowercase
            ("USYDScrapper", "usydrocks!"),  # lowercase password
        ]
        
        for username, password in test_credentials:
            print(f"\n🧪 Testing credentials: {username} / {password}")
            
            try:
                user = auth_service.authenticate_user(username, password)
                if user:
                    print(f"✅ SUCCESS! Login works for {username}")
                    print(f"   User ID: {user.user_id}")
                    print(f"   Username: {user.username}")
                    return True
                else:
                    print(f"❌ FAILED: Invalid credentials for {username}")
            except Exception as e:
                print(f"❌ ERROR during authentication: {str(e)}")
        
        # If we get here, none of the credentials worked
        print("\n🔍 Let's check what users exist in the database...")
        list_users(auth_service)
        
        return False
        
    except Exception as e:
        print(f"❌ ERROR initializing AuthService: {str(e)}")
        return False

def list_users(auth_service):
    """List all users in the database for debugging"""
    try:
        conn = auth_service._get_db_connection()
        cursor = conn.cursor()
        
        if auth_service.db_url.startswith("sqlite:"):
            cursor.execute("SELECT id, username, email, is_active, created_at FROM users")
        else:
            cursor.execute("SELECT id, username, email, is_active, created_at FROM users")
        
        users = cursor.fetchall()
        
        if users:
            print(f"\n📋 Found {len(users)} user(s) in database:")
            for user in users:
                if auth_service.db_url.startswith("sqlite:"):
                    print(f"   ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Active: {user[3]}")
                else:
                    print(f"   ID: {user['id']}, Username: {user['username']}, Email: {user['email']}, Active: {user['is_active']}")
        else:
            print("\n📋 No users found in database!")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ ERROR listing users: {str(e)}")

def create_test_user(auth_service):
    """Create a test user for debugging"""
    try:
        print("\n🔧 Creating new test user...")
        
        conn = auth_service._get_db_connection()
        cursor = conn.cursor()
        
        from werkzeug.security import generate_password_hash
        
        test_password_hash = generate_password_hash("testpass123")
        
        if auth_service.db_url.startswith("sqlite:"):
            cursor.execute("""
                INSERT OR REPLACE INTO users
                (username, email, password_hash, is_active)
                VALUES (?, ?, ?, ?)
            """, (
                "testuser",
                "test@usyd.edu.au",
                test_password_hash,
                True
            ))
        else:
            cursor.execute("""
                INSERT INTO users
                (username, email, password_hash, is_active)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (username) DO UPDATE SET
                password_hash = EXCLUDED.password_hash
            """, (
                "testuser",
                "test@usyd.edu.au",
                test_password_hash,
                True
            ))
        
        conn.commit()
        conn.close()
        
        print("✓ Test user created: testuser / testpass123")
        
        # Test the new user
        user = auth_service.authenticate_user("testuser", "testpass123")
        if user:
            print("✅ Test user authentication successful!")
            return True
        else:
            print("❌ Test user authentication failed!")
            return False
            
    except Exception as e:
        print(f"❌ ERROR creating test user: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 USYD Web Crawler - Authentication Test")
    print("=" * 50)
    
    success = test_authentication()
    
    if not success:
        print("\n🔧 Attempting to create a test user...")
        auth_service = AuthService()
        create_test_user(auth_service)
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")
    print("\nIf authentication is still failing, try these credentials:")
    print("📝 Default: USYDScrapper / USYDRocks!")
    print("📝 Test: testuser / testpass123")
