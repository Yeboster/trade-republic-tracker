import websocket
import json
import threading
import time
import uuid
from constants import WS_BASE_URL, WEBHOOK_VERSION, USER_AGENT

class WebSocketClient:
    def __init__(self, token, on_message_callback=None):
        self.token = token
        self.ws = None
        self.connected = False
        self.subscriptions = {}  # id -> callback
        self.sub_id_counter = 0
        self.on_message_callback = on_message_callback
        self.lock = threading.Lock()

    def connect(self):
        # websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(
            WS_BASE_URL,
            header={"User-Agent": USER_AGENT},
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        
        # Start the WebSocket connection in a separate thread
        wst = threading.Thread(target=self.ws.run_forever)
        wst.daemon = True
        wst.start()
        
        # Wait for connection
        timeout = 10
        start_time = time.time()
        while not self.connected and time.time() - start_time < timeout:
            time.sleep(0.1)
            
        if not self.connected:
            raise Exception("WebSocket connection timed out")

    def _on_open(self, ws):
        print("WebSocket opened")
        # Send connect message
        connect_payload = {
            "locale": "en",
            "platformId": "webtrading",
            "platformVersion": "chrome - 96.0.4664",
            "clientVersion": "1.27.5"
        }
        msg = f"connect {WEBHOOK_VERSION} {json.dumps(connect_payload)}"
        ws.send(msg)
        self.connected = True

    def _on_message(self, ws, message):
        # Parse message: <id> <state> <payload>
        parts = message.split(" ", 2)
        if len(parts) < 2:
            return
            
        msg_id = parts[0]
        state = parts[1]
        payload = parts[2] if len(parts) > 2 else ""

        if msg_id == "connected": 
            # Initial response from connect? Go code says: "received connect response"
            # The Go code reads the first message after connect.
            # "connect <version> <json>" -> response
            # Actually, the response to "connect" might not have an ID or might be special.
            # But let's assume standard format for now.
            print(f"Connected response: {message}")
            return

        if state == "A": # Data?
            # Find subscription
            with self.lock:
                callback = self.subscriptions.get(msg_id)
            
            if callback:
                callback(payload)
                # Unsubscribe after receiving data? Go code does it.
                # But for timeline, maybe we want updates?
                # The Go code for timeline transactions loops and subscribes with cursor.
                # This implies pagination, so one-shot makes sense for that.
                self.unsubscribe(msg_id)
        elif state == "C": # Continue?
             print(f"Continue: {message}")
        elif state == "E": # Error
             print(f"Error: {message}")

    def _on_error(self, ws, error):
        print(f"WebSocket error: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        print("WebSocket closed")
        self.connected = False

    def subscribe(self, request_type, payload_data, callback):
        with self.lock:
            self.sub_id_counter += 1
            sub_id = str(self.sub_id_counter)
            self.subscriptions[sub_id] = callback

        payload = {
            "type": request_type,
            "token": self.token,
            **payload_data
        }
        
        msg = f"sub {sub_id} {json.dumps(payload)}"
        self.ws.send(msg)
        return sub_id

    def unsubscribe(self, sub_id):
        with self.lock:
            if sub_id in self.subscriptions:
                del self.subscriptions[sub_id]
        
        msg = f"unsub {sub_id}"
        self.ws.send(msg)

