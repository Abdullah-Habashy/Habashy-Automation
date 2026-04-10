import requests
import json
import sys

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

def find_student_by_phone(token, phone_number):
    """Searches for a student by phone number."""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Using the general search filter which typically covers phone, name, code
    params = {
        "filter[search]": phone_number,
        "page": 1
    }
    
    try:
        response = requests.get(STUDENTS_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get("success"):
            students = data["data"]["data"]
            # Filter exactly by phone in case 'search' is fuzzy
            exact_matches = [s for s in students if s.get("phone") == phone_number]
            
            if exact_matches:
                return exact_matches[0]
            elif students:
                 # If no exact phone match, but search returned results, maybe the user entered a partial number or name?
                 # For now, let's just return the first result if it looks reasonable, or strict match.
                 # The user asked specifically for phone verification, so let's stick to strict phone checking if possible,
                 # or print what we found.
                 print(f"Warning: Exact phone match not found, but found student: {students[0]['name']} ({students[0]['phone']})")
                 return students[0]
            
    except Exception as e:
        print(f"Error searching for student: {e}")
    
    return None

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
        print(f"Error fetching enrollment: {e}")
    return []

def main():
    token = login()
    if not token:
        return

    while True:
        print("\n" + "="*40)
        phone_input = input("Enter phone number (or 'q' to quit): ").strip()
        
        if phone_input.lower() == 'q':
            break
            
        if not phone_input:
            continue

        print(f"Searching for student with phone: {phone_input}...")
        student = find_student_by_phone(token, phone_input)
        
        if student:
            print(f"Student Found: {student['name']} (ID: {student['id']})")
            print("Checking enrollments...")
            
            enrollments = get_student_enrollments(token, student['id'])
            
            if enrollments:
                print(f"\nUser is enrolled in {len(enrollments)} bootcamps:")
                for i, enroll in enumerate(enrollments, 1):
                    # Check if subscription is active/valid if needed, but request asked for "subscribed"
                    # We print Details
                    status = "Active" if enroll.get("days_left", 0) > 0 else "Expired"
                    print(f"{i}. {enroll['bootcamp_name']} ({enroll['semester_name']}) - [{status}]")
            else:
                print("\nStudent found, but NOT enrolled in any bootcamps.")
        else:
            print("No student found with this phone number.")

if __name__ == "__main__":
    main()
