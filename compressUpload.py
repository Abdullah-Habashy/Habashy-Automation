#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# watch_and_compress_v2.py

import os
import sys
import string
import ctypes
import time
import shutil
import subprocess
import threading
import platform
import signal
import re
import json
import logging
from logging.handlers import TimedRotatingFileHandler, QueueHandler, QueueListener
from queue import Queue, Empty
from pathlib import Path

# ========== AUTO-INSTALL & BOOTSTRAP ==========
def bootstrap():
    packages = {
        "watchdog": "watchdog",
        "colorama": "colorama",
        "psutil": "psutil",
        "requests": "requests",
        "openpyxl": "openpyxl",
        "requests_toolbelt": "requests-toolbelt",
        "bidi": "python-bidi",
        "pyrogram": "pyrogram",
        "tgcrypto": "tgcrypto"
    }
    import importlib.util
    for module, package in packages.items():
        if importlib.util.find_spec(module) is None:
            print(f"📦 Missing library detected: Installing {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--quiet"])
            except Exception as e:
                print(f"⚠️ Failed to install {package}: {e}")

bootstrap()

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from colorama import Fore, Style, init
import psutil
import requests

init(autoreset=True)

# ========== CONFIGURATION MANAGER ==========
CONFIG_FILE = Path(__file__).parent / "compress_config.json"
DEFAULT_CONFIG = {
    "watch_folder": r"F:\2026",
    "output_folder": r"I:\.shortcut-targets-by-id\1tyBiKxKMHyqqqcsMiOYNO-oQVjZbre7f\استلام المحتوى - دكتور عبد الله حبشي\تحت المراجعة",
    "output_folder_2": r"I:\.shortcut-targets-by-id\1tyBiKxKMHyqqqcsMiOYNO-oQVjZbre7f\استلام المحتوى - دكتور عبد الله حبشي\نهائي",
    "log_dir": r"F:\2026\WatchLogs",
    "handbrake_path": "",
    "valid_extensions": [".mp4", ".mov", ".mkv", ".avi", ".mxf"],
    "check_interval": 2.0,
    "debounce_sec": 10,
    "stable_min_age_sec": 60,
    "ignore_substrings": ["ame working", "adobe media encoder", ".aerender", "~$", "_temp", "cache"],
    "telegram_token": "",
    "telegram_chat_id": "-5034031577",
    "telegram_chat_id_abwab": "-5050644658",
    "telegram_chat_id_project_notify": "-1003521418260",
    "telegram_api_id": "",
    "telegram_api_hash": "",
    "upload_method": "ask"
}

GLOBAL_UPLOAD_METHOD = "gdrive" # Default, updated in main()

def load_config():
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # Merge with default to ensure all keys exist
            for k, v in DEFAULT_CONFIG.items():
                if k not in config:
                    config[k] = v
            return config
    except Exception as e:
        print(f"⚠️ Error loading config, using defaults: {e}")
        return DEFAULT_CONFIG

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Error saving config: {e}")

# Load Config
CFG = load_config()

# ========== LOGGING SETUP ==========
LOG_DIR = Path(CFG.get("log_dir", r"F:\2026\WatchLogs"))
LOG_FILE = LOG_DIR / "daily_process.log"

class ColorFormatter(logging.Formatter):
    FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
    COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        color = self.COLORS.get(record.levelno, Fore.WHITE)
        try:
            msg_str = str(record.msg)
            record.msg = color + msg_str + Style.RESET_ALL
        except:
            pass
        return super().format(record)

class SafeTimedRotatingFileHandler(TimedRotatingFileHandler):
    def doRollover(self):
        try:
            if self.stream:
                self.stream.close()
                self.stream = None
            super().doRollover()
        except (PermissionError, OSError):
            pass

# Initialize Logger
logger = logging.getLogger("Compressor")
logger.setLevel(logging.INFO)
log_queue = Queue(-1)
logger.addHandler(QueueHandler(log_queue))
_log_listener = None

