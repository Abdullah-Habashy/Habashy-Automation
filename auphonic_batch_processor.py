#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Auphonic Batch Processor (Standalone)
------------------------------------
Processes a folder of audio files through Auphonic.
Uses settings.xlsx for account distribution.
"""

import os
import sys
import time
import json
import requests
import subprocess
import concurrent.futures
from pathlib import Path
from datetime import datetime, timedelta
import openpyxl
from requests_toolbelt.multipart.encoder import MultipartEncoder, MultipartEncoderMonitor

# ========== CONFIGURATION ==========
EXCEL_PATH = r"E:\HABASHY\Python Codes\settings.xlsx"
BIN_FOLDER = r"e:\HABASHY\Python Codes\bin"
FFMPEG_PATH = os.path.join(BIN_FOLDER, "ffmpeg.exe")

def log(msg, status="INFO"):
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] [{status}] {msg}")

# ========== AUPHONIC LOGIC ==========

def get_session():
    s = requests.Session()
    return s

def headers(acc):
    return {"Authorization": f"Bearer {acc['api']}"}

def load_accounts():
    if not os.path.isfile(EXCEL_PATH):
        log(f"Excel not found: {EXCEL_PATH}", "ERROR")
        return []
    
    wb = openpyxl.load_workbook(EXCEL_PATH)
    sheet = wb.active # Reads the first sheet (Auphonic_Accounts)
    accounts = []
    for i in range(2, sheet.max_row + 1):
        email = sheet[f"A{i}"].value
        api = sheet[f"B{i}"].value
        preset = sheet[f"C{i}"].value
        if email and api and preset:
            accounts.append({
                "email": str(email),
                "api": str(api),
                "preset": str(preset),
                "remaining_minutes": 0.0
            })
    return accounts

def check_credits(acc):
    url = "https://auphonic.com/api/user.json"
    try:
        r = get_session().get(url, headers=headers(acc), timeout=10)
        r.raise_for_status()
        data = r.json()["data"]
        credits = float(data.get("credits", 0))
        acc["remaining_minutes"] = credits
        return credits
    except:
        return 0.0

def auphonic_process(file_path, acc):
    log(f"Processing {os.path.basename(file_path)} with {acc['email']}...")
    url = "https://auphonic.com/api/simple/productions.json"
    
    try:
        with open(file_path, "rb") as f:
            m = MultipartEncoder(fields={
                "preset": acc["preset"],
                "title": os.path.basename(file_path),
                "action": "start",
                "input_file": (os.path.basename(file_path), f, "audio/mpeg")
            })
            r = get_session().post(url, headers={"Authorization": f"Bearer {acc['api']}", "Content-Type": m.content_type}, data=m)
            r.raise_for_status()
            uuid = r.json()["data"]["uuid"]
            
            # Wait for finish
            status_url = f"https://auphonic.com/api/production/{uuid}/status.json"
            while True:
                rs = get_session().get(status_url, headers=headers(acc))
                st = rs.json()["data"]["status"]
                if st == 2 or st == 3: break
                time.sleep(10)
            
            # Download
            prod_url = f"https://auphonic.com/api/production/{uuid}.json"
            rp = get_session().get(prod_url, headers=headers(acc))
            outs = rp.json()["data"]["output_files"]
            for out in outs:
                dl_url = out["download_url"]
                if dl_url.startswith("/"): dl_url = "https://auphonic.com" + dl_url
                fname = out["output_basename"]
                rd = get_session().get(dl_url)
                with open(os.path.join(os.path.dirname(file_path), fname), "wb") as f:
                    f.write(rd.content)
            log(f"Done: {os.path.basename(file_path)}", "SUCCESS")
            return True
    except Exception as e:
        log(f"Failed {file_path}: {e}", "ERROR")
        return False

def main():
    print("========================================")
    print("   Auphonic Batch & Automation Tool")
    print("========================================")
    print("1. [Manual] Drag and Drop a folder")
    print("2. [Link] Paste a path or link")
    print("3. [Auto-Scan] Full Scan for ALL pending WAV files (F:\\2026\\3RD)")
    print("========================================")
    
    choice = input("Select choice (1-3): ").strip()

    folders_to_process = []
    
    if choice == "3":
        print("🚀 Starting Full Scan on F:\\2026\\3RD...")
        root_dir = Path(r"F:\2026\3RD")
        if not root_dir.exists():
            print("❌ Root directory not found.")
            return
        
        # Look for 'audio' folders in project directories (dd.mm.yyyy)
        for project in root_dir.iterdir():
            if project.is_dir():
                audio_dir = project / "audio"
                if audio_dir.exists():
                    # Check if there are .wav files in it
                    wavs = [f for f in audio_dir.iterdir() if f.suffix.lower() == ".wav"]
                    if wavs:
                        folders_to_process.append(audio_dir)
        print(f"🔍 Found {len(folders_to_process)} projects with pending audio.")
        
    elif choice in ["1", "2"]:
        folder = input("Paste link/path and press Enter: ").strip().replace('"', '')
        if os.path.isdir(folder):
            folders_to_process.append(Path(folder))
        else:
            print("❌ Invalid path.")
            return
    else:
        print("❌ Invalid choice.")
        return

    # Initialize Accounts
    accs = load_accounts()
    if not accs: return
    
    print(f"Loaded {len(accs)} accounts. Checking credits...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        executor.map(check_credits, accs)
    
    active_accs = [a for a in accs if a["remaining_minutes"] > 5]
    if not active_accs:
        print("❌ No accounts with enough credit.")
        return
    print(f"Accounts with credit: {len(active_accs)}")

    for folder in folders_to_process:
        print(f"\n📁 Processing Folder: {folder}")
        files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(('.mp3', '.wav'))]
        
        # Filter files to check if they actually need processing 
        # (e.g. if the final output name doesn't exist yet)
        to_process = []
        for f in files:
            name = os.path.basename(f)
            # If it's a WAV, we assume we need to process it if no matching output exists
            if f.lower().endswith('.wav'):
                to_process.append(f)
            else:
                # For MP3s, maybe it's already an Auphonic output? 
                # (Simple logic: if it doesn't have "ZOOM-" prefix, it's a source)
                if not name.startswith("ZOOM-"):
                    to_process.append(f)

        if not to_process:
            print(f"✅ Nothing pending in {folder.name}")
            continue

        print(f"📦 Found {len(to_process)} files to process in this folder.")
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            for i, file in enumerate(to_process):
                acc = active_accs[i % len(active_accs)]
                executor.submit(auphonic_process, file, acc)

    print("\n🎉 ALL TASKS FINISHED!")

if __name__ == "__main__":
    main()
