import requests
from constants import API_BASE_URL, USER_AGENT

class AuthClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json"
        })

    def login(self, phone_number, pin):
        """
        Initiates the login process.
        Returns the processId needed for OTP verification.
        """
        url = f"{API_BASE_URL}/auth/web/login"
        payload = {
            "phoneNumber": phone_number,
            "pin": pin
        }
        
        response = self.session.post(url, json=payload)
        
        if response.status_code >= 400:
            raise Exception(f"Login failed: {response.status_code} {response.text}")
            
        data = response.json()
        return data.get("processId")

    def verify_otp(self, process_id, otp):
        """
        Verifies the OTP and returns the session cookies.
        """
        url = f"{API_BASE_URL}/auth/web/login/{process_id}/{otp}"
        
        response = self.session.post(url)
        
        if response.status_code >= 400:
            raise Exception(f"OTP verification failed: {response.status_code} {response.text}")
            
        # Extract cookies
        cookies = response.cookies.get_dict()
        return cookies

    def refresh_session(self, refresh_token):
        # TODO: Implement refresh logic if needed
        pass