def start_logging_listener():
    global _log_listener
    if _log_listener:
        _log_listener.stop()
    
    l_dir = Path(CFG.get("log_dir", r"F:\2026\WatchLogs"))
    l_dir.mkdir(parents=True, exist_ok=True)
    l_file = l_dir / "daily_process.log"
    
    f_handler = SafeTimedRotatingFileHandler(l_file, when="midnight", interval=1, backupCount=7, encoding='utf-8')
    f_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s'))
    
    c_handler = logging.StreamHandler()
    c_handler.setFormatter(ColorFormatter("%(asctime)s | %(message)s", datefmt="%H:%M:%S"))
    
    _log_listener = QueueListener(log_queue, f_handler, c_handler, respect_handler_level=True)
    _log_listener.start()

# ========== HANDBRAKE SETUP ==========
def get_handbrake_path():
    path = CFG.get("handbrake_path", "")
    if path and os.path.isfile(path): return path
    local_bin = Path(__file__).parent / "bin" / "HandBrakeCLI.exe"
    if local_bin.exists(): 
        CFG["handbrake_path"] = str(local_bin)
        save_config(CFG)
        return str(local_bin)
    path = shutil.which("HandBrakeCLI")
    if path: return path
    common_paths = [r"C:\Program Files\HandBrake\HandBrakeCLI.exe", r"C:\Program Files (x86)\HandBrake\HandBrakeCLI.exe"]
    for p in common_paths:
        if os.path.isfile(p): return p
    print(Fore.YELLOW + "⚠️ HandBrakeCLI not found.")
    while True:
        user_input = input(Fore.CYAN + "Enter full path to HandBrakeCLI.exe: ").strip().strip('"')
        if os.path.isfile(user_input):
            CFG["handbrake_path"] = user_input
            save_config(CFG)
            return user_input

def validate_and_update_paths():
    updated = False
    keys_to_check = [
        ("watch_folder", "📂 Watch Folder"),
        ("output_folder", "📁 Review Folder (تحت المراجعة)"),
        ("output_folder_2", "📁 Final Folder (نهائي)"),
        ("log_dir", "📝 Log Directory")
    ]
    for key, label in keys_to_check:
        current_path = CFG.get(key, "")
        path_obj = Path(current_path)
        while not path_obj.exists():
            print(Fore.RED + f"\n❌ Missing: {label}")
            new_input = input(Fore.CYAN + f"   Enter new path for {key}: ").strip().strip('"')
            if not new_input: continue
            new_path_obj = Path(new_input)
            if new_path_obj.exists():
                CFG[key] = new_input
                path_obj = new_path_obj
                updated = True
    if updated: save_config(CFG)

HANDBRAKE_CLI = get_handbrake_path()
validate_and_update_paths()
start_logging_listener()
LOG_DIR = Path(CFG["log_dir"])

# ========== HELPERS ==========
def _fmt_mmss(sec):
    s = int(max(0, sec))
    return f"{s//60:02d}:{s%60:02d}"

def _windows_handle_is_exclusive_openable(path):
    if platform.system().lower() != "windows": return True
    import ctypes
    GENERIC_WRITE = 0x40000000
    OPEN_EXISTING = 3
    FILE_SHARE_NONE = 0x00000000
    FILE_ATTRIBUTE_NORMAL = 0x80
    INVALID = ctypes.c_void_p(-1).value
    try:
        h = ctypes.windll.kernel32.CreateFileW(str(path), GENERIC_WRITE, FILE_SHARE_NONE, None, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, None)
        if h == INVALID: return False
        ctypes.windll.kernel32.CloseHandle(h)
        return True
    except: return False

def wait_until_file_ready(path):
    path_obj = Path(path)
    logger.info(f"⏳ Checking file stability: {path_obj.name}")
    last_size = -1
    stable_count = 0
    while stable_count < 3:
        try:
            curr_size = path_obj.stat().st_size
            if curr_size > 0 and curr_size == last_size:
                stable_count += 1
                logger.info(f"   📊 File size stable ({stable_count}/3)...")
            else:
                stable_count = 0
                if curr_size > 0:
                    logger.info(f"   🔄 File is still growing: {curr_size / (1024*1024):.1f} MB")
            last_size = curr_size
        except: return False
        time.sleep(CFG.get("check_interval", 2.0))
        
    start_wait = time.time()
    logger.info(f"   🔓 Checking if Windows has released the file...")
    while not _windows_handle_is_exclusive_openable(path):
        elapsed = int(time.time() - start_wait)
        if elapsed % 10 == 0:
            logger.info(f"   🕒 Still waiting for system to release lock... ({elapsed}s)")
        if elapsed > 300: 
            logger.error(f"❌ Timed out waiting for file access: {path_obj.name}")
            return False
        time.sleep(2)
    return True

