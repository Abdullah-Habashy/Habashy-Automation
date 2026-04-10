import requests
import json

# Configuration
BASE_URL = "https://api.abdullah-habashy.com/v1/academy"
LOGIN_URL = f"{BASE_URL}/auth/login"
BOOTCAMPS_URL = f"{BASE_URL}/admin/bootcamps"

# Credentials (from documentation)
EMAIL = "abdelrahmanmostafa785@gmail.com"
PASSWORD = "password"

def login():
    """Authenticates the user and returns the access token."""
    payload = {
        "identifier": EMAIL,
        "password": PASSWORD
    }
    
    try:
        response = requests.post(LOGIN_URL, json=payload)
        response.raise_for_status()
        
        data = response.json()
        if data.get("success"):
            token = data["data"]["token"]
            print("Login successful. Token acquired.")
            return token
        else:
            print(f"Login failed: {data.get('message')}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error during login: {e}")
        return None

def get_bootcamps(token):
    """Fetches and prints the list of bootcamps."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # You can add parameters like ?page=1 or ?sort=name here if needed
    # For now, we fetch the default list
    try:
        response = requests.get(BOOTCAMPS_URL, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if data.get("success"):
            bootcamps = data["data"]["data"]
            print(f"\nSuccessfully retrieved {len(bootcamps)} bootcamps:\n")
            print(f"{'ID':<5} | {'Name':<40} | {'Instructor':<20} | {'Price'}")
            print("-" * 80)
            
            for bootcamp in bootcamps:
                b_id = bootcamp.get("id", "N/A")
                name = bootcamp.get("name", "N/A")
                instructor = bootcamp.get("instructor", "N/A")
                price = f"{bootcamp.get('price', 0)} {bootcamp.get('price_currency', '')}"
                
                # Truncate long names for display
                if len(name) > 37:
                    name = name[:37] + "..."
                
                print(f"{b_id:<5} | {name:<40} | {instructor:<20} | {price}")
        else:
            print(f"Failed to retrieve bootcamps: {data.get('message')}")
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching bootcamps: {e}")

if __name__ == "__main__":
    print("Starting process...")
    token = login()
    if token:
        get_bootcamps(token)
