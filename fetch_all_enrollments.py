import requests
import json
import time

# Configuration
BASE_URL = "https://api.abdullah-habashy.com/v1/academy"
LOGIN_URL = f"{BASE_URL}/auth/login"
STUDENTS_URL = f"{BASE_URL}/admin/students"
BOOTCAMP_HISTORY_URL_TEMPLATE = f"{BASE_URL}/admin/bootcamps/student/{{student_id}}/enrollmentHistory"

# Credentials
EMAIL = "abdelrahmanmostafa785@gmail.com"
PASSWORD = "password"

def login():
    """Authenticates and returns token."""
    try:
        response = requests.post(LOGIN_URL, json={"identifier": EMAIL, "password": PASSWORD})
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            return data["data"]["token"]
    except Exception as e:
        print(f"Login failed: {e}")
    return None

def get_all_students(token):
    """Fetches all students handling pagination."""
    students = []
    page = 1
    per_page = 50  # Fetch 50 at a time to reduce requests
    
    print("Fetching students list...")
    while True:
        try:
            url = f"{STUDENTS_URL}?page={page}&per_page={per_page}"
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                print(f"Failed to fetch page {page}: {response.text}")
                break
                
            data = response.json()
            if not data.get("success"):
                break
                
            page_data = data["data"]["data"]
            if not page_data:
                break
                
            students.extend(page_data)
            print(f"Fetched page {page} ({len(page_data)} students)...")
            
            # Check if we reached the last page
            meta = data["data"].get("meta", {})
            last_page = meta.get("last_page", page)
            if page >= last_page:
                break
            
            page += 1
            
        except Exception as e:
            print(f"Error fetching students: {e}")
            break
            
    return students

def get_student_enrollments(token, student_id):
    """Fetches enrollment history for a specific student."""
    url = BOOTCAMP_HISTORY_URL_TEMPLATE.format(student_id=student_id)
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data["data"]["data"]
    except Exception as e:
        print(f"Error fetching enrollment for student {student_id}: {e}")
    return []

def main():
    token = login()
    if not token:
        return

    students = get_all_students(token)
    print(f"Total students found: {len(students)}")
    
    # Dictionary to map Bootcamp Name -> List of Students
    bootcamp_subscribers = {}
    
    print("Fetching enrollments for each student (this might take a moment)...")
    for i, student in enumerate(students):
        s_id = student["id"]
        s_name = student["name"]
        
        # Optional: Print progress every 10 students
        if (i + 1) % 10 == 0:
            print(f"Processing student {i + 1}/{len(students)}...")
            
        enrollments = get_student_enrollments(token, s_id)
        
        for enroll in enrollments:
            b_name = enroll["bootcamp_name"]
            if b_name not in bootcamp_subscribers:
                bootcamp_subscribers[b_name] = []
            
            bootcamp_subscribers[b_name].append(s_name)
            
        # Moderate rate limiting to be polite
        time.sleep(0.1)

    print("\n" + "="*50)
    print("ENROLLMENT REPORT")
    print("="*50)
    
    if not bootcamp_subscribers:
        print("No enrollments found.")
    
    for bootcamp, subs in bootcamp_subscribers.items():
        print(f"\nBootcamp: {bootcamp}")
        print(f"Total Subscribers: {len(subs)}")
        print("-" * 30)
        for sub in subs:
            print(f" - {sub}")

if __name__ == "__main__":
    main()
