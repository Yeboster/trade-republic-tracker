import requests
import json
import logging

BASE_URL = "https://api.traderepublic.com/api/v1"

class Auth:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            "Content-Type": "application/json"
        })
        self.process_id = None
        self.tr_session = None
        self.tr_refresh = None

    def login(self, phone_number, pin):
        """Initiates login with phone number and PIN."""
        url = f"{BASE_URL}/auth/web/login"
        payload = {
            "phoneNumber": phone_number,
            "pin": pin
        }
        
        logging.info(f"Logging in with {phone_number}...")
        response = self.session.post(url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            self.process_id = data.get("processId")
            logging.info(f"Login initiated. Process ID: {self.process_id}")
            return self.process_id
        else:
            logging.error(f"Login failed: {response.text}")
            response.raise_for_status()

    def verify_otp(self, otp):
        """Verifies OTP using the process ID obtained from login."""
        if not self.process_id:
            raise ValueError("No process ID found. Please call login() first.")
        
        url = f"{BASE_URL}/auth/web/login/{self.process_id}/{otp}"
        
        logging.info("Verifying OTP...")
        response = self.session.post(url)
        
        if response.status_code == 200:
            cookies = response.cookies
            self.tr_session = cookies.get("tr_session")
            self.tr_refresh = cookies.get("tr_refresh")
            
            if self.tr_session and self.tr_refresh:
                logging.info("OTP verified successfully. Tokens received.")
                self.save_tokens()
                return {
                    "tr_session": self.tr_session,
                    "tr_refresh": self.tr_refresh
                }
            else:
                logging.error("OTP verified but tokens not found in cookies.")
                return None
        else:
            logging.error(f"OTP verification failed: {response.text}")
            response.raise_for_status()

    def save_tokens(self, filename="tokens.json"):
        """Saves tokens to a file."""
        import json
        with open(filename, "w") as f:
            json.dump({
                "tr_session": self.tr_session,
                "tr_refresh": self.tr_refresh
            }, f)
        logging.info(f"Tokens saved to {filename}")

    def load_tokens(self, filename="tokens.json"):
        """Loads tokens from a file."""
        import json
        import os
        if os.path.exists(filename):
            with open(filename, "r") as f:
                data = json.load(f)
                self.tr_session = data.get("tr_session")
                self.tr_refresh = data.get("tr_refresh")
                # Set cookies in session
                self.session.cookies.set("tr_session", self.tr_session)
                self.session.cookies.set("tr_refresh", self.tr_refresh)
            logging.info(f"Tokens loaded from {filename}")
            return True
        return False


    def refresh_session(self):
        """Refreshes the session token."""
        # This implementation assumes we have the cookies set in the session
        # or we manually set them if implementing token persistence.
        url = f"{BASE_URL}/auth/web/session"
        response = self.session.get(url)
        if response.status_code == 200:
             # Update tokens from cookies if changed
             cookies = response.cookies
             new_session = cookies.get("tr_session")
             new_refresh = cookies.get("tr_refresh")
             if new_session: self.tr_session = new_session
             if new_refresh: self.tr_refresh = new_refresh
             return True
        return False
