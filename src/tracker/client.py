import httpx
import logging
import json
import os
import asyncio
import websockets
from typing import Optional, Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradeRepublicClient:
    BASE_URL = "https://api.traderepublic.com/api/v1"
    WS_URL = "wss://api.traderepublic.com/"
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # WebSocket Connect Message (Platform info is crucial)
    CONNECT_MSG = "connect 31 {\"locale\":\"en\",\"platformId\":\"webtrading\",\"platformVersion\":\"chrome - 120.0.0\",\"clientId\":\"app.traderepublic.com\",\"clientVersion\":\"3.174.0\"}"

    def __init__(self, phone_number: str = None, pin: str = None):
        self.phone_number = phone_number
        self.pin = pin
        self.session_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.process_id: Optional[str] = None
        
        self.client = httpx.Client(
            base_url=self.BASE_URL,
            headers={
                "User-Agent": self.USER_AGENT,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=10.0
        )
        self.ws = None
        self.sub_id_counter = 0

    def load_tokens(self):
        """
        Loads tokens from a local file.
        """
        if os.path.exists(".tokens.json"):
            try:
                with open(".tokens.json", "r") as f:
                    tokens = json.load(f)
                    self.session_token = tokens.get("session_token")
                    self.refresh_token = tokens.get("refresh_token")
                logger.info("Tokens loaded from file.")
            except Exception as e:
                logger.error(f"Failed to load tokens: {e}")
        else:
            logger.info("No token file found.")

    def login(self) -> str:
        """
        Initiates login flow.
        Returns the process_id needed for OTP.
        """
        if not self.phone_number or not self.pin:
            raise ValueError("Phone number and PIN required for login.")
        
        payload = {
            "phoneNumber": self.phone_number,
            "pin": self.pin
        }
        
        logger.info(f"Logging in with {self.phone_number}...")
        try:
            response = self.client.post("/auth/web/login", json=payload)
            response.raise_for_status()
            
            # Capture session token from cookies if present
            self._update_tokens_from_response(response)
            
            data = response.json()
            self.process_id = data.get("processId")
            
            logger.info(f"Login initiated. Process ID: {self.process_id}")
            return self.process_id
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Login failed: {e.response.text}")
            raise

    def verify_otp(self, otp: str):
        """
        Completes login flow with OTP.
        """
        if not self.process_id:
            raise ValueError("No active login process. Call login() first.")
        
        endpoint = f"/auth/web/login/{self.process_id}/{otp}"
        
        logger.info(f"Verifying OTP for process {self.process_id}...")
        try:
            response = self.client.post(endpoint)
            response.raise_for_status()
            
            self._update_tokens_from_response(response)
            
            if self.session_token and self.refresh_token:
                logger.info("Login successful! Session and refresh tokens captured.")
                self._save_tokens()
            else:
                logger.warning("Login completed but tokens might be missing.")
                
        except httpx.HTTPStatusError as e:
            logger.error(f"OTP verification failed: {e.response.text}")
            raise

    def refresh_session(self):
        """
        Refreshes the session token using the refresh token.
        """
        if not self.refresh_token:
            logger.warning("No refresh token available.")
            return

        logger.info("Refreshing session...")
        
        cookies = {"tr_refresh": self.refresh_token}
        
        try:
            response = self.client.get("/auth/web/session", cookies=cookies)
            response.raise_for_status()
            
            self._update_tokens_from_response(response)
            logger.info("Session refreshed.")
            self._save_tokens()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Session refresh failed: {e.response.text}")
            raise

    def _update_tokens_from_response(self, response: httpx.Response):
        """
        Extracts tr_session and tr_refresh from cookies.
        """
        for cookie in response.cookies.jar:
            if cookie.name == "tr_session":
                self.session_token = cookie.value
            elif cookie.name == "tr_refresh":
                self.refresh_token = cookie.value

    def _save_tokens(self):
        """
        Saves tokens to a local file (insecure, for MVP).
        """
        tokens = {
            "session_token": self.session_token,
            "refresh_token": self.refresh_token
        }
        with open(".tokens.json", "w") as f:
            json.dump(tokens, f)

    async def ws_connect(self):
        """
        Establishes WebSocket connection and performs handshake.
        """
        if not self.session_token:
            raise ValueError("No session token. Log in first.")

        logger.info(f"Connecting to WebSocket {self.WS_URL}...")
        try:
            extra_headers = {
                "User-Agent": self.USER_AGENT,
                "Origin": "https://app.traderepublic.com",
            }
            # Pass session token as cookie
            if self.session_token:
                extra_headers["Cookie"] = f"tr_session={self.session_token}"

            self.ws = await websockets.connect(
                self.WS_URL,
                additional_headers=extra_headers,
            )
            logger.info("Sent connect message.")
            await self.ws.send(self.CONNECT_MSG)
            
            response = await asyncio.wait_for(self.ws.recv(), timeout=10.0)
            logger.info(f"Handshake response: {response[:200]}")
            if "connected" in response:
                logger.info("WebSocket handshake successful.")
            else:
                logger.warning(f"Unexpected handshake response: {response}")
                
        except asyncio.TimeoutError:
            logger.error("WebSocket handshake timed out (10s). Server didn't respond to connect message.")
            raise
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            raise

    async def close(self):
        if self.ws:
            await self.ws.close()
        self.client.close()

    async def _ws_subscribe(self, type_name: str, payload: Dict[str, Any] = None) -> int:
        """
        Sends a subscription request.
        Returns the subscription ID.
        """
        if not self.ws:
            await self.ws_connect()
            
        self.sub_id_counter += 1
        sub_id = self.sub_id_counter
        
        data = payload or {}
        data["token"] = self.session_token
        data["type"] = type_name
        
        msg = f"sub {sub_id} {json.dumps(data)}"
        logger.debug(f"Sending sub: {msg}")
        await self.ws.send(msg)
        
        return sub_id

    async def _ws_unsubscribe(self, sub_id: int):
        """
        Unsubscribes from a subscription.
        """
        if not self.ws:
            return
        
        data = {"token": self.session_token}
        msg = f"unsub {sub_id} {json.dumps(data)}"
        logger.debug(f"Sending unsub: {sub_id}")
        await self.ws.send(msg)

    async def fetch_timeline_transactions(self, limit: int = 100) -> List[Dict]:
        """
        Fetches timeline transactions.
        Iterates through pages until limit is reached or no more data.
        """
        if not self.ws:
            await self.ws_connect()
            
        all_transactions = []
        cursor_after = None
        
        max_loops = 50
        loops = 0
        
        logger.info("Starting timeline fetch...")
        
        while loops < max_loops:
            loops += 1
            
            payload = {}
            if cursor_after:
                payload["after"] = cursor_after
                
            sub_id = await self._ws_subscribe("timelineTransactions", payload)
            
            valid_data = None
            
            try:
                while True:
                    try:
                        response = await asyncio.wait_for(self.ws.recv(), timeout=10.0)
                    except asyncio.TimeoutError:
                        logger.error("Timeout waiting for WebSocket response")
                        break
                        
                    if response.startswith("echo"):
                         continue

                    parts = response.split(maxsplit=2)
                    
                    if len(parts) < 2:
                        continue
                        
                    try:
                        resp_id = int(parts[0])
                    except ValueError:
                        continue
                        
                    if resp_id != sub_id:
                        continue
                        
                    state = parts[1]
                    
                    if state == "C": 
                        # 'C'ontinue / Processing - ignore
                        continue
                    elif state == "E": 
                        # 'E'rror
                        logger.error(f"WebSocket Error for sub {sub_id}: {parts[2] if len(parts) > 2 else ''}")
                        break
                    elif state == "A": 
                        # 'A'dd (Initial payload)
                        if len(parts) > 2:
                            valid_data = json.loads(parts[2])
                        break
                    elif state == "D":
                         # 'D'elete (Update) - usually not initial payload
                         pass
                    else:
                        # Fallback
                        if len(parts) > 2:
                             valid_data = json.loads(parts[2])
                        break
                
                await self._ws_unsubscribe(sub_id)
                
                if not valid_data:
                    break
                
                items = valid_data.get("items", [])
                all_transactions.extend(items)
                
                cursors = valid_data.get("cursors", {})
                cursor_after = cursors.get("after")
                
                logger.info(f"Page {loops}: Fetched {len(items)} items. Total: {len(all_transactions)}")
                
                if not cursor_after or len(all_transactions) >= limit:
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching page {loops}: {e}")
                await self._ws_unsubscribe(sub_id)
                break
                
        return all_transactions[:limit]
