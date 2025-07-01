#!/usr/bin/env python3
import sys
import sqlite3

def check_login_credentials():
    """Check what users exist in the database and test credentials"""
    print("🔐 Checking Login Credentials...")
    
    try:
        # Connect to the local SQLite database
        conn = sqlite3.connect('usydrag.db')
        cursor = conn.cursor()
        
        # List all users
        cursor.execute("SELECT id, username, email, password_hash, is_active FROM users")
        users = cursor.fetchall()
        
        print(f"\n📋 Found {len(users)} user(s) in database:")
        for user in users:
            print(f"   ID: {user[0]}")
            print(f"   Username: {user[1]}")
            print(f"   Email: {user[2]}")
            print(f"   Active: {user[4]}")
            print(f"   Password Hash: {user[3][:50]}...")
            print()
        
        # Test password verification
        if users:
            print("🧪 Testing password verification...")
            from werkzeug.security import check_password_hash
            
            test_passwords = ["USYDRocks!", "usydrocks!", "USYDRocks", "USYDScrapper"]
            
            for user in users:
                username = user[1]
                password_hash = user[3]
                
                print(f"\nTesting user: {username}")
                for test_pass in test_passwords:
                    is_valid = check_password_hash(password_hash, test_pass)
                    status = "✅ VALID" if is_valid else "❌ INVALID"
                    print(f"   Password '{test_pass}': {status}")
                    
                    if is_valid:
                        print(f"\n🎉 SUCCESS! Working credentials:")
                        print(f"   Username: {username}")
                        print(f"   Password: {test_pass}")
                        return True
        
        conn.close()
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = check_login_credentials()
    
    if not success:
        print("\n❌ No working credentials found!")
        print("\n🔧 Try resetting the default user by running:")
        print("   python3 -c \"")
        print("   from services.auth import AuthService;")
        print("   auth = AuthService()\"")
    else:
        print("\n✅ Found working credentials above!")
