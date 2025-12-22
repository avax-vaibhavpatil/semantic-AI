"""
Test Script for Database Configuration Module

Run this to verify the database configuration works correctly.

Usage:
    python -m app.config.test_database
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config import (
    get_database_engine,
    get_session_factory,
    get_db_session,
    test_database_connection,
    get_settings
)


def test_database_config():
    """Test the database configuration module"""
    print("=" * 60)
    print("Testing Database Configuration Module")
    print("=" * 60)
    
    try:
        # Get settings
        settings = get_settings()
        print(f"\n📋 Database Configuration:")
        print("-" * 60)
        print(f"Database URL: {settings.database_url[:50]}..." if len(settings.database_url) > 50 else f"Database URL: {settings.database_url}")
        
        # Test 1: Get engine
        print("\n🔧 Test 1: Creating Database Engine...")
        engine = get_database_engine()
        print("✅ Engine created successfully!")
        print(f"   Engine: {engine}")
        
        # Test 2: Get session factory
        print("\n🔧 Test 2: Creating Session Factory...")
        session_factory = get_session_factory()
        print("✅ Session factory created successfully!")
        print(f"   Factory: {session_factory}")
        
        # Test 3: Test connection
        print("\n🔧 Test 3: Testing Database Connection...")
        if test_database_connection():
            print("✅ Database connection successful!")
        else:
            print("❌ Database connection failed!")
            print("   Make sure your database is running and DATABASE_URL is correct")
            return False
        
        # Test 4: Create a session
        print("\n🔧 Test 4: Creating Database Session...")
        session_gen = get_db_session()
        session = next(session_gen)
        print("✅ Session created successfully!")
        print(f"   Session: {session}")
        
        # Close session properly
        try:
            next(session_gen, None)  # Complete the generator
        except StopIteration:
            pass
        
        print("\n" + "=" * 60)
        print("✅ Database Configuration Module Test PASSED!")
        print("=" * 60)
        return True
        
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\n💡 Tip: Make sure DATABASE_URL is set in your .env file")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_database_config()
    sys.exit(0 if success else 1)

