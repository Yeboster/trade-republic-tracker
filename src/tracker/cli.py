import asyncio
import argparse
import logging
import os
import sys
from .client import TradeRepublicClient
from .timeline import TimelineManager
from .analysis import SpendingAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Main")

async def main():
    parser = argparse.ArgumentParser(description="Trade Republic Card Transaction Tracker")
    parser.add_argument("--phone", help="Phone number (international format)")
    parser.add_argument("--pin", help="PIN")
    parser.add_argument("--limit", type=int, default=50, help="Number of transactions to fetch")
    parser.add_argument("--output", default="transactions.csv", help="Output CSV file")
    # For testing/CI reuse
    parser.add_argument("--otp", help="OTP code (if you know it ahead of time, rarely works due to expiry)")
    
    args = parser.parse_args()

    # Load credentials from env if not provided
    phone = args.phone or os.environ.get("TR_PHONE")
    pin = args.pin or os.environ.get("TR_PIN")
    otp_env = os.environ.get("TR_OTP")

    if not phone or not pin:
        logger.error("Phone number and PIN are required. Set TR_PHONE and TR_PIN env vars or use arguments.")
        return

    client = TradeRepublicClient(phone_number=phone, pin=pin)
    
    # Try to load existing tokens 
    client.load_tokens()

    try:
        # Check if we need to login
        if not client.session_token:
            logger.info("No session token found. Logging in...")
            await asyncio.to_thread(client.login)
            
            # Interactive OTP
            otp = args.otp or otp_env
            if not otp:
                if sys.stdin.isatty():
                    otp = input(f"Enter OTP sent to {phone}: ")
                else:
                    logger.error("OTP required and no TTY available. Set --otp or TR_OTP.")
                    return
            
            await asyncio.to_thread(client.verify_otp, otp)
        else:
            # Attempt refresh
            try:
                await asyncio.to_thread(client.refresh_session)
            except Exception as e:
                logger.warning(f"Session refresh failed: {e}. Re-logging in...")
                await asyncio.to_thread(client.login)
                otp = args.otp or otp_env
                if not otp:
                     if sys.stdin.isatty():
                        otp = input(f"Enter OTP sent to {phone}: ")
                     else:
                        logger.error("OTP required and no TTY available.")
                        return
                await asyncio.to_thread(client.verify_otp, otp)

        timeline = TimelineManager(client)
        
        # 3. Fetch Transactions
        logger.info(f"Fetching last {args.limit} transactions...")
        transactions = await timeline.fetch_transactions(limit=args.limit)
        
        # 4. Filter Card Transactions
        card_txns = timeline.filter_card_transactions()
        logger.info(f"Found {len(card_txns)} card transactions out of {len(transactions)} total.")
        
        print("\n--- Card Transactions Preview ---")
        for txn in card_txns[:5]:
            amt = txn.get('amount', {}).get('value')
            curr = txn.get('amount', {}).get('currency')
            print(f"{txn['timestamp']} | {txn['title']} | {amt} {curr} | {txn.get('status')}")
        print("---------------------------------\n")

        # 5. Analysis
        analyzer = SpendingAnalyzer(card_txns)
        report = analyzer.generate_report()
        print(report)
        print("\n---------------------------------\n")

        # 6. Export
        timeline.export_to_csv(args.output)
        logger.info(f"Done. Check {args.output}")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
