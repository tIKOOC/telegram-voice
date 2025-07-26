#!/usr/bin/env python3
"""
create_session.py - Generate Telegram Session String for Railway Deployment
Place this file in the ROOT directory of your project (same level as Dockerfile)
"""

import asyncio
import os
from telethon import TelegramClient
from telethon.sessions import StringSession

# Your Telegram credentials (from Railway dashboard)
TELEGRAM_API_ID = 21259510
TELEGRAM_API_HASH = "13c9cc03461f27b699533ff36ee69fb5"
TELEGRAM_PHONE = "+84363371124"

async def generate_session():
    """Generate Telegram session string for Railway deployment"""
    
    print("🔐 Generating Telegram Session String for Railway...")
    print("=" * 50)
    print(f"📱 Phone: {TELEGRAM_PHONE}")
    print(f"🆔 API ID: {TELEGRAM_API_ID}")
    print()
    
    try:
        # Create client with empty StringSession
        client = TelegramClient(StringSession(), TELEGRAM_API_ID, TELEGRAM_API_HASH)
        
        print("🔄 Connecting to Telegram...")
        await client.start(phone=TELEGRAM_PHONE)
        
        # Get user info to verify connection
        me = await client.get_me()
        print(f"✅ Successfully connected!")
        print(f"👤 User: {me.first_name} {me.last_name or ''}")
        print(f"📧 Username: @{me.username}")
        print()
        
        # Generate session string
        session_string = client.session.save()
        
        print("🎉 Session string generated successfully!")
        print("=" * 50)
        print("📋 Copy this session string to your Railway environment variables:")
        print()
        print(f"TELEGRAM_SESSION_STRING={session_string}")
        print()
        print("🚀 Steps to add to Railway:")
        print("1. Go to your Railway dashboard")
        print("2. Select your project")
        print("3. Go to Variables tab")
        print("4. Add/Update: TELEGRAM_SESSION_STRING")
        print("5. Paste the session string above")
        print("6. Redeploy your application")
        print()
        
        # Save to file for backup
        with open("session_backup.txt", "w") as f:
            f.write(f"TELEGRAM_SESSION_STRING={session_string}\n")
            f.write(f"Generated for: {me.first_name} {me.last_name or ''} (@{me.username})\n")
            f.write(f"Phone: {TELEGRAM_PHONE}\n")
            f.write(f"Date: {asyncio.get_event_loop().time()}\n")
        
        print("💾 Session string also saved to: session_backup.txt")
        print("⚠️  Keep this file secure and don't commit it to git!")
        
        await client.disconnect()
        
    except Exception as e:
        print(f"❌ Error generating session: {e}")
        print()
        print("🔧 Troubleshooting:")
        print("1. Make sure your phone number is correct")
        print("2. Check your internet connection")
        print("3. Verify API ID and Hash are correct")
        print("4. Try running again")
        
        return False
    
    return True

def main():
    """Main function to run session generation"""
    print("🚀 Telegram Session Generator")
    print("This will help you generate a session string for Railway deployment")
    print()
    
    # Check if telethon is installed
    try:
        import telethon
        print(f"✅ Telethon version: {telethon.__version__}")
    except ImportError:
        print("❌ Telethon not installed!")
        print("Run: pip install telethon")
        return
    
    print()
    input("Press Enter to continue (you'll need to enter verification code)...")
    print()
    
    # Run the async function
    try:
        success = asyncio.run(generate_session())
        if success:
            print("🎊 Session generation completed successfully!")
        else:
            print("💥 Session generation failed!")
    except KeyboardInterrupt:
        print("\n⏹️  Session generation cancelled by user")
    except Exception as e:
        print(f"💥 Unexpected error: {e}")

if __name__ == "__main__":
    main()