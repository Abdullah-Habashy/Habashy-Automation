#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# manual_folder_compress.py
# نسخة يدوية لضغط مجلد كامل مع اختيار الجودة ومسار الرفع

import os
import sys
import time
import shutil
import subprocess
import json
import logging
from pathlib import Path
from colorama import Fore, Style, init
import requests

# ========== AUTO-INSTALL ==========
def ensure_pkg(pkg):
    try: __import__(pkg)
    except ImportError:
        print(f"📦 Installing {pkg} ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--quiet"])

for p in ("colorama", "requests"):
    ensure_pkg(p)

init(autoreset=True)

# ========== CONFIGURATION ==========
CONFIG_FILE = Path(__file__).parent / "compress_config.json"
DEFAULT_CONFIG = {
    "output_folder": r"J:\My Drive\Videos for revision",
    "output_folder_2": r"J:\My Drive\To Abwab",
    "handbrake_path": "",
    "valid_extensions": [".mp4", ".mov", ".mkv", ".avi", ".mxf"],
    "telegram_token": "",
    "telegram_chat_id": "",
    "telegram_chat_id_abwab": ""
}

def load_config():
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                if k not in config:
                    config[k] = v
            return config
    except Exception as e:
        print(f"⚠️ Error loading config: {e}")
        return DEFAULT_CONFIG

CFG = load_config()

# ========== LOGGING ==========
logging.basicConfig(
    level=logging.INFO,
    format=f"{Fore.GREEN}%(asctime)s{Style.RESET_ALL} | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("ManualCompressor")

# ========== HANDBRAKE SETUP ==========
def get_handbrake_path():
    path = CFG.get("handbrake_path", "")
    if path and os.path.isfile(path): return path
    
    path = shutil.which("HandBrakeCLI")
    if path: return path
        
    common_paths = [
        r"C:\Program Files\HandBrake\HandBrakeCLI.exe",
        r"C:\Program Files (x86)\HandBrake\HandBrakeCLI.exe"
    ]
    for p in common_paths:
        if os.path.isfile(p): return p
            
    print(Fore.RED + "❌ HandBrakeCLI not found!")
    return None

HANDBRAKE_CLI = get_handbrake_path()

# ========== HELPERS ==========
def _unique_out_path(base_out: Path) -> Path:
    if not base_out.exists(): return base_out
    stem, suf = base_out.stem, base_out.suffix
    i = 1
    while True:
        cand = base_out.with_name(f"{stem}({i}){suf}")
        if not cand.exists(): return cand
        i += 1

def _fmt_mmss(sec):
    s = int(max(0, sec))
    return f"{s//60:02d}:{s%60:02d}"

def send_telegram_msg(msg, is_abwab=False):
    token = CFG.get("telegram_token")
    if is_abwab:
        chat_id = CFG.get("telegram_chat_id_abwab") or CFG.get("telegram_chat_id")
    else:
        chat_id = CFG.get("telegram_chat_id")
    
    if not token or not chat_id:
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": msg}, timeout=10)
    except Exception as e:
        logger.error(f"⚠️ Telegram Error: {e}")

import platform
import ctypes
import string

# ========== DYNAMIC PATH RESOLUTION ==========
def resolve_path_dynamic(path_input):
    """
    Checks if path exists. If not, searches other drives for the same directory tree.
    """
    path_obj = Path(path_input)
    if path_obj.exists():
        return path_obj
    
    # Extract relative path (remove drive letter)
    try:
        parts = path_obj.parts
        if ':' in parts[0]: # e.g. "J:\\"
            rel_parts = parts[1:]
        else:
            return path_obj 
    except:
        return path_obj

    rel_path = Path(*rel_parts)
    
    # Get available drives
    drives = []
    if platform.system() == "Windows":
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drives.append(f"{letter}:\\")
            bitmask >>= 1
    else:
        return path_obj
        
    for drv in drives:
        candidate = Path(drv) / rel_path
        # Check if the parent of the target folder exists (since we might be creating the folder)
        # Or check if enough of the path exists to be confident.
        # Here we 'guess' that 'My Drive/Videos for revision' is distinctive enough.
        # We check if 'My Drive' exists on that drive? Or just try to find the full path if it already exists?
        
        # Strategy: Checks if the *root* of the requested path exists on this drive.
        # For 'J:\My Drive\Videos for revision', we check 'X:\My Drive\Videos for revision'
        # If it doesn't exist, we might be creating it. 
        # But if the Drive is missing, usually the 'My Drive' part is what we are looking for.
        
        # Let's try to find 'My Drive' or the immediate parent.
        if (Path(drv) / rel_path).parent.exists():
             return Path(drv) / rel_path
            
    print(Fore.RED + f"❌ Critical: Could not find path {rel_path} on any drive.")
    return path_obj # Return original to fail naturally

# ========== CORE LOGIC ==========
def process_video(src_path: Path, resolution_mode):
    """
    resolution_mode: 1 for 720p (Revision), 2 for 1080p (Abwab)
    """
    if not HANDBRAKE_CLI:
        logger.error("HandBrakeCLI not configured.")
        return

    logger.info(f"🎬 Processing: {src_path.name}")

    # تحديد الإعدادات بناءً على اختيار المستخدم
    if resolution_mode == 2:
        # 1080p -> To Abwab
        res_tag = "1080p"
        quality = "22"
        preset = "Fast 1080p30"
        target_folder = resolve_path_dynamic(CFG["output_folder_2"]) # Dynamic Resolve
        folder_name = "To Abwab"
        is_abwab = True
    else:
        # 720p -> Videos for revision (Default)
        res_tag = "720p"
        quality = "28"
        preset = "Fast 720p30"
        target_folder = resolve_path_dynamic(CFG["output_folder"]) # Dynamic Resolve
        folder_name = "Videos for revision"
        is_abwab = False

    if not target_folder.parent.exists() and not target_folder.exists():
         print(Fore.RED + f"❌ Error: Target drive/folder not accessible: {target_folder}")
         print(Fore.YELLOW + "   Please ensure Google Drive is mounted.")
         return

    # 1. إعداد المسارات
    archive_folder = Path(r"D:\2026\Completed_Archive")
    archive_folder.mkdir(parents=True, exist_ok=True)
    
    base = src_path.stem
    ext = src_path.suffix
    
    final_out = _unique_out_path(archive_folder / f"{base}_compressed{ext}")
    
    # التأكد من وجود فولدر الرفع
    target_folder.mkdir(parents=True, exist_ok=True)
    drive_out = _unique_out_path(target_folder / f"{base}_compressed{ext}")
    
    # نسخة في نفس المكان الأصلي
    local_copy = _unique_out_path(src_path.parent / f"{base}_compressed{ext}")

    cmd = [
        HANDBRAKE_CLI, "-i", str(src_path), "-o", str(final_out),
        "-e", "x264", "-q", quality, "--preset", preset,
        "-E", "av_aac", "--ab", "320", "--optimize"
    ]
    
    logger.info(f"⚙️ Encoding to {res_tag} ({folder_name})...")
    start_time = time.time()
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            encoding='utf-8',
            errors='replace'
        )
        
        last_printed = ""
        for line in process.stdout:
            line = line.strip()
            if "Encoding" in line and "%" in line:
                if line != last_printed:
                    print(f"\r{Fore.YELLOW}⏳ {line}{Style.RESET_ALL}", end="", flush=True)
                    last_printed = line
        
        process.wait()
        print() 
        
        if process.returncode != 0:
            logger.error("❌ HandBrake failed.")
            return

        elapsed = time.time() - start_time
        logger.info(f"✅ Finished compression in {_fmt_mmss(elapsed)}")

        # 3. الرفع والنسخ
        if final_out.stat().st_size == 0:
            logger.error("❌ Output file is empty!")
            return

        logger.info(f"☁️ Uploading to '{folder_name}'...")
        shutil.copy2(final_out, drive_out)
        
        logger.info(f"📂 Copying to source folder...")
        shutil.copy2(final_out, local_copy)
        
        msg = (
            f"✅ **Manual Compression Done**\n"
            f"File: {src_path.name}\n"
            f"Resolution: {res_tag}\n"
            f"Folder: {folder_name}\n"
            f"Time: {_fmt_mmss(elapsed)}"
        )
        send_telegram_msg(msg, is_abwab=is_abwab)
        print(Fore.GREEN + f"🎉 Successfully processed: {src_path.name}")

    except Exception as e:
        logger.error(f"❌ Error during processing: {e}")

