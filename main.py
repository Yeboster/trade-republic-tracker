import argparse
import sys
import getpass
from api.auth import AuthClient
from api.timeline import TimelineClient
from api.websocket_client import WebSocketClient

def main():
    parser = argparse.ArgumentParser(description="Trade Republic Tracker")
    parser.add_argument("--phone", help="Phone number for login (e.g., +49123456789)")
    parser.add_argument("--pin", help="PIN for login")
    parser.add_argument("--session", help="Session token (if already logged in)")
    
    args = parser.parse_args()
    
    auth_client = AuthClient()
    
    if args.session:
        print("Using provided session token.")
        session_token = args.session
    elif args.phone and args.pin:
        print(f"Logging in with {args.phone}...")
        try:
            process_id = auth_client.login(args.phone, args.pin)
            print(f"Process ID: {process_id}")
            otp = input("Enter OTP received via SMS: ")
            cookies = auth_client.verify_otp(process_id, otp)
            session_token = cookies.get("tr_session")
            print(f"Logged in! Session Token: {session_token}")
            print(f"Refresh Token: {cookies.get('tr_refresh')}")
        except Exception as e:
            print(f"Error logging in: {e}")
            sys.exit(1)
    else:
        print("Usage: python main.py --phone <PHONE> --pin <PIN>")
        sys.exit(1)
        
    print("Fetching timeline transactions...")
    
    timeline_client = TimelineClient(session_token)
    
    # Connect
    timeline_client.connect()
    
    # Fetch transactions (this will just start the process)
    transactions = timeline_client.get_transactions()
    
    print(f"Transactions found: {len(transactions)}")
    
    # Print some transaction details (focus on Card)
    card_transactions = [
        tx for tx in transactions 
        if tx.get("eventType") in ["card_successful_transaction", "card_refund"]
    ]
    
    print(f"Card transactions found: {len(card_transactions)}")
    
    for tx in card_transactions[:10]:
        amount = tx.get("amount", {})
        value = amount.get("value", 0)
        currency = amount.get("currency", "EUR")
        title = tx.get("title", "Unknown")
        date = tx.get("timestamp", "Unknown")
        print(f"[{date}] {title}: {value} {currency}")

if __name__ == "__main__":
    main()
