"""
Test Script for Logging Configuration Module

Run this to verify the logging configuration works correctly.

Usage:
    python -m app.config.test_logging
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config import setup_logging, get_logger, get_settings


def test_logging_config():
    """Test the logging configuration module"""
    print("=" * 60)
    print("Testing Logging Configuration Module")
    print("=" * 60)
    
    try:
        # Get settings
        settings = get_settings()
        print(f"\n📋 Current Settings:")
        print("-" * 60)
        print(f"Debug Mode: {settings.debug}")
        
        # Test 1: Setup logging
        print("\n🔧 Test 1: Setting up logging...")
        setup_logging()
        print("✅ Logging configured successfully!")
        
        # Test 2: Get logger
        print("\n🔧 Test 2: Getting logger...")
        logger = get_logger(__name__)
        print(f"✅ Logger created: {logger.name}")
        
        # Test 3: Test different log levels
        print("\n🔧 Test 3: Testing log levels...")
        logger.debug("This is a DEBUG message")
        logger.info("This is an INFO message")
        logger.warning("This is a WARNING message")
        logger.error("This is an ERROR message")
        print("✅ All log levels tested!")
        
        # Test 4: Test module-specific logger
        print("\n🔧 Test 4: Testing module-specific logger...")
        service_logger = get_logger("app.services.query_service")
        service_logger.info("Service logger works!")
        print(f"✅ Module logger created: {service_logger.name}")
        
        # Test 5: Test with exception
        print("\n🔧 Test 5: Testing exception logging...")
        try:
            raise ValueError("Test exception")
        except Exception as e:
            logger.exception("Exception occurred (this is expected)")
        print("✅ Exception logging tested!")
        
        print("\n" + "=" * 60)
        print("✅ Logging Configuration Module Test PASSED!")
        print("=" * 60)
        print("\n💡 Check the console output above to see formatted logs")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_logging_config()
    sys.exit(0 if success else 1)

