#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Replicate Video Generator (Batch)
--------------------------------
Generates short videos from text prompts using Replicate API.
Supports multiple models (Veo, Kling, Zeroscope).
Reads from Excel, saves MP4 files locally.

Requirements:
- replicate
- pandas
- openpyxl
- requests
"""

import os
import sys
import time
import subprocess
import requests
import pandas as pd
import json

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Replicate Video Generator (Batch)
--------------------------------
Generates short videos from text prompts using Replicate API.
Supports multiple models (Veo, Kling, Zeroscope) via Raw HTTP (No conflict).
Reads from Excel, saves MP4 files locally.

Requirements:
- pandas
- openpyxl
- requests
"""

import os
import sys
import time
import subprocess
import requests
import pandas as pd
import json

# ========== AUTO-INSTALL ==========
def install(package):
    try:
        __import__(package)
    except ImportError:
        print(f"📦 Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

for pkg in ["pandas", "openpyxl", "requests"]:
    install(pkg)

# ========== CONFIGURATION ==========

# 1. API KEY
REPLICATE_API_TOKEN = "" 
HEADERS = {
    "Authorization": f"Token {REPLICATE_API_TOKEN}",
    "Content-Type": "application/json"
}

# 2. FILE SETTINGS
INPUT_EXCEL = "video_prompts.xlsx"
OUTPUT_FOLDER = "Generated_Videos"

# 3. MODELS CONFIGURATION
# We define the owner/name. The script will fetch the latest version ID automatically.
# 3. MODELS CONFIGURATION
# We define the owner/name. The script will fetch the latest version ID automatically.
MODELS = {
    "1": {
        "name": "Google Veo 2 (1080p HQ)",
        "owner": "google",
        "model_name": "veo-2",
        "params": lambda prompt: {
            "prompt": prompt,
            "resolution": "1080p"
        }
    },
    "2": {
        "name": "Kling 1.6 Pro (10s HQ)",
        "owner": "kwaivgi",
        "model_name": "kling-v1.6-pro",
        "params": lambda prompt: {
            "prompt": prompt,
            "aspect_ratio": "16:9",
            "duration": 10
        }
    },
    "3": {
        "name": "Zeroscope v2 XL (Wide 24fps)",
        "owner": "anotherjesse",
        "model_name": "zeroscope-v2-xl",
        "params": lambda prompt: {
            "prompt": prompt,
            "num_frames": 24,
            "fps": 24,
            "width": 854,
            "height": 480
        }
    },
    "4": {
        "name": "Minimax (Cinematic)",
        "owner": "minimax",
        "model_name": "video-01",
        "params": lambda prompt: {
            "prompt": prompt
        }
    }
}

# ===================================

def setup_env():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    
    if not os.path.exists(INPUT_EXCEL):
        df = pd.DataFrame({
            "Prompt": [
                "A cinematic drone shot of a futuristic city at sunset",
                "Clown fish swimming in coral reef, 4k high quality"
            ],
            "Status": ["Pending", "Pending"]
        })
        df.to_excel(INPUT_EXCEL, index=False)
        print(f"📄 Created sample file: {INPUT_EXCEL}")
        return False
    return True

def get_latest_version(owner, model_name):
    """Fetch the latest version ID for a model"""
    # method 1: Get Model Details (Preferred for official models)
    url = f"https://api.replicate.com/v1/models/{owner}/{model_name}"
    try:
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code == 200:
            data = resp.json()
            if "latest_version" in data and data["latest_version"]:
                return data["latest_version"]["id"]
    except Exception as e:
        print(f"⚠️ Error fetching model details for {owner}/{model_name}: {e}")

    # Method 2: List Versions (Fallback for community models)
    url_versions = f"https://api.replicate.com/v1/models/{owner}/{model_name}/versions"
    try:
        resp = requests.get(url_versions, headers=HEADERS)
        if resp.status_code == 200:
            versions = resp.json().get("results", [])
            if versions:
                return versions[0]["id"]
    except Exception:
        pass # Ignore errors here if method 1 also failed

    print(f"❌ Failed to find a version for {owner}/{model_name}")
    return None

def create_prediction(version_id, input_data):
    """Start generation via HTTP API"""
    url = "https://api.replicate.com/v1/predictions"
    data = {
        "version": version_id,
        "input": input_data
    }
    
    resp = requests.post(url, json=data, headers=HEADERS)
    if resp.status_code != 201:
        raise Exception(f"API Error ({resp.status_code}): {resp.text}")
    
    return resp.json()

def wait_for_prediction(prediction_id):
    """Poll API until complete"""
    url = f"https://api.replicate.com/v1/predictions/{prediction_id}"
    
    while True:
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code != 200:
            raise Exception(f"Polling Error: {resp.status_code}")
            
        data = resp.json()
        status = data.get("status")
        
        if status == "succeeded":
            return data.get("output")
        elif status == "failed":
            raise Exception(f"Generation Failed: {data.get('error')}")
        elif status == "canceled":
            raise Exception("Generation Canceled")
            
        print(f"   ⏳ Status: {status}...", end="\r")
        time.sleep(3)

def save_video(url, filename):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            path = os.path.join(OUTPUT_FOLDER, filename)
            with open(path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
    except Exception as e:
        print(f"❌ Download Error: {e}")
    return False

def select_model():
    print("\n🤖 Select a Video Generation Model:")
    for key, info in MODELS.items():
        print(f"  {key}. {info['name']}")
    
    while True:
        choice = input("\n👉 Enter number (1-4): ").strip()
        if choice in MODELS:
            print(f"✅ Selected: {MODELS[choice]['name']}")
            return MODELS[choice]
        print("❌ Invalid selection. Try again.")

def main():
    print("🚀 Starting Replicate Video Generator (Raw HTTP Mode)...")
    
    if not setup_env():
        return

    # 1. Select Model
    selected_model_config = select_model()
    
    # 2. Get Version ID (Once per run for efficiency)
    print(f"🔍 Fetching latest version for {selected_model_config['name']}...")
    version_id = get_latest_version(selected_model_config['owner'], selected_model_config['model_name'])
    
    if not version_id:
        print("❌ Could not determine model version. Exiting.")
        return
        
    print(f"✅ Model Version: {version_id[:10]}...")

    print("📊 Reading Excel...")
    try:
        df = pd.read_excel(INPUT_EXCEL)
    except Exception as e:
        print(f"❌ Error reading Excel: {e}")
        return

    if "Prompt" not in df.columns:
        print("❌ Column 'Prompt' missing.")
        return
        
    if "Status" not in df.columns:
        df["Status"] = "Pending"

    success_count = 0
    
    for index, row in df.iterrows():
        prompt = str(row["Prompt"]).strip()
        status = str(row.get("Status", "")).lower()

        if not prompt or prompt == "nan": continue
        if "done" in status or "success" in status: continue

        print(f"\n🎬 Processing Row {index+1}: {prompt[:40]}...")
        filename = f"{index+1}.mp4"

        try:
            start_time = time.time()
            
            # Prepare params
            input_params = selected_model_config['params'](prompt)
            
            # 3. Start Prediction
            pred_data = create_prediction(version_id, input_params)
            pred_id = pred_data.get("id")
            print(f"   🆔 Started Job ID: {pred_id}")
            
            # 4. Polling
            output = wait_for_prediction(pred_id)
            
            # Output handling
            video_url = output[0] if isinstance(output, list) else output
            
            # Veo sometimes returns a dict with 'mp4' key
            if isinstance(video_url, dict):
                video_url = video_url.get("video") or video_url.get("mp4") or str(video_url)

            print(f"\n✨ Generated! Downloading...")
            
            if save_video(video_url, filename):
                print(f"   ✅ Saved to {OUTPUT_FOLDER}/{filename}")
                df.at[index, "Status"] = f"Done ({selected_model_config['name']})"
                df.at[index, "Video_File"] = filename
                success_count += 1
            else:
                df.at[index, "Status"] = "Download Failed"

        except Exception as e:
            print(f"\n❌ Error: {e}")
            df.at[index, "Status"] = f"Error: {str(e)[:50]}"
        
        df.to_excel(INPUT_EXCEL, index=False)
        time.sleep(1)

    print(f"\n🎉 Turn Finished. Generated {success_count} videos.")

if __name__ == "__main__":
    main()
