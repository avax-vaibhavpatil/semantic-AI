"""
Test Script for Settings Module

Run this to verify the configuration module works correctly.

Usage:
    python -m app.config.test_settings
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config import get_settings, validate_settings


def test_settings():
    """Test the settings module"""
    print("=" * 60)
    print("Testing Configuration Module")
    print("=" * 60)
    
    try:
        # Get settings instance
        settings = get_settings()
        print("\n✅ Settings loaded successfully!")
        
        # Display configuration
        print("\n📋 Current Configuration:")
        print("-" * 60)
        print(f"API Title:      {settings.api_title}")
        print(f"API Version:    {settings.api_version}")
        print(f"API Host:       {settings.api_host}")
        print(f"API Port:       {settings.api_port}")
        print(f"Database URL:   {settings.database_url[:50]}..." if len(settings.database_url) > 50 else f"Database URL:   {settings.database_url}")
        print(f"Preferred AI:   {settings.preferred_ai}")
        print(f"Groq Model:     {settings.groq_model}")
        print(f"Semantic Path:  {settings.semantic_json_path}")
        print(f"Max Rows:       {settings.max_query_rows}")
        print(f"Debug Mode:     {settings.debug}")
        
        # Check AI providers
        print("\n🤖 AI Provider Configuration:")
        print("-" * 60)
        print(f"Groq API Key:     {'✅ Set' if settings.groq_api_key else '❌ Not set'}")
        print(f"OpenAI API Key:   {'✅ Set' if settings.openai_api_key else '❌ Not set'}")
        print(f"Anthropic API Key: {'✅ Set' if settings.anthropic_api_key else '❌ Not set'}")
        
        # Validate settings
        print("\n🔍 Validating Settings...")
        validate_settings()
        print("✅ All required settings are present!")
        
        print("\n" + "=" * 60)
        print("✅ Configuration Module Test PASSED!")
        print("=" * 60)
        
    except ValueError as e:
        print(f"\n❌ Validation Error: {e}")
        print("\n💡 Tip: Make sure you have a .env file with required settings")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    test_settings()

