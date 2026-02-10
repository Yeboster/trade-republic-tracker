import httpx
import logging
import json
import os
import asyncio
import websockets
from typing import Optional, Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradeRepublicClient:
    BASE_URL = "https://api.traderepublic.com/api/v1"
    WS_URL = "wss://api.traderepublic.com/"
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    CONNECT_MSG = 'connect 31 {"locale":"en","platformId":"webtrading","platformVersion":"chrome - 120.0.0","clientId":"app.traderepublic.com","clientVersion":"3.174.0"}'

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
            self._update_tokens_from_response(response)
            data = response.json()
            self.process_id = data.get("processId")
            logger.info(f"Login initiated. Process ID: {self.process_id}")
            return self.process_id
        except httpx.HTTPStatusError as e:
            logger.error(f"Login failed: {e.response.text}")
            raise

    def verify_otp(self, otp: str):
        if not self.process_id:
            raise ValueError("No active login process. Call login() first.")
        
        endpoint = f"/auth/web/login/{self.process_id}/{otp}"
        logger.info("Verifying OTP...")
        try:
            response = self.client.post(endpoint)
            response.raise_for_status()
            self._update_tokens_from_response(response)
            if self.session_token and self.refresh_token:
                logger.info("OTP verified successfully. Tokens received.")
                self._save_tokens()
            else:
                logger.warning("Login completed but tokens might be missing.")
        except httpx.HTTPStatusError as e:
            logger.error(f"OTP verification failed: {e.response.text}")
            raise

    def refresh_session(self):
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
        for cookie in response.cookies.jar:
            if cookie.name == "tr_session":
                self.session_token = cookie.value
            elif cookie.name == "tr_refresh":
                self.refresh_token = cookie.value

    def _save_tokens(self):
        tokens = {
            "session_token": self.session_token,
            "refresh_token": self.refresh_token
        }
        with open(".tokens.json", "w") as f:
            json.dump(tokens, f)
        logger.info("Tokens saved to tokens.json")

    async def ws_connect(self):
        if not self.session_token:
            raise ValueError("No session token. Log in first.")

        logger.info(f"Connecting to WebSocket {self.WS_URL}...")
        try:
            extra_headers = {
                "User-Agent": self.USER_AGENT,
                "Origin": "https://app.traderepublic.com",
            }
            if self.session_token:
                extra_headers["Cookie"] = f"tr_session={self.session_token}"

            self.ws = await websockets.connect(
                self.WS_URL,
                additional_headers=extra_headers,
            )
            await self.ws.send(self.CONNECT_MSG)
            logger.info("Sent connect message.")
            
            response = await asyncio.wait_for(self.ws.recv(), timeout=10.0)
            logger.info(f"Handshake response: {response[:200]}")
            if "connected" in response:
                logger.info("WebSocket handshake successful.")
            else:
                logger.warning(f"Unexpected handshake response: {response}")
                
        except asyncio.TimeoutError:
            logger.error("WebSocket handshake timed out (10s).")
            raise
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            raise

    async def close(self):
        if self.ws:
            await self.ws.close()
        self.client.close()

    async def _ws_subscribe(self, type_name: str, payload: Dict[str, Any] = None) -> int:
        if not self.ws:
            await self.ws_connect()
            
        self.sub_id_counter += 1
        sub_id = self.sub_id_counter
        
        data = payload or {}
        data["token"] = self.session_token
        data["type"] = type_name
        
        msg = f"sub {sub_id} {json.dumps(data)}"
        await self.ws.send(msg)
        return sub_id

    async def _ws_unsubscribe(self, sub_id: int):
        if not self.ws:
            return
        data = {"token": self.session_token}
        msg = f"unsub {sub_id} {json.dumps(data)}"
        await self.ws.send(msg)

    async def _ws_receive_response(self, sub_id: int, timeout: float = 15.0) -> Optional[Dict]:
        """
        Waits for a response matching sub_id. Returns parsed JSON or None.
        """
        while True:
            try:
                response = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
            except asyncio.TimeoutError:
                logger.error(f"Timeout waiting for sub {sub_id}")
                return None
                
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
                continue
            elif state == "E":
                logger.error(f"WS Error sub {sub_id}: {parts[2] if len(parts) > 2 else ''}")
                return None
            elif state == "A":
                if len(parts) > 2:
                    return json.loads(parts[2])
                return None
            elif state == "D":
                continue
            else:
                if len(parts) > 2:
                    return json.loads(parts[2])
                return None

    async def fetch_timeline_transactions(self, limit: int = 0) -> List[Dict]:
        """
        Fetches timeline transactions. 
        limit=0 means fetch ALL (paginate until exhausted).
        """
        if not self.ws:
            await self.ws_connect()
            
        all_transactions = []
        cursor_after = None
        
        # For 3k+ transactions, allow up to 200 pages (typical page ~20-50 items)
        max_pages = 500
        page = 0
        
        fetch_all = (limit == 0)
        
        logger.info(f"Starting timeline fetch ({'all' if fetch_all else f'limit={limit}'})...")
        
        while page < max_pages:
            page += 1
            
            payload = {}
            if cursor_after:
                payload["after"] = cursor_after
                
            sub_id = await self._ws_subscribe("timelineTransactions", payload)
            
            try:
                valid_data = await self._ws_receive_response(sub_id, timeout=15.0)
                await self._ws_unsubscribe(sub_id)
                
                if not valid_data:
                    break
                
                items = valid_data.get("items", [])
                all_transactions.extend(items)
                
                cursors = valid_data.get("cursors", {})
                cursor_after = cursors.get("after")
                
                logger.info(f"Page {page}: +{len(items)} items (total: {len(all_transactions)})")
                
                # Stop conditions
                if not cursor_after:
                    logger.info("No more pages.")
                    break
                if not fetch_all and len(all_transactions) >= limit:
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                await self._ws_unsubscribe(sub_id)
                break
        
        if not fetch_all:
            return all_transactions[:limit]
        return all_transactions
