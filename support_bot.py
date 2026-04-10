#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Support Ticket Bot / بوت خدمة العملاء والطلاب
-------------------------------------------
Acts as a middleman between Students (Private Chat) and Teachers (Group Chat).
يعمل كوسيط بين الطالب (شات خاص) والمدرسين (جروب خاص)، مما يسمح بالمراقبة وحساب زمن الرد.

How it works:
1. Student sends message to Bot.
2. Bot forwards it to 'Staff Group' (creates a Topic per student if possible).
3. Teacher replies in 'Staff Group'.
4. Bot sends reply back to Student.
5. Bot monitors time and alerts if reply is late.
"""
import sys
import subprocess

# ========== AUTO-INSTALL ==========
def install_and_import(package):
    try:
        __import__(package)
    except ImportError:
        print(f"📦 Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot"])

install_and_import("telegram")
# ==================================

import logging
import time
import asyncio
import json
import os
from typing import Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatType
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from telegram.error import BadRequest

# ========== CONFIGURATION / الإعدادات ==========

BOT_TOKEN = ""
MAX_WAIT_MINUTES = 30  # Alert after X minutes

# Teachers List for Selection
# Format: "Label": "Tag/ID"
TEACHERS_MENU = {
    "1": "ميس هبة",
    "2": "ميس إسراء",
    "3": "ميس إيمان",
    "4": "ميس هاجر"
}

# The ID of the private group where Teachers/TAs are present
# We will auto-detect this if you run /start inside the group.
STAFF_GROUP_ID = None 

# ========== LOGGING ==========
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== DATABASE (PERSISTENCE) ==========
DB_FILE = "support_bot_db.json"

def load_db():
    """Load user-topic mapping from disk to survive restarts."""
    global user_topics, topic_users
    if not os.path.exists(DB_FILE):
        return
    
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Keys in JSON are always strings, convert back to int
            user_topics = {int(k): int(v) for k, v in data.get("user_topics", {}).items()}
            # Rebuild reverse map
            topic_users = {v: k for k, v in user_topics.items()}
            
            # Load User Teachers
            global user_teachers
            user_teachers = {int(k): v for k, v in data.get("user_teachers", {}).items()}
            
            logger.info(f"📂 Loaded database: {len(user_topics)} students mapped.")
    except Exception as e:
        logger.error(f"⚠️ Failed to load DB: {e}")

def save_db():
    """Save user-topic mapping to disk."""
    try:
        data = {
            "user_topics": user_topics,
            "user_teachers": user_teachers
        }
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(f"⚠️ Failed to save DB: {e}")

# ========== STATE ==========
# user_topics maps UserID -> MessageThreadID (Topic ID in the group)
user_topics: Dict[int, int] = {}
topic_users: Dict[int, int] = {}
user_teachers: Dict[int, str] = {} # UserID -> TeacherName
pending_timers: Dict[int, float] = {}

# Load on start
load_db()

# ========== HANDLERS ==========

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start.
    If sent in Private -> Welcome User.
    If sent in Group -> Set as Staff Group.
    """
    global STAFF_GROUP_ID
    chat = update.effective_chat
    
    if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        STAFF_GROUP_ID = chat.id
        await update.message.reply_text(f"✅ **System Ready!**\nThis group is now set as the Staff Operations Center.\nID: `{STAFF_GROUP_ID}`")
        logger.info(f"Staff Group set to: {STAFF_GROUP_ID}")
    else:
        # Show Teacher Selection Menu
        keyboard = [
            [InlineKeyboardButton(name, callback_data=f"select_teacher:{code}")]
            for code, name in TEACHERS_MENU.items()
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "أهلاً بك! 👋\n"
            "من فضلك اختر المدرس الخاص بك للبدء:",
            reply_markup=reply_markup
        )

