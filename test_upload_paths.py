import os
import sys
from pathlib import Path

# Ensure stdout handles UTF-8 for Arabic output in terminal if possible
# or just avoid it in the logs for now to prevent encoding errors
try:
    if sys.stdout.encoding.lower() != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
except:
    pass

# Paths from the user's request
REVIEW_PATH = r"I:\.shortcut-targets-by-id\1tyBiKxKMHyqqqcsMiOYNO-oQVjZbre7f\استلام المحتوى - دكتور عبد الله حبشي\تحت المراجعة"
FINAL_PATH = r"I:\.shortcut-targets-by-id\1tyBiKxKMHyqqqcsMiOYNO-oQVjZbre7f\استلام المحتوى - دكتور عبد الله حبشي\نهائي"

def test_upload_path(path_str, label_en):
    print(f"Testing {label_en} path...")
    path = Path(path_str)
    
    if not path.exists():
        print(f"FAILED: The path does not exist: {path_str}")
        return False
        
    test_file = path / f"test_conn_{label_en.lower()}.txt"
    try:
        # Create a small 1MB dummy content
        content = "Test connection " * (1024 * 64) 
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"SUCCESS: File written to {test_file}")
        return True
    except Exception as e:
        print(f"FAILED: Error writing to {label_en} path: {e}")
        return False

print("--- Starting Upload Path Validation ---")
test_upload_path(REVIEW_PATH, "Review")
print("-" * 40)
test_upload_path(FINAL_PATH, "Final")
print("--- Test Completed ---")
