import time
import winsound

def play_alert():
    """Play a simple beep sound sequence."""
    try:
        # Play a sequence of beeps
        # Frequency: 1000 Hz, Duration: 300 ms
        winsound.Beep(1000, 300)
        time.sleep(0.1)
        winsound.Beep(1000, 300)
    except Exception as e:
        print(f"Could not play sound: {e}")
        # Fallback to visual alert (bell character) if winsound fails for some reason
        print("\a")

if __name__ == "__main__":
    print("Starting timer logic.")
    print("Press Ctrl+C to stop the program.\n")
    
    try:
        duration1_min = float(input("Enter first duration in minutes (e.g., 10): "))
        duration2_min = float(input("Enter second duration in minutes (e.g., 5): "))
    except ValueError:
        print("Invalid input. Please enter numbers only.")
        exit(1)

    # Convert to seconds
    duration1_sec = duration1_min * 60
    duration2_sec = duration2_min * 60
    
    print(f"\nTimer started! Alternating between {duration1_min} min and {duration2_min} min.")
    
    try:
        while True:
            # First Interval
            print(f"[{time.strftime('%H:%M:%S')}] Waiting for {duration1_min} minutes...")
            time.sleep(duration1_sec)
            
            print(f"[{time.strftime('%H:%M:%S')}] {duration1_min} minutes passed! ALERT!")
            play_alert()
            
            # Second Interval
            print(f"[{time.strftime('%H:%M:%S')}] Waiting for {duration2_min} minutes...")
            time.sleep(duration2_sec)
            
            print(f"[{time.strftime('%H:%M:%S')}] {duration2_min} minutes passed! ALERT!")
            play_alert()
            
    except KeyboardInterrupt:
        print("\nTimer stopped manually.")
