import asyncio
import argparse
import logging
import os
import sys
from .client import TradeRepublicClient
from .timeline import TimelineManager
from .analysis import PortfolioAnalyzer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Main")


async def main():
    parser = argparse.ArgumentParser(description="Trade Republic Portfolio Tracker")
    parser.add_argument("--phone", help="Phone number (international format)")
    parser.add_argument("--pin", help="PIN")
    parser.add_argument("--limit", type=int, default=0,
                        help="Max transactions to fetch (0 = all, default: all)")
    parser.add_argument("--output", default="transactions.csv", help="Output CSV file")
    parser.add_argument("--input", help="Input CSV file (analyze existing data without fetching)")
    parser.add_argument("--otp", help="OTP code")
    parser.add_argument("--card-only", action="store_true",
                        help="Only show/export card transactions")
    parser.add_argument("--invest-only", action="store_true",
                        help="Only show/export investment transactions")
    
    args = parser.parse_args()

    # ── Mode: Offline Analysis ──────────────────────────────
    if args.input:
        if not os.path.exists(args.input):
            logger.error(f"Input file not found: {args.input}")
            return
            
        logger.info(f"Loading transactions from {args.input}...")
        import csv
        transactions = []
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Reconstruct dict structure expected by analyzer
                    # Analyzer expects: normalized_amount, category, merchant, spending_category
                    try:
                        t = {
                            "normalized_amount": float(row.get("normalized_amount", 0)),
                            "category": row.get("category", "other"),
                            "merchant": row.get("merchant", "Unknown"),
                            "spending_category": row.get("spending_category", ""),
                            "timestamp": row.get("timestamp"),
                            "status": row.get("status"),
                            "currency": row.get("currency", "EUR"),
                            "subtitle_raw": row.get("subtitle_raw", ""),
                        }
                        transactions.append(t)
                    except ValueError:
                        continue # Header or bad row
        except Exception as e:
            logger.error(f"Failed to read CSV: {e}")
            return

        logger.info(f"Loaded {len(transactions)} transactions.")
        analyzer = PortfolioAnalyzer(transactions)
        report = analyzer.generate_report()
        print(f"\n{report}\n")
        return

    # ── Mode: Fetch & Analyze ───────────────────────────────
    phone = args.phone or os.environ.get("TR_PHONE")
    pin = args.pin or os.environ.get("TR_PIN")
    otp_env = os.environ.get("TR_OTP")

    if not phone or not pin:
        logger.error("Phone and PIN required. Set TR_PHONE/TR_PIN or use --phone/--pin.")
        return

    client = TradeRepublicClient(phone_number=phone, pin=pin)
    client.load_tokens()

    try:
        # ── Auth ────────────────────────────────────────────────
        if not client.session_token:
            logger.info("No session token. Logging in...")
            await asyncio.to_thread(client.login)
            otp = args.otp or otp_env
            if not otp:
                if sys.stdin.isatty():
                    otp = input(f"Enter OTP sent to {phone}: ")
                else:
                    logger.error("OTP required. Set --otp or TR_OTP.")
                    return
            await asyncio.to_thread(client.verify_otp, otp)
        else:
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
                        logger.error("OTP required. Set --otp or TR_OTP.")
                        return
                await asyncio.to_thread(client.verify_otp, otp)

        # ── Fetch ───────────────────────────────────────────────
        timeline = TimelineManager(client)
        
        limit_label = "all" if args.limit == 0 else str(args.limit)
        logger.info(f"Fetching transactions (limit: {limit_label})...")
        transactions = await timeline.fetch_transactions(limit=args.limit)
        logger.info(f"Fetched {len(transactions)} total transactions.")

        # ── Classify ────────────────────────────────────────────
        all_classified = timeline.filter_all_classified()
        
        card_count = sum(1 for t in all_classified if t["category"] == "card")
        invest_count = sum(1 for t in all_classified if t["category"] == "investment")
        other_count = sum(1 for t in all_classified if t["category"] == "other")
        
        logger.info(f"Classified: {card_count} card, {invest_count} investment, {other_count} other")

        # ── Analysis ────────────────────────────────────────────
        analyzer = PortfolioAnalyzer(all_classified)
        report = analyzer.generate_report()
        print(f"\n{report}\n")

        # ── Export ──────────────────────────────────────────────
        categories = None
        if args.card_only:
            categories = ["card"]
        elif args.invest_only:
            categories = ["investment"]

        timeline.export_to_csv(args.output, categories=categories)
        logger.info(f"Done. Exported to {args.output}")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        await client.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