def copy_with_bar(src: Path, dst: Path, prefix="Upload"):
    size = src.stat().st_size
    copied = 0
    with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
        while True:
            buf = fsrc.read(4 * 1024 * 1024)
            if not buf: break
            fdst.write(buf)
            copied += len(buf)
            pct = (copied / size) * 100
            bar = "█" * int(30 * copied // size) + "░" * (30 - int(30 * copied // size))
            print(f"\r{Fore.BLUE}   {prefix}: [{Fore.MAGENTA}{bar}{Fore.BLUE}] {pct:3.1f}%", end="", flush=True)
    print()

def _unique_out_path(base_out: Path) -> Path:
    if not base_out.exists(): return base_out
    stem, suf, i = base_out.stem, base_out.suffix, 1
    while True:
        cand = base_out.with_name(f"{stem}({i}){suf}")
        if not cand.exists(): return cand
        i += 1

# ========== TELEGRAM ==========
def send_telegram_msg(msg, target_chat_id=None, parse_mode=None):
    token = CFG.get("telegram_token")
    target_chat_id = target_chat_id or CFG.get("telegram_chat_id")
    if not token or not target_chat_id: return
    try: 
        payload = {"chat_id": target_chat_id, "text": msg}
        if parse_mode: payload["parse_mode"] = parse_mode
        logger.info(f"📤 Sending Telegram msg to {target_chat_id}...")
        resp = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json=payload, timeout=10)
        if not resp.ok: logger.error(f"❌ Telegram API Error: {resp.text}")
    except Exception as e: 
        logger.error(f"❌ Connection Error sending Telegram: {e}")

def send_telegram_file_pyrogram(file_path, caption, target_chat_id):
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    from pyrogram import Client
    
    api_id = CFG.get("telegram_api_id")
    api_hash = CFG.get("telegram_api_hash")
    if not api_id or not api_hash: return False
    
    async def _send():
        async def progress(current, total):
            print(f"\r{Fore.YELLOW}🚀 Telegram Upload: {current * 100 / total:.1f}%", end="")
        app = Client("my_user_session", api_id=api_id, api_hash=api_hash)
        async with app:
            try: chat_id_to_use = int(target_chat_id)
            except: chat_id_to_use = target_chat_id
            await app.send_document(chat_id=chat_id_to_use, document=file_path, caption=caption, file_name=Path(file_path).name, progress=progress)
            print()
            
    try:
        loop.run_until_complete(_send())
        return True
    except Exception as e:
        logger.error(f"⚠️ Pyrogram Error: {e}")
        return False

