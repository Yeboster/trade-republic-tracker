import asyncio
import websockets
import json
import logging

WS_URL = "wss://api.traderepublic.com/"
VERSION = "33"

class WebSocketClient:
    def __init__(self, token):
        self.token = token
        self.ws = None
        self.sub_id_counter = 0
        self.subscriptions = {} # Map sub_id -> callback
        self.connected = False

    async def connect(self):
        """Connects to the WebSocket server."""
        logging.info(f"Connecting to WebSocket {WS_URL}...")
        try:
            self.ws = await websockets.connect(WS_URL)
            self.connected = True
            
            # Send connect message
            connect_msg = f"connect {VERSION} {{}}"
            await self.ws.send(connect_msg)
            logging.info("Sent connect message.")
            
            # Receive response (initial 'connected' message)
            response = await self.ws.recv()
            logging.info(f"Received connect response: {response}")

            if "connected" in response:
                logging.info("WebSocket connected successfully.")
                # Start listening loop in background
                asyncio.create_task(self.listen())
                return True
            else:
                logging.error(f"Failed to connect: {response}")
                await self.ws.close()
                self.connected = False
                return False
        except Exception as e:
            logging.error(f"Error connecting to WebSocket: {e}")
            self.connected = False
            return False

    async def subscribe(self, payload, callback):
        """Subscribes to a specific topic."""
        if not self.ws or not self.connected:
            raise ConnectionError("WebSocket is not connected.")

        self.sub_id_counter += 1
        sub_id = str(self.sub_id_counter)
        self.subscriptions[sub_id] = callback

        # Add token to payload if not present
        if "token" not in payload:
             payload["token"] = self.token

        msg = f"sub {sub_id} {json.dumps(payload)}"
        await self.ws.send(msg)
        logging.info(f"Subscribed to {sub_id} (Type: {payload.get('type')})")
        return sub_id

    async def unsubscribe(self, sub_id):
        """Unsubscribes from a topic."""
        if not self.ws or not self.connected:
            return

        msg = f"unsub {sub_id}"
        await self.ws.send(msg)
        if sub_id in self.subscriptions:
            del self.subscriptions[sub_id]
        logging.info(f"Unsubscribed from {sub_id}")

    async def listen(self):
        """Listens for incoming messages."""
        try:
            async for message in self.ws:
                parts = message.split(" ", 2)
                if len(parts) < 2:
                    logging.warning(f"Invalid message format: {message}")
                    continue
                
                sub_id = parts[0]
                msg_type = parts[1] # A (Action/Data), C (Continue), E (Error)
                data = parts[2] if len(parts) > 2 else ""

                if sub_id in self.subscriptions:
                    callback = self.subscriptions[sub_id]
                    try:
                        parsed_data = json.loads(data) if data else None
                        await callback(sub_id, msg_type, parsed_data)
                    except json.JSONDecodeError:
                        logging.error(f"Failed to decode JSON for sub {sub_id}: {data}")
                else:
                    # Echo or keep-alive might come here
                    logging.debug(f"Received message for unknown subscription {sub_id}: {message}")

        except websockets.exceptions.ConnectionClosed as e:
            logging.error(f"WebSocket connection closed: {e}")
            self.connected = False
