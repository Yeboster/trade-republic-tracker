import asyncio
import os
import logging
import json
import csv
from datetime import datetime
from dotenv import load_dotenv
from tr_api.auth import Auth
from tr_api.websocket import WebSocketClient
from tr_api.models import Transaction, EventType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("tracker.log"),
        logging.StreamHandler()
    ]
)

# Load .env
load_dotenv()

PHONE_NUMBER = os.getenv("TR_PHONE_NUMBER")
PIN = os.getenv("TR_PIN")
OUTPUT_FILE = "card_transactions.csv"

# Global storage
all_transactions = []
card_transactions = []

def save_to_csv(transactions, filename):
    if not transactions:
        return
    
    # Define headers based on Transaction model
    headers = ["id", "timestamp", "type", "title", "subtitle", "amount", "currency", "status"]
    
    file_exists = os.path.isfile(filename)
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for tx in transactions:
            row = {
                "id": tx.id,
                "timestamp": tx.timestamp,
                "type": tx.event_type,
                "title": tx.title,
                "subtitle": tx.subtitle,
                "amount": tx.amount.decimal_value,
                "currency": tx.amount.currency,
                "status": tx.status
            }
            writer.writerow(row)
    logging.info(f"Saved {len(transactions)} transactions to {filename}")

async def main():
    auth = Auth()
    
    if not auth.load_tokens():
        if not PHONE_NUMBER or not PIN:
            logging.error("No tokens found and TR_PHONE_NUMBER/TR_PIN not set in .env")
            return

        try:
            process_id = auth.login(PHONE_NUMBER, PIN)
            print(f"Login initiated for {PHONE_NUMBER}. Check your app for OTP.")
            otp = input("Enter OTP: ")
            tokens = auth.verify_otp(otp)
            if not tokens:
                logging.error("Failed to obtain tokens.")
                return
        except Exception as e:
            logging.error(f"Login failed: {e}")
            return

    session_token = auth.tr_session
    client = WebSocketClient(session_token)
    
    if not await client.connect():
        return

    # Callback for Timeline Details (Optional for now, but useful for deep analysis)
    async def on_timeline_detail(sub_id, msg_type, data):
        if msg_type == "A":
            # Enhance existing transaction data if needed
            # For now, just logging
            # logging.debug(f"Detail for {data.get('id')}: {json.dumps(data)}")
            await client.unsubscribe(sub_id)

    # Callback for Timeline Transactions
    async def on_timeline_transactions(sub_id, msg_type, data):
        if msg_type == "A":
            items = data.get("items", [])
            logging.info(f"Received batch of {len(items)} transactions.")
            
            for item in items:
                try:
                    tx = Transaction.from_dict(item)
                    all_transactions.append(tx)
                    
                    if tx.is_card_transaction():
                        card_transactions.append(tx)
                        logging.info(f"💳 CARD TX: {tx.title} - {tx.amount.decimal_value} {tx.amount.currency}")
                        
                        # Subscribe to details for card transactions specifically
                        # payload = {"type": "timelineDetailV2", "id": tx.id}
                        # await client.subscribe(payload, on_timeline_detail)
                    else:
                        logging.debug(f"Other TX: {tx.title} ({tx.event_type})")
                        
                except Exception as e:
                    logging.error(f"Error parsing transaction: {e}")

            # Pagination
            cursors = data.get("cursors", {})
            after = cursors.get("after")
            if after:
                logging.info(f"Fetching history (cursor: {after})...")
                await client.subscribe({
                    "type": "timelineTransactions",
                    "after": after
                }, on_timeline_transactions)
                
                # Unsubscribe from the previous page to keep connection clean
                await client.unsubscribe(sub_id)
            else:
                logging.info("Reached end of transaction history.")
                # Save immediately when done
                save_to_csv(card_transactions, OUTPUT_FILE)
                
        elif msg_type == "E":
            logging.error(f"Error in timelineTransactions: {data}")

    # Start fetching
    logging.info("Starting timeline fetch...")
    await client.subscribe({"type": "timelineTransactions"}, on_timeline_transactions)

    # Keep running until we likely have all data
    # In a real app, we'd wait for the "end of history" signal, but here we use a timeout
    try:
        # Wait for 60 seconds or until user stops
        for i in range(60):
            if i % 10 == 0:
                logging.info(f"Collected {len(all_transactions)} total, {len(card_transactions)} card transactions...")
                save_to_csv(card_transactions, OUTPUT_FILE)
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logging.info("Stopping...")
    finally:
        save_to_csv(card_transactions, OUTPUT_FILE)
        if client.ws:
            await client.ws.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
