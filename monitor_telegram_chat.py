#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram Chat Monitor / مراقب شات التيليجرام
------------------------------------------
This script monitors a Telegram group for questions and replies.
It calculates the time taken to reply and sends alerts for late responses.
يقوم هذا السكربت بمراقبة جروب تيليجرام لحساب وقت رد المدرسين على الطلبة وإرسال تنبيهات عند التأخر.

Features:
1. Tracks student messages (Questions).
2. Detects replies from TAs (Answers).
3. Reports response time.
4. Alerts if a question is not answered within X minutes.

Requirements:
- python-telegram-bot (Auto-installed)
"""

import sys
import subprocess
import time
import logging
import asyncio
from typing import Dict, Set

# ========== AUTO-INSTALL / التثبيت التلقائي ==========
def install_package(package):
    try:
        __import__(package.replace("-", "_"))
    except ImportError:
        print(f"📦 Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Install python-telegram-bot if missing
try:
    import telegram
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
except ImportError:
    install_package("python-telegram-bot")
    import telegram
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ========== CONFIGURATION / الإعدادات ==========

# Token from your other scripts (change if needed)
BOT_TOKEN = ""

# Maximum time allowed before alert (in minutes) / الحد الأقصى للدقائق قبل التنبيه
MAX_WAIT_MINUTES = 30

# Chat ID to send alerts to (can be the same group or an admin group)
# You can find this using the get_telegram_chat_id.py script
# Defaulting to the group ID found in compressUpload.py logic (Abwab group or Revision group)
# Change this to the specific group you want to monitor
MONITORED_GROUP_ID = -100123456789 # ⚠️ REPLACE THIS with the real Group ID

# TAs List (Optional): If you want to strictly check who is replying
# If empty, anyone who replies is considered a "Responder"
# Example: [12345678, 98765432]
TAS_IDS = []

# ========== LOGGING SETUP ==========
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== STATE TRACKING ==========
# Dictionary to store pending questions: {message_id: {time: timestamp, user: user_name, text: message_text}}
pending_questions: Dict[int, dict] = {}
answered_questions: Set[int] = set()

# Global variable for Chat ID (Auto-discovered)
current_chat_id = None

# ========== HANDLERS ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Answers the /start command"""
    global current_chat_id
    current_chat_id = update.message.chat_id
    
    await update.message.reply_text(
        f"👋 **Bot Started!**\n"
        f"✅ Monitoring Chat ID: `{current_chat_id}`\n"
        f"I am now monitoring this chat for Q&A.\n"
        f"Alerts will be sent if replies take longer than {MAX_WAIT_MINUTES} mins."
    )
    logger.info(f"Set monitoring chat ID to: {current_chat_id}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Analyzes every message in the group.
    """
    global current_chat_id
    message = update.message
    if not message:
        return

    # Auto-set chat ID if not set
    if current_chat_id is None:
        current_chat_id = message.chat_id
        logger.info(f"ℹ️ Auto-detected Chat ID: {current_chat_id}")

    chat_id = message.chat_id
    msg_id = message.message_id
    user = message.from_user
    now = time.time()
    
    # Identify user name
    user_name = user.first_name if user else "Unknown"
    if user and user.username:
        user_name = f"@{user.username}"

    # 1. CHECK IF IT IS A REPLY (ANSWER)
    if message.reply_to_message:
        original_msg_id = message.reply_to_message.message_id
        
        # Check if we are tracking the original message
        if original_msg_id in pending_questions:
            # OPTIONAL: Check if replier is a TA (if TAS_IDS is configured)
            if TAS_IDS and user.id not in TAS_IDS:
                logger.info(f"Ignoring reply from non-TA ID: {user.id} ({user_name})")
                return

            question_data = pending_questions.pop(original_msg_id)
            start_time = question_data['time']
            duration_sec = now - start_time
            duration_min = duration_sec / 60
            
            # Format output
            time_str = f"{int(duration_min)}m {int(duration_sec % 60)}s"
            
            logger.info(f"✅ Answered: {user_name} replied to {question_data['user']} in {time_str}")
            
            # If it was very late, maybe shame them?
            if duration_min > MAX_WAIT_MINUTES:
                await message.reply_text(
                    f"⚠️ **Late Reply!**\n"
                    f"Took: {time_str} (Limit: {MAX_WAIT_MINUTES}m)"
                )
                
        else:
            # It's a reply to a message we didn't track (maybe before bot started) or expert chatter
            pass

    # 2. IF NOT A REPLY, ASSUME IT IS A QUESTION/TOPIC
    else:
        # Ignore messages from Bots or Service messages
        if user and user.is_bot:
            return

        # Store it
        pending_questions[msg_id] = {
            'time': now,
            'user': user_name,
            'text': message.text[:50] + "..." if message.text else "Photo/Media"
        }
        logger.info(f"📩 New Question tracked from {user_name}: {msg_id}")

async def check_late_replies(context: ContextTypes.DEFAULT_TYPE):
    """
    Background job to check for unanswered questions.
    """
    if current_chat_id is None:
        return

    now = time.time()
    chat_id = current_chat_id
    
    # List to modify safely
    late_ids = []
    
    for msg_id, data in pending_questions.items():
        # Check if already alerted? (To avoid spamming let's add a 'alerted' flag)
        if data.get('alerted'):
            continue
            
        elapsed_min = (now - data['time']) / 60
        
        if elapsed_min > MAX_WAIT_MINUTES:
            # SEND ALERT
            user_name = data['user']
            wait_time = int(elapsed_min)
            
            alert_text = (
                f"🚨 **Alert: Late Response!** 🚨\n\n"
                f"👤 Student: {user_name}\n"
                f"⏳ Waiting: {wait_time} minutes\n"
                f"💬 Message: {data['text']}\n"
                f"Please reply ASAP!"
            )
            
            try:
                # Reply to the original message so TAs can click and go to it
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=alert_text,
                    reply_to_message_id=msg_id
                )
                # Mark as alerted so we don't spam 
                data['alerted'] = True
                
            except Exception as e:
                logger.error(f"Failed to send alert: {e}")

# ========== MAIN EXECUTION ==========

def main():
    print("🚀 Starting Telegram Monitor Bot...")
    
    # 1. Create Application
    application = Application.builder().token(BOT_TOKEN).build()

    # 2. Add Handlers
    application.add_handler(CommandHandler("start", start))
    
    # Monitor text, photos, video, etc. (everything that can be replied to)
    # Using filters.ALL but excluding status updates
    msg_filter = filters.ALL & (~filters.StatusUpdate.ALL)
    application.add_handler(MessageHandler(msg_filter, handle_message))

    # 3. Setup Job Queue for periodic checks
    # Use the job_queue from the application
    if application.job_queue:
        # Check every 60 seconds
        application.job_queue.run_repeating(check_late_replies, interval=60, first=10)
    else:
        print("❌ Error: JobQueue not available (install python-telegram-bot[job-queue])?")

    # 4. Run Console Info
    print(f"✅ Bot is running. Monitoring for replies > {MAX_WAIT_MINUTES} mins.")
    print("waiting for messages...")

    # 5. Start Polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
