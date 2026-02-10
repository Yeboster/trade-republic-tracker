import asyncio
import argparse
import logging
import os
import sys
from .client import TradeRepublicClient
from .timeline import TimelineManager
from .analysis import PortfolioAnalyzer
from .categories import add_rule

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
    
    # New features
    parser.add_argument("--map", action="append", help="Map merchant to category (format: 'Merchant Name=Category')")
    parser.add_argument("--list-merchants", action="store_true", help="List all unique merchants and exit (useful for LLM categorization)")
    
    args = parser.parse_args()

    # ── Custom Rules ────────────────────────────────────────
    if args.map:
        for rule in args.map:
            if "=" in rule:
                merchant, cat = rule.split("=", 1)
                add_rule(merchant.strip(), cat.strip())
                logger.debug(f"Added custom rule: '{merchant}' -> '{cat}'")
            else:
                logger.warning(f"Invalid mapping format: {rule}. Use 'Merchant=Category'")

    transactions = []

    # ── Mode: Offline Analysis ──────────────────────────────
    if args.input:
        if not os.path.exists(args.input):
            logger.error(f"Input file not found: {args.input}")
            return
            
        logger.info(f"Loading transactions from {args.input}...")
        import csv
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
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
                        # Re-apply categorization if offline (in case rules changed)
                        if t["category"] == "card":
                            from .categories import categorize_merchant
                            t["spending_category"] = categorize_merchant(t["merchant"])
                        
                        transactions.append(t)
                    except ValueError:
                        continue 
        except Exception as e:
            logger.error(f"Failed to read CSV: {e}")
            return

        logger.info(f"Loaded {len(transactions)} transactions.")
        
    # ── Mode: Fetch ─────────────────────────────────────────
    else:
        phone = args.phone or os.environ.get("TR_PHONE")
        pin = args.pin or os.environ.get("TR_PIN")
        otp_env = os.environ.get("TR_OTP")

        if not phone or not pin:
            logger.error("Phone and PIN required. Set TR_PHONE/TR_PIN or use --phone/--pin.")
            return

        client = TradeRepublicClient(phone_number=phone, pin=pin)
        client.load_tokens()

        try:
            # Auth logic...
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

            # Fetch
            timeline = TimelineManager(client)
            limit_label = "all" if args.limit == 0 else str(args.limit)
            logger.info(f"Fetching transactions (limit: {limit_label})...")
            transactions = await timeline.fetch_transactions(limit=args.limit)
            logger.info(f"Fetched {len(transactions)} total transactions.")
            
            # Use filter_all_classified to ensure categories are applied
            transactions = timeline.filter_all_classified()
            
            # Log breakdown
            card_count = sum(1 for t in transactions if t["category"] == "card")
            invest_count = sum(1 for t in transactions if t["category"] == "investment")
            other_count = sum(1 for t in transactions if t["category"] == "other")
            logger.info(f"Classified: Card={card_count}, Investment={invest_count}, Other={other_count}")
            
            # Export if output requested
            categories = None
            if args.card_only:
                categories = ["card"]
            elif args.invest_only:
                categories = ["investment"]
            timeline.export_to_csv(args.output, categories=categories)
            logger.info(f"Exported to {args.output}")

        except Exception as e:
            logger.error(f"Error fetching: {e}", exc_info=True)
            return
        finally:
            await client.close()

    # ── Post-Processing & Output ────────────────────────────
    
    # 1. Feature: List Merchants (for LLM extraction)
    if args.list_merchants:
        # Get all unique merchants from card transactions
        merchants = sorted(list(set(t["merchant"] for t in transactions if t.get("category") == "card")))
        
        # Print count to stderr so it doesn't pollute CSV if redirected
        print(f"Unique Merchants: {len(merchants)}", file=sys.stderr)
        
        print("Merchant,Category")
        from .categories import categorize_merchant
        
        for m in merchants:
            try:
                cat = categorize_merchant(m)
                # Escape quotes if necessary for CSV
                m_safe = f'"{m}"' if ',' in m else m
                # Force UTF-8 output handling implicitly by Python 3, but catch errors
                print(f"{m_safe},{cat}")
            except Exception as e:
                # Log error to stderr and continue
                logger.error(f"Failed to process merchant '{m}': {e}")
                # Print a safe fallback to keep the CSV structure valid
                safe_m = m.encode('ascii', 'ignore').decode('ascii')
                print(f"{safe_m},ERROR")
        return

    # 2. Analyze
    if transactions:
        analyzer = PortfolioAnalyzer(transactions)
        report = analyzer.generate_report()
        print(f"\n{report}\n")
    else:
        logger.warning("No transactions available for analysis.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