async def handle_teacher_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback for teacher selection buttons"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("select_teacher:"):
        code = data.split(":")[1]
        teacher_name = TEACHERS_MENU.get(code, "General")
        
        user_id = query.from_user.id
        user_teachers[user_id] = teacher_name
        save_db()
        
        await query.edit_message_text(
            f"✅ تم اختيار: **{teacher_name}**\n\n"
            "الآن يمكنك إرسال سؤالك وسيصل للمدرس مباشرة."
        )

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Received message from STUDENT (Private Chat).
    Forward to Staff Group.
    """
    if STAFF_GROUP_ID is None:
        await update.message.reply_text("⚠️ System Maintenance: Staff group not connected yet.")
        return

    user = update.effective_user
    msg = update.message
    
    # 0. Check if teacher is selected
    if user.id not in user_teachers:
        # Re-send selection menu
        keyboard = [
            [InlineKeyboardButton(name, callback_data=f"select_teacher:{code}")]
            for code, name in TEACHERS_MENU.items()
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await msg.reply_text("🛑 من فضلك اختر المدرس أولاً:", reply_markup=reply_markup)
        return
    
    teacher_name = user_teachers[user.id]

    # 1. Get or Create Topic (Forum Thread) for this user
    # Note: Topics are only supported in Supergroups with "Topics" enabled.
    # If standard group, we just forward to the main chat.
    
    topic_id = user_topics.get(user.id)
    
    # Attempt to create topic if not exists (Only works if bot is Admin in a Supergroup with Topics)
    if not topic_id:
        try:
            # Prefix Topic with Teacher Name
            topic_name = f"{teacher_name} | {user.first_name}"[:60]
            new_topic = await context.bot.create_forum_topic(chat_id=STAFF_GROUP_ID, name=topic_name)
            topic_id = new_topic.message_thread_id
            user_topics[user.id] = topic_id
            topic_users[topic_id] = user.id
            save_db() # <--- SAVE TO DISK
            
            # Send info message in the new topic
            await context.bot.send_message(
                chat_id=STAFF_GROUP_ID,
                message_thread_id=topic_id,
                text=f"👤 **New Student:** {user.first_name}\nSelected: {teacher_name}\nID: {user.id}"
            )
        except BadRequest as e:
            # Fallback for groups without topics enabled or permissions
            logger.warning(f"Could not create topic (Group might not be a Forum): {e}")
            topic_id = None # Send to general chat
    
    # 2. Forward the message to the Staff Group (Specific Topic)
    try:
        # Use copy_message so it looks nice, or forward_message
        sent_msg = await msg.forward(chat_id=STAFF_GROUP_ID, message_thread_id=topic_id)
        
        # 3. Start Timer (if not already running for this topic)
        # We track the "last unanswered question time"
        if (topic_id or 0) not in pending_timers:
            pending_timers[topic_id or 0] = time.time()
            logger.info(f"⏱ Timer started for {user.first_name}")
            
    except Exception as e:
        logger.error(f"Failed to forward message: {e}")
        await msg.reply_text("❌ Error sending message to teachers.")

async def handle_staff_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Received reply from TEACHER (Staff Group).
    Forward back to Student.
    """
    msg = update.message
    
    # Safety check: Ignore messages from the bot itself (updates, alerts)
    if msg.from_user.id == context.bot.id:
        return

    # Determine which student this is for
    # If using Topics: Check message_thread_id
    topic_id = msg.message_thread_id
    
    target_user_id = topic_users.get(topic_id)
    
    # If NOT using topics, we might rely on "Reply to forwarded message"
    if not target_user_id and msg.reply_to_message:
        # The forwarded message usually has details about the original user if we used 'forward'
        # But `forward_from` is often hidden by privacy settings.
        # So using Topics is much safer.
        pass

    if target_user_id:
        try:
            # Copy the logic to the student
            await context.bot.copy_message(
                chat_id=target_user_id,
                from_chat_id=msg.chat.id,
                message_id=msg.message_id
            )
            
            # STOP Timer & Calculate Duration
            key = topic_id or 0
            if key in pending_timers:
                start_time = pending_timers.pop(key)
                duration_min = (time.time() - start_time) / 60
                
                logger.info(f"✅ Reply sent in {duration_min:.1f} minutes")
                
                # Optional: Send stats to teacher
                # await msg.reply_text(f"✅ Sent. Response time: {int(duration_min)}m")
                
                if duration_min > MAX_WAIT_MINUTES:
                    await msg.reply_text(f"⚠️ **Note:** This reply was late (+{MAX_WAIT_MINUTES}m).")

        except Exception as e:
            logger.error(f"Failed to send to user {target_user_id}: {e}")
            await msg.reply_text("❌ Failed to deliver reply. User might have blocked the bot.")

async def check_late_replies(context: ContextTypes.DEFAULT_TYPE):
    """
    Background job to alert on late unreplied topics.
    """
    if not STAFF_GROUP_ID:
        return

    now = time.time()
    for topic_id, start_time in list(pending_timers.items()):
        elapsed_min = (now - start_time) / 60
        
        if elapsed_min > MAX_WAIT_MINUTES:
            # Check if we already alerted recently? (Simple logic: just one alert or repeated?)
            # For now, let's just send a message and reset timer effectively or mark as alerted.
            # We don't want to spam. Let's assume we remove it from pending ONLY if we want 1 alert.
            # But we want to keep tracking.
            
            # Use a slightly different logic: Store "Last Alert Time" to avoid spam
            pass 
            
            try:
                alert_msg = (
                    f"🚨 **Late Alert!** 🚨\n"
                    f"Student waiting for {int(elapsed_min)} mins.\n"
                    f"Please reply!"
                )
                await context.bot.send_message(
                    chat_id=STAFF_GROUP_ID, 
                    message_thread_id=topic_id, 
                    text=alert_msg
                )
                # Reset timer to avoid spamming every minute? 
                # Or set to future?
                pending_timers[topic_id] = now  # Reset base so next alert is in +30 mins
                
            except Exception as e:
                logger.error(f"Alert failed: {e}")

# ========== MAIN ==========

def main():
    print("🚀 Starting Support Bot...")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # 1. Private Chat Handler (Students)
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_user_message))
    
    # 2. Group Chat Handler (Staff)
    # Listens to replies in the staff group
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & ~filters.COMMAND, handle_staff_reply))
    
    # 3. Commands
    app.add_handler(CommandHandler("start", start_command))
    
    # 3.5 Button Handler
    app.add_handler(CallbackQueryHandler(handle_teacher_selection))
    
    # 4. Job Queue
    if app.job_queue:
        app.job_queue.run_repeating(check_late_replies, interval=60, first=30)
    
    print("✅ Bot Polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
