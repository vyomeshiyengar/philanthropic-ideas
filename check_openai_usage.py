#!/usr/bin/env python3
"""
Script to check OpenAI account usage and credits.
"""
import sys
import os
from datetime import datetime, timedelta
from openai import OpenAI

def check_openai_usage():
    """Check OpenAI account usage and credits."""
    print("💰 Checking OpenAI Account Usage & Credits")
    print("=" * 50)
    
    # Get API key from settings
    try:
        from config.settings import settings
        api_key = settings.OPENAI_API_KEY
    except ImportError:
        api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ OpenAI API key not found")
        return False
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Get current date and first day of current month
        now = datetime.now()
        first_day = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        print(f"📅 Checking usage for: {first_day.strftime('%B %Y')}")
        print(f"📅 From: {first_day.strftime('%Y-%m-%d')}")
        print(f"📅 To: {now.strftime('%Y-%m-%d')}")
        
        # Get usage data
        usage = client.usage.list(
            start_date=first_day,
            end_date=now
        )
        
        print("\n📊 Usage Summary:")
        print("-" * 30)
        
        total_cost = 0
        total_tokens = 0
        
        if usage.data:
            for day_usage in usage.data:
                date = day_usage.date
                cost = day_usage.total_cost
                tokens = day_usage.total_usage
                
                print(f"📅 {date}: ${cost:.4f} ({tokens:,} tokens)")
                total_cost += cost
                total_tokens += tokens
        else:
            print("📅 No usage data found for this period")
        
        print("-" * 30)
        print(f"💰 Total Cost: ${total_cost:.4f}")
        print(f"🔢 Total Tokens: {total_tokens:,}")
        
        # Check if account has any usage limits or credits
        print("\n💳 Account Status:")
        print("-" * 30)
        
        if total_cost == 0:
            print("✅ No charges this month")
            print("💡 Your account is active and ready to use")
        else:
            print(f"💸 Monthly spending: ${total_cost:.4f}")
            
            # Provide cost context
            if total_cost < 1:
                print("💡 Low usage - account is healthy")
            elif total_cost < 10:
                print("💡 Moderate usage - within normal range")
            else:
                print("⚠️ High usage - consider monitoring costs")
        
        # Test API functionality
        print("\n🧪 Testing API Functionality:")
        print("-" * 30)
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            print("✅ API is working correctly")
            print(f"📝 Test response: {response.choices[0].message.content}")
            
        except Exception as e:
            print(f"❌ API test failed: {e}")
            
            if "quota" in str(e).lower() or "insufficient_quota" in str(e).lower():
                print("💡 This suggests you've run out of credits")
            elif "401" in str(e):
                print("💡 This suggests an authentication issue")
            elif "rate" in str(e).lower():
                print("💡 This suggests rate limiting")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to check usage: {e}")
        
        if "401" in str(e):
            print("\n🔍 Authentication Error")
            print("Your API key might be invalid or expired")
        elif "quota" in str(e).lower():
            print("\n💰 Quota Error")
            print("You've likely run out of credits")
        elif "rate" in str(e).lower():
            print("\n⏱️ Rate Limit Error")
            print("Too many requests - try again later")
        
        return False

def check_api_key_status():
    """Check if the API key is valid and active."""
    print("\n🔑 API Key Status Check")
    print("=" * 30)
    
    try:
        from config.settings import settings
        api_key = settings.OPENAI_API_KEY
    except ImportError:
        api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ No API key found")
        return False
    
    print(f"📋 API Key: {api_key[:20]}...")
    
    # Check key format
    if api_key.startswith('sk-proj-'):
        print("✅ Key format: Project key (correct)")
    elif api_key.startswith('sk-'):
        print("✅ Key format: Standard key (correct)")
    else:
        print("❌ Key format: Invalid (should start with 'sk-')")
        return False
    
    # Test with a simple call
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1
        )
        print("✅ API key is valid and working")
        return True
        
    except Exception as e:
        print(f"❌ API key test failed: {e}")
        return False

def provide_help():
    """Provide helpful information about OpenAI accounts."""
    print("\n💡 OpenAI Account Help")
    print("=" * 30)
    print("🔗 Useful Links:")
    print("   • Account Dashboard: https://platform.openai.com/account")
    print("   • Usage Page: https://platform.openai.com/usage")
    print("   • Billing: https://platform.openai.com/account/billing")
    print("   • API Keys: https://platform.openai.com/account/api-keys")
    
    print("\n💰 Account Types:")
    print("   • Pay-as-you-go: Pay per usage, no credits needed")
    print("   • Prepaid credits: Buy credits in advance")
    print("   • Enterprise: Contact OpenAI sales")
    
    print("\n🔧 Common Issues:")
    print("   • 401 Error: Invalid/expired API key")
    print("   • Quota exceeded: No credits remaining")
    print("   • Rate limit: Too many requests")
    print("   • Account suspended: Contact OpenAI support")

if __name__ == "__main__":
    print("🚀 OpenAI Account Usage Checker")
    print("=" * 40)
    
    # Check API key status first
    key_ok = check_api_key_status()
    
    if key_ok:
        # Check usage
        usage_ok = check_openai_usage()
        
        if usage_ok:
            print("\n🎉 Account check completed successfully!")
        else:
            print("\n⚠️ Usage check failed, but API key is valid")
    else:
        print("\n❌ API key is invalid - check your .env file")
    
    # Always provide help
    provide_help()