# ========== CORE LOGIC ==========
class FileMonitor:
    def __init__(self, drive_folder_path):
        self.drive_folder = Path(drive_folder_path)
        self.pending_files = {} # path -> last_seen_time
        self.processing = set()
        self.compress_queue = Queue()
        self.upload_queue = Queue()
        self.lock = threading.RLock() # Changed to RLock to prevent deadlocks
        self.shutdown_event = threading.Event()
        self.session_processed_count = 0
        self.task_states = {} # path -> {stage, time}
        self.history_file = LOG_DIR / "processed_history.txt"
        self.processed_history = self._load_history_from_disk()

    def _append_to_history(self, path_str):
        """Append a single path to the history file safely."""
        try:
            with open(self.history_file, "a", encoding="utf-8") as f:
                f.write(path_str + "\n")
        except Exception as e:
            logger.error(f"Failed to append to history: {e}")

    def _load_history_from_disk(self):
        loaded = set()
        if self.history_file.exists():
            with open(self.history_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip(): loaded.add(line.strip())
        return loaded

    def _save_history_to_disk(self):
        """Save the entire history set to disk."""
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                for path in self.processed_history:
                    f.write(path + "\n")
        except Exception as e:
            logger.error(f"Failed to save history: {e}")

    def update_state(self, path, stage):
        with self.lock:
            self.task_states[str(path)] = {"stage": stage, "time": time.time()}

    def mark_seen(self, path):
        # Normalize Name (Lowercase) for Name-Based tracking
        p_obj = Path(path).resolve()
        name_lower = p_obj.name.lower()
        
        # 1. Fast Silent Filters (Ignore non-videos, logs, and already compressed files)
        if name_lower.endswith('.log') or "compressed" in name_lower: return
        if p_obj.suffix.lower() not in CFG["valid_extensions"]: return
        
        # 2. History Filter (Silent & Name-Based)
        if name_lower in self.processed_history: return
        
        # 3. English Check (Silent or Warning)
        if re.search(r'[a-zA-Z]', p_obj.stem):
            return
            
        # 4. Keyword Check (Only process relevant videos)
        if not any(k in name_lower for k in ["مراجعة", "نهائي", "بعد التصحيح"]): return

        # 5. Potential Video Found! (Now we Log)
        logger.info(f"🔍 Potential Video Detected: {p_obj.name}")
        
        with self.lock:
            if path not in self.pending_files and path not in self.processing:
                self.pending_files[path] = time.time()
                self.update_state(path, "👀 SEEN (Stabilizing)")
                logger.info(f"⏳ Stabilizing: {p_obj.name} (Waiting 10s for copy to finish...)")

    def perform_scan(self, initial=False):
        """Walks the watch folder. If initial=True, it silently marks all existing files as processed."""
        watch_path = Path(CFG.get("watch_folder", ""))
        if not watch_path.exists(): return
        
        if initial:
            logger.info("🧹 Performing initial scan to ignore existing files...")
        
        count = 0
        for root, _, files in os.walk(watch_path):
            for file in files:
                full_path_obj = Path(root) / file
                name_low = full_path_obj.name.lower()
                
                if initial:
                    # Mark EVERYTHING currently in folder as processed by NAME (Silently)
                    ext = full_path_obj.suffix.lower()
                    if ext in CFG["valid_extensions"]:
                        self.processed_history.add(name_low)
                        count += 1
                else:
                    self.mark_seen(str(full_path_obj))
        
        if initial and count > 0:
            self._save_history_to_disk()
            logger.info(f"✅ Ignored {count} existing files. Now only watching for NEW files.")

    def should_skip(self, path_str):
        p = Path(path_str)
        name_lower = p.name.lower()
        if "compressed" in name_lower: return True, "Already compressed"
        if name_lower in self.processed_history:
            logger.warning(f"⏭️  Skipped: {p.name} (This name was previously processed)")
            return True, "Name already done"
            
        if p.suffix.lower() not in CFG["valid_extensions"]: return True, "Invalid ext"
        
        if re.search(r'[a-zA-Z]', p.stem):
            logger.warning(f"⏭️  Skipped: {p.name} (Contains English letters)")
            return True, "English in name"
            
        if not any(k in name_lower for k in ["مراجعة", "نهائي", "بعد التصحيح"]):
            logger.warning(f"⏭️  Skipped: {p.name} (No keywords: مراجعة/نهائي/بعد التصحيح)")
            return True, "No keywords"
            
        return False, ""

    def monitor_loop(self):
        # Initial scan to ignore everything currently in the folder
        self.perform_scan(initial=True)
        
        last_scan = 0
        while not self.shutdown_event.is_set():
            now = time.time()
            
            # Periodic scan every 30 seconds to catch missed events
            if now - last_scan > 30:
                self.perform_scan(initial=False)
                last_scan = now

            to_queue = []
            with self.lock:
                for path, last_seen in list(self.pending_files.items()):
                    if now - last_seen >= CFG.get("debounce_sec", 3):
                        to_queue.append(path)
                        del self.pending_files[path]
            for path in to_queue:
                skip, _ = self.should_skip(path)
                if not skip and path not in self.processing:
                    self.processing.add(path)
                    self.compress_queue.put(path)
                    self.update_state(path, "📥 QUEUED")
                    logger.info(f"🧾 Queued for Compression: {Path(path).name}")
            time.sleep(2)

    def compress_worker(self):
        """Worker thread dedicated ONLY to compression tasks."""
        while not self.shutdown_event.is_set():
            try: path = self.compress_queue.get(timeout=1)
            except Empty: continue
            
            try:
                if os.path.exists(path) and wait_until_file_ready(path):
                    # Start compression process
                    compressed_path = self.run_compression(path)
                    if compressed_path:
                        # Move to upload queue
                        self.upload_queue.put((path, str(compressed_path)))
                        self.update_state(path, "📤 QUEUED FOR UPLOAD")
                        logger.info(f"✅ Compression Done: {Path(path).name} -> Added to Upload Queue")
                else:
                    self.processing.discard(path)
            except Exception as e:
                logger.error(f"❌ Compression Error: {e}")
                self.processing.discard(path)
            finally:
                self.compress_queue.task_done()

    def upload_worker(self):
        """Worker thread dedicated ONLY to upload/sync tasks."""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while not self.shutdown_event.is_set():
            try: original_src, compressed_path = self.upload_queue.get(timeout=1)
            except Empty: continue
            
            try:
                self.run_upload(original_src, compressed_path)
                self.session_processed_count += 1
            except Exception as e:
                logger.error(f"❌ Upload Error: {e}")
            finally:
                self.processing.discard(original_src)
                self.upload_queue.task_done()

    def run_compression(self, src):
        """Logic for analyzing and compressing a file locally."""
        src_p = Path(src)
        name_lower = src_p.name.lower()
        base, ext = src_p.stem, src_p.suffix
        
        is_abwab = "نهائي" in name_lower or "بعد التصحيح" in name_lower
        cur_res, cur_qual = ("1080", "22") if is_abwab else ("720", "28")
        
        # Determine output location (Local archive first)
        archive_folder = Path(r"F:\2026\Completed_Archive")
        archive_folder.mkdir(parents=True, exist_ok=True)
        final_out = _unique_out_path(archive_folder / f"{base}_compressed{ext}")

        print(f"\n{Fore.CYAN}STEP 1: ANALYSIS")
        self.update_state(src, "🔍 ANALYZING")
        
        preset = "Fast 720p30" if cur_res == "720" else "Fast 1080p30"
        cmd = [HANDBRAKE_CLI, "-i", str(src_p), "-o", str(final_out), "-e", "x264", "-q", cur_qual, "--preset", preset, "-E", "av_aac", "--ab", "320", "--optimize"]
        
        print(f"\n{Fore.WHITE}STEP 2: COMPRESSION | Mode: {'Final' if is_abwab else 'Review'}")
        self.update_state(src, "🎞️ COMPRESSING")
        start_time = time.time()
        
        if not os.path.exists(HANDBRAKE_CLI):
            raise Exception(f"HandBrakeCLI.exe not found at {HANDBRAKE_CLI}")
            
        logger.info(f"🚀 Starting HandBrake for: {src_p.name}")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf-8', errors='replace')
        for line in process.stdout:
            if "Encoding" in line and "%" in line: print(f"\r{Fore.YELLOW}⏳ {line.strip()}", end="", flush=True)
        process.wait()
        
        if not final_out.exists() or final_out.stat().st_size < 1024:
            raise Exception(f"Compression failed, output file missing or empty.")
            
        print(f"\n✅ Local Compression Done in {_fmt_mmss(time.time() - start_time)}")
        return final_out

    def run_upload(self, src, compressed_path):
        """Logic for moving the compressed file to its final destination (Drive/TG)."""
        src_p = Path(src)
        comp_p = Path(compressed_path)
        name_lower = src_p.name.lower()
        
        is_review = "مراجعة" in name_lower
        is_abwab = "نهائي" in name_lower or "بعد التصحيح" in name_lower
        
        out_folder = Path(CFG['output_folder_2']) if is_abwab else Path(CFG['output_folder'])
        target_chat = CFG.get("telegram_chat_id_abwab") if is_abwab else CFG.get("telegram_chat_id")
        
        # Force Telegram upload if "مراجعة" is in the name
        effective_method = "telegram" if is_review else GLOBAL_UPLOAD_METHOD
        
        print(f"\n{Fore.CYAN}STEP 3: UPLOAD | Mode: {effective_method.upper()}")
        self.update_state(src, "💾 FINALIZING")
        
        try:
            # 1. Copy to original source directory (Additional local copy)
            src_neighbor = _unique_out_path(src_p.parent / comp_p.name)
            logger.info(f"📂 Saving copy next to original: {src_neighbor}")
            shutil.copy2(comp_p, src_neighbor)
            
            # 2. Copy to Drive sync folder ONLY if method is Google Drive
            local_copy = None
            if effective_method == "gdrive":
                local_copy = _unique_out_path(out_folder / comp_p.name)
                logger.info(f"📂 Copying to Drive sync folder: {local_copy}")
                shutil.copy2(comp_p, local_copy)
                logger.info(f"✅ Success: File placed in Drive and Source folders.")
            else:
                logger.info(f"✅ Success: File placed in Source folder. (Skipping Drive for Telegram mode)")
        except Exception as e:
            logger.error(f"❌ Failed during file placement: {e}")
            raise
        
        # Update history
        with self.lock:
            self.processed_history.add(name_lower)
            self._save_history_to_disk()
        
        file_size_mb = comp_p.stat().st_size / (1024 * 1024)
        
        if effective_method == "telegram":
            self.update_state(src, "📤 UPLOADING (Telegram)")
            file_to_send = str(local_copy) if local_copy else str(src_neighbor)
            send_telegram_file_pyrogram(file_to_send, target_chat, f"✅ {src_p.name}\n📦 Size: {file_size_mb:.1f} MB")
        else:
            self.update_state(src, "☁️ SYNCING (G-Drive)")
            # Path is already in local sync folder
            drive_link = "https://drive.google.com/drive/folders/16ca3xf73JtjDEoMLWIYIE6u_AUYlB06a" if not is_abwab else "https://drive.google.com/drive/folders/1L5q8kqd2dVUXqMGbzNWwQYtdSQ64TIH4"
            msg = f"☁️ **Upload to Drive:**\n{src_p.name}\n📦 Size: {file_size_mb:.1f} MB\n🔗 {drive_link}"
            send_telegram_msg(msg, target_chat)

        self.update_state(src, "DONE")
        logger.info(f"🎉 Fully Processed: {src_p.name}")

    def send_status_update(self):
        """Generates and sends the status report to both console and Telegram."""
        notify_chat = CFG.get("telegram_chat_id_project_notify")
        with self.lock:
            report_time = time.strftime('%H:%M:%S')
            
            # --- Console Logic ---
            print(f"\n{Fore.CYAN}{'='*60}")
            print(f"{Fore.CYAN}STATUS UPDATE | {report_time}")
            print(f"{Fore.CYAN}{'='*60}")
            
            active_tasks = {p: s for p, s in self.task_states.items() if s['stage'] != "DONE" and "FAILED" not in s['stage']}
            if active_tasks:
                print(f"{Fore.MAGENTA}ACTIVE: {len(active_tasks)} task(s)")
            else:
                print(f"{Fore.GREEN}System Idle")

            pending_count = len(self.pending_files)
            c_q_size = self.compress_queue.qsize()
            u_q_size = self.upload_queue.qsize()
            print(f"{Fore.WHITE}📈 TOTAL PROCESSED: {self.session_processed_count}")
            print(f"{Fore.CYAN}📥 COMPRESS QUEUE: {c_q_size} | 📤 UPLOAD QUEUE: {u_q_size}")
            print(f"{Fore.CYAN}{'='*60}\n")

            # --- Telegram Logic ---
            tg_msg = None
            if notify_chat:
                tg_lines = [f"📊 *STATUS UPDATE* | {report_time}"]
                tg_lines.append("─" * 15)
                
                if active_tasks:
                    tg_lines.append(f"🚀 *ACTIVE TASKS ({len(active_tasks)}):*")
                    for p, info in active_tasks.items():
                        elapsed = int(time.time() - info['time'])
                        clean_name = Path(p).name.replace('_', '\\_').replace('*', '\\*')
                        tg_lines.append(f"• `{clean_name}`")
                        tg_lines.append(f"  └ {info['stage']} ({elapsed}s)")
                else:
                    tg_lines.append("😴 No active tasks.")

                if pending_count > 0 or c_q_size > 0 or u_q_size > 0:
                    tg_lines.append("")
                    if pending_count > 0: tg_lines.append(f"👀 *SEEN:* {pending_count} files")
                    if c_q_size > 0: tg_lines.append(f"📥 *COMPRESS QUEUE:* {c_q_size}")
                    if u_q_size > 0: tg_lines.append(f"📤 *UPLOAD QUEUE:* {u_q_size}")

                tg_lines.append("")
                tg_lines.append(f"📈 *SESSION TOTAL:* {self.session_processed_count}")
                tg_msg = "\n".join(tg_lines)

        # Send Telegram outside the lock to prevent deadlocks on slow internet
        if notify_chat and tg_msg:
            send_telegram_msg(tg_msg, notify_chat, parse_mode="Markdown")

    def report_status_loop(self):
        """Sends a status report every 5 minutes (and immediately on startup)."""
        # Send first report immediately on startup
        time.sleep(5) # Small buffer to allow monitor to see files
        self.send_status_update()
        
        while not self.shutdown_event.is_set():
            # Wait 5 minutes
            for _ in range(300):
                if self.shutdown_event.is_set(): return
                time.sleep(1)
            self.send_status_update()

# ========== MAIN ==========
class WatchHandler(FileSystemEventHandler):
    def __init__(self, monitor): self.monitor = monitor
    def on_created(self, event):
        if not event.is_directory: self.monitor.mark_seen(event.src_path)
    def on_modified(self, event):
        if not event.is_directory: self.monitor.mark_seen(event.src_path)
    def on_moved(self, event):
        if not event.is_directory: self.monitor.mark_seen(event.dest_path)

def main():
    global GLOBAL_UPLOAD_METHOD
    
    # 1. Ask for upload method FIRST while terminal is clean
    print(Fore.MAGENTA + "\n" + "="*40)
    print(Fore.MAGENTA + "      SELECT UPLOAD METHOD")
    print(Fore.MAGENTA + "="*40)
    print(Fore.WHITE + " 1 - Telegram Upload (Direct)")
    print(Fore.WHITE + " 2 - Google Drive Sync (Folder)")
    print(Fore.MAGENTA + "="*40)
    
    choice = input(Fore.YELLOW + " Choice [Default: 2]: ").strip()
    GLOBAL_UPLOAD_METHOD = "telegram" if choice == "1" else "gdrive"
    
    if GLOBAL_UPLOAD_METHOD == "telegram" and (not CFG.get("telegram_api_id") or not CFG.get("telegram_api_hash")):
        print(Fore.RED + "\n⚠️ Telegram API credentials needed (my.telegram.org)")
        CFG["telegram_api_id"] = input(" API ID: ").strip()
        CFG["telegram_api_hash"] = input(" API Hash: ").strip()
        save_config(CFG)

    print(Fore.GREEN + f"\n✅ Mode: {GLOBAL_UPLOAD_METHOD.upper()} Active")
    print(Fore.CYAN + f"📂 Watch Folder: {CFG['watch_folder']}\n")

    # 2. Initialize monitor
    monitor = FileMonitor(CFG['output_folder'])
    
    # 3. Start reporting and worker threads
    threading.Thread(target=monitor.report_status_loop, daemon=True).start()
    threading.Thread(target=monitor.compress_worker, daemon=True).start()
    threading.Thread(target=monitor.upload_worker, daemon=True).start()
    
    # 4. Start monitor loop (scans and debounces)
    threading.Thread(target=monitor.monitor_loop, daemon=True).start()
    
    # 5. Start observer last
    observer = Observer()
    observer.schedule(WatchHandler(monitor), CFG["watch_folder"], recursive=True)
    observer.start()
    
    logger.info("🚀 System is live and watching...")
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        monitor.shutdown_event.set()
        observer.stop()
        observer.join()
        if _log_listener: _log_listener.stop()

if __name__ == "__main__":
    main()
