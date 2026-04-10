import yt_dlp
import os
import sys

def download_video(url, output_path='Downloads'):
    """
    Downloads a YouTube video using yt-dlp.
    """
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',  # Download best video and best audio and merge them
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'), # Save as Title.extension
        'progress_hooks': [progress_hook],
        # 'quiet': True, # Uncomment to suppress all output except errors
        # 'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Fetching video info for: {url}")
            ydl.download([url])
        print("\nDownload completed successfully!")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

def progress_hook(d):
    if d['status'] == 'downloading':
        try:
            p = d.get('_percent_str', '0%').replace('%','')
            print(f"\rDownloading: {d.get('_percent_str')} | Speed: {d.get('_speed_str')} | ETA: {d.get('_eta_str')}", end='')
        except:
            pass
    elif d['status'] == 'finished':
        print("\nDownload complete, now converting/merging if necessary...")

def main():
    print("--- YouTube Video Downloader ---")
    print("Files will be saved in a 'Downloads' folder here.")
    
    while True:
        url = input("\nEnter YouTube URL (or 'q' to quit): ").strip()
        
        if url.lower() in ('q', 'quit', 'exit'):
            print("Exiting...")
            break
        
        if not url:
            continue

        download_video(url)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