def main():
    print(Fore.CYAN + Style.BRIGHT + "📂 Manual Folder Compressor (Multi-Quality)\n")
    

            
    # 2. استقبال ملفات الفيديو + تحديد الجودة فوراً
    processing_queue = [] # List of tuples: (Path, resolution_mode)
    
    print(Fore.YELLOW + "\n📂 Enter video paths (Drag & Drop). Type 'done' or Press [Enter] on empty line to START PROCESSING:")
    
    while True:
        user_input = input(Fore.CYAN + f"   [{len(processing_queue)+1}] File path > " + Style.RESET_ALL).strip()
        
        # Check for exit condition
        if not user_input or user_input.lower() == 'done':
            if processing_queue:
                break
            else:
                if not user_input: continue
                print(Fore.RED + "⚠️ No files added yet!")
                continue

        # Handle multiple files in one line
        paths_in_line = []
        if '"' in user_input:
            import shlex
            try:
                paths_in_line = [p.strip('"') for p in shlex.split(user_input, posix=False)]
            except:
                paths_in_line = [user_input.strip('"')]
        else:
            paths_in_line = [user_input]

        for p_str in paths_in_line:
            f_path = Path(p_str)
            if f_path.is_file():
                if f_path.suffix.lower() in CFG["valid_extensions"]:
                    # Check if already added
                    if any(item[0] == f_path for item in processing_queue):
                        print(Fore.YELLOW + f"      ⚠️ Already added: {f_path.name}")
                        continue
                        
                    print(Fore.GREEN + f"      ✅ Found: {f_path.name}")
                    
                    # Ask for Quality IMMEDIATELY
                    print(Fore.YELLOW + f"      🔻 Settings for '{f_path.name}':")
                    print(Fore.WHITE + "         [1] 720p  -> Videos for revision")
                    print(Fore.WHITE + "         [2] 1080p -> To Abwab")
                    
                    res_mode = 1
                    while True:
                        c = input(Fore.CYAN + "         Choice > " + Style.RESET_ALL).strip()
                        if c == '1':
                            res_mode = 1
                            break
                        elif c == '2':
                            res_mode = 2
                            break
                        elif c == '': # Default to 1
                            break
                        print(Fore.RED + "         ❌ Enter 1 or 2")
                    
                    processing_queue.append((f_path, res_mode))
                    mode_str = "1080p/Abwab" if res_mode == 2 else "720p/Revision"
                    print(Fore.BLUE + f"         👌 Queued with: {mode_str}")

                else:
                    print(Fore.RED + f"      ❌ Invalid extension: {f_path.name}")
            elif f_path.is_dir():
                 print(Fore.YELLOW + f"      ⚠️ Directory ignored (expecting file): {f_path.name}")
            else:
                print(Fore.RED + f"      ❌ File not found: {p_str}")

    print(Fore.GREEN + f"\n✅ Ready to process {len(processing_queue)} videos.\n")
    
    for i, (video, mode) in enumerate(processing_queue, 1):
        print("-" * 50)
        print(Fore.MAGENTA + f"[{i}/{len(processing_queue)}] Processing: {video.name}")
        process_video(video, mode)
        
    print(Fore.CYAN + "\n🏁 All files processed!")

if __name__ == "__main__":
    main()
