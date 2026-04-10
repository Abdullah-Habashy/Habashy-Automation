import cv2
import numpy as np
import mss
import psutil
import time
import datetime
import os
import ctypes

# ---------------------------------------------------------
# إعدادات البرنامج
# Program Configuration
# ---------------------------------------------------------
PROCESS_NAME = "POWERPNT.EXE"  # اسم عملية الباوربوينت
OUTPUT_FOLDER = "C:\\Recordings"  # مجلد الحفظ (سيتم إنشاءه إذا لم يكن موجوداً)
FPS = 20.0  # عدد الإطارات في الثانية (Frame Rate) - 20-30 مناسب لتسجيل الشاشة
SCREEN_SCALE = 1.0 # يمكن تعديله إذا كانت الشاشة عالية الدقة (HiDPI)

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

def get_screen_resolution():
    """الحصول على دقة الشاشة الفعلية"""
    try:
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        return width, height
    except:
        # Fallback mechanism
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            return monitor["width"], monitor["height"]

def is_process_running(process_name):
    """التحقق مما إذا كان البرنامج يعمل حالياً"""
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def start_recording():
    """بدء عملية التسجيل"""
    screen_width, screen_height = get_screen_resolution()
    
    # اسم الملف بناءً على الوقت الحالي
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(OUTPUT_FOLDER, f"PPT_Recording_{timestamp}.mp4")
    
    # إعداد كوديك الفيديو (mp4v هو خيار جيد للتوافق والجودة)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, FPS, (screen_width, screen_height))
    
    print(f"[*] PowerPoint detected! Started recording: {filename}")
    print(f"[*] Resolution: {screen_width}x{screen_height}")

    # استخدام mss لالتقاط الشاشة لأنه أسرع من غيره
    with mss.mss() as sct:
        # تحديد منطقة الالتقاط (الشاشة الأولى كاملة)
        monitor = {"top": 0, "left": 0, "width": screen_width, "height": screen_height}
        
        running = True
        last_check_time = time.time()
        
        while running:
            # وقت بداية الإطار لضبط الـ FPS
            start_time = time.time()
            
            # التحقق من أن البرنامج لا يزال يعمل كل 2 ثانية لتخفيف الحمل على المعالج
            if time.time() - last_check_time > 2.0:
                if not is_process_running(PROCESS_NAME):
                    running = False
                last_check_time = time.time()

            if not running:
                break
            
            # التقاط الصورة
            img = np.array(sct.grab(monitor))
            
            # تحويل الألوان من BGRA إلى BGR (لأن OpenCV يستخدم BGR)
            frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            # كتابة الإطار في ملف الفيديو
            out.write(frame)
            
            # التحكم في سرعة الحلقة للحفاظ على الـ FPS تقريباً
            elapsed_time = time.time() - start_time
            delay = max(1.0 / FPS - elapsed_time, 0)
            time.sleep(delay)

    # إنهاء التسجيل عند إغلاق الباوربوينت
    out.release()
    print(f"[*] PowerPoint closed. Recording saved to: {filename}")

def main():
    print("--- PowerPoint Auto-Recorder Started ---")
    print(f"[*] Waiting for {PROCESS_NAME} to start...")
    
    while True:
        if is_process_running(PROCESS_NAME):
            start_recording()
            print(f"[*] Waiting for {PROCESS_NAME} to start again...")
        
        # فحص كل 2 ثانية لتجنب استهلاك المعالج
        time.sleep(2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Script stopped by user.")
