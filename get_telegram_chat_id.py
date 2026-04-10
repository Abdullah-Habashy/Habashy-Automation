#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Get Telegram Chat ID
--------------------
This script retrieves the chat ID from recent messages sent to your bot.
"""

import requests

# ضع التوكن الخاص بك هنا
BOT_TOKEN = ""

def get_updates():
    """Get recent updates from the bot"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("ok"):
            print("❌ Error:", data.get("description", "Unknown error"))
            return
        
        updates = data.get("result", [])
        
        if not updates:
            print("⚠️ No messages found!")
            print("\nℹ️ To get chat ID:")
            print("1. Add the bot to your chat/group")
            print("2. Send any message in that chat")
            print("3. Run this script again")
            return
        
        print("=" * 70)
        print("📱 TELEGRAM CHAT IDs")
        print("=" * 70)
        
        seen_chats = set()
        
        for update in updates:
            message = update.get("message", {})
            chat = message.get("chat", {})
            
            chat_id = chat.get("id")
            chat_type = chat.get("type", "unknown")
            chat_title = chat.get("title", "")
            
            # For private chats
            first_name = chat.get("first_name", "")
            last_name = chat.get("last_name", "")
            username = chat.get("username", "")
            
            if chat_id and chat_id not in seen_chats:
                seen_chats.add(chat_id)
                
                print(f"\n{'─' * 70}")
                print(f"Chat Type: {chat_type}")
                
                if chat_type == "private":
                    name = f"{first_name} {last_name}".strip()
                    print(f"Name: {name}")
                    if username:
                        print(f"Username: @{username}")
                elif chat_type in ["group", "supergroup"]:
                    print(f"Group Name: {chat_title}")
                
                print(f"✅ Chat ID: {chat_id}")
                print(f"{'─' * 70}")
        
        print("\n💡 Copy the Chat ID you need and paste it in your script!")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    get_updates()
    input("\nPress Enter to exit...")
