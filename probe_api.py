import httpx
import logging
import json
import os
import asyncio
import websockets
from typing import Optional, Dict, List, Any

# Adjust logging level to DEBUG to see raw WS frames
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TradeRepublicClientProbe:
    BASE_URL = "https://api.traderepublic.com/api/v1"
    WS_URL = "wss://api.traderepublic.com/"
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    CONNECT_MSG = 'connect 31 {"locale":"en","platformId":"webtrading","platformVersion":"chrome - 120.0.0","clientId":"app.traderepublic.com","clientVersion":"3.174.0"}'

    def __init__(self):
        self.session_token = None
        self.ws = None
        self.sub_id_counter = 0

    def load_tokens(self):
        if os.path.exists(".tokens.json"):
            with open(".tokens.json", "r") as f:
                tokens = json.load(f)
                self.session_token = tokens.get("session_token")
            logger.info("Tokens loaded.")
        else:
            logger.error("No .tokens.json found! Run 'tracker login' first.")
            exit(1)

    async def probe_timeline(self):
        self.load_tokens()
        
        extra_headers = {
            "User-Agent": self.USER_AGENT,
            "Origin": "https://app.traderepublic.com",
            "Cookie": f"tr_session={self.session_token}"
        }

        try:
            async with websockets.connect(self.WS_URL, additional_headers=extra_headers) as ws:
                self.ws = ws
                await ws.send(self.CONNECT_MSG)
                
                # Handshake
                resp = await ws.recv()
                logger.debug(f"Handshake: {resp}")
                
                # Subscribe to timelineTransactions (first page)
                sub_id = 1
                payload = {"token": self.session_token}
                msg = f"sub {sub_id} timelineTransactions {json.dumps(payload)}"
                await ws.send(msg)
                logger.info(f"Sent sub {sub_id}...")

                # Listen for response
                while True:
                    resp = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    if resp.startswith(f"{sub_id} A"):
                        # We got data!
                        json_str = resp[len(f"{sub_id} A "):]
                        data = json.loads(json_str)
                        
                        # Inspect the first few items
                        items = data.get("items", [])
                        if items:
                            logger.info(f"Received {len(items)} items.")
                            print("\n--- RAW ITEM DUMP (First 3) ---")
                            for i, item in enumerate(items[:3]):
                                print(json.dumps(item, indent=2))
                            print("-------------------------------\n")
                        else:
                            logger.warning("No items in response.")
                            
                        break
                    elif resp.startswith(f"{sub_id} E"):
                         logger.error(f"Error: {resp}")
                         break
                    else:
                        logger.debug(f"Ignored: {resp[:50]}...")

        except Exception as e:
            logger.error(f"Probe failed: {e}")

if __name__ == "__main__":
    probe = TradeRepublicClientProbe()
    asyncio.run(probe.probe_timeline())
