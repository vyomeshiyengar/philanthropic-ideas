#!/usr/bin/env python3
"""
Simple test script to verify OpenAI API key.
"""
import os
import sys
from openai import OpenAI

def test_openai_key():
    """Test the OpenAI API key directly."""
    print("🔑 Testing OpenAI API Key")
    print("=" * 40)
    
    # Import settings to get API key
    try:
        from config.settings import settings
        api_key = settings.OPENAI_API_KEY
    except ImportError:
        # Fallback to environment variable
        api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ OPENAI_API_KEY not found in settings or environment variables")
        return False
    
    print(f"📋 API Key found: {api_key[:20]}...")
    print(f"📏 Key length: {len(api_key)} characters")
    
    # Check key format
    if not api_key.startswith('sk-'):
        print("❌ API key doesn't start with 'sk-'")
        return False
    
    print("✅ API key format looks correct")
    
    # Test with OpenAI client
    try:
        client = OpenAI(api_key=api_key)
        
        # Simple test call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        
        print("✅ API key is valid and working!")
        print(f"📝 Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ API key test failed: {e}")
        
        # Provide helpful error messages
        if "401" in str(e):
            print("\n🔍 401 Error - Authentication failed")
            print("Possible causes:")
            print("1. API key is incorrect or expired")
            print("2. API key doesn't have the right permissions")
            print("3. Account might be suspended")
            print("\n💡 Solutions:")
            print("1. Check your API key at: https://platform.openai.com/account/api-keys")
            print("2. Generate a new API key if needed")
            print("3. Make sure your account has credits/usage")
        
        elif "quota" in str(e).lower():
            print("\n💰 Quota exceeded - You've run out of credits")
            print("💡 Add credits to your OpenAI account")
        
        elif "rate" in str(e).lower():
            print("\n⏱️ Rate limit exceeded - Too many requests")
            print("💡 Wait a moment and try again")
        
        return False

def check_env_file():
    """Check the .env file for issues."""
    print("\n📁 Checking .env file...")
    
    try:
        with open('.env', 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        api_key_line = None
        
        for line in lines:
            if line.startswith('OPENAI_API_KEY='):
                api_key_line = line
                break
        
        if api_key_line:
            key_value = api_key_line.split('=', 1)[1].strip()
            print(f"📋 Found API key in .env: {key_value[:20]}...")
            print(f"📏 Length: {len(key_value)} characters")
            
            # Check for common issues
            if '\n' in key_value or '\r' in key_value:
                print("⚠️ Warning: API key contains newline characters")
                print("💡 This might cause authentication issues")
            
            if key_value.endswith('"') or key_value.endswith("'"):
                print("⚠️ Warning: API key might have extra quotes")
            
            return key_value
        else:
            print("❌ OPENAI_API_KEY not found in .env file")
            return None
            
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return None

if __name__ == "__main__":
    print("🚀 OpenAI API Key Verification")
    print("=" * 40)
    
    # Check .env file first
    env_key = check_env_file()
    
    # Test the key
    success = test_openai_key()
    
    if success:
        print("\n🎉 API key is working correctly!")
        print("You can now use the OpenAI integration.")
    else:
        print("\n❌ API key verification failed!")
        print("\n🔧 Troubleshooting steps:")
        print("1. Go to https://platform.openai.com/account/api-keys")
        print("2. Check if your key is still valid")
        print("3. Generate a new key if needed")
        print("4. Update your .env file with the new key")
        print("5. Make sure your account has credits")
        
        sys.exit(1)
