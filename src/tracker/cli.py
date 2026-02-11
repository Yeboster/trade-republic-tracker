import asyncio
import argparse
import logging
import os
import sys
import json
from .client import TradeRepublicClient
from .timeline import TimelineManager
from .analysis import PortfolioAnalyzer
from .categories import add_rule, append_rules_to_csv

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
    parser.add_argument("--budget", type=float, help="Monthly spending budget (EUR). Shows alerts if exceeded.")
    parser.add_argument("--export-suggestions", type=str, metavar="PATH",
                        help="Export uncategorized merchants to CSV for review (with AI-suggested categories)")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                        help="Output format for the report (default: text)")
    parser.add_argument("--json-output", type=str, metavar="PATH",
                        help="Write JSON report to file (implies --format json)")
    parser.add_argument("--auto-apply", action="store_true",
                        help="Automatically add high-confidence category suggestions to categories.csv")
    parser.add_argument("--auto-apply-threshold", type=float, default=0.90,
                        metavar="THRESHOLD",
                        help="Minimum confidence score for auto-apply (default: 0.90)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview auto-apply changes without writing to CSV")
    parser.add_argument("--alerts-only", action="store_true",
                        help="Show only spending alerts (skip full report)")
    
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
        from .categories import categorize_merchant, normalize_text
        
        # Get all unique merchants from card transactions, normalized
        raw_merchants = [t["merchant"] for t in transactions if t.get("category") == "card"]
        # Normalize and set to deduplicate
        unique_merchants = sorted(list(set(normalize_text(m) for m in raw_merchants)))
        
        # Print count to stderr so it doesn't pollute CSV if redirected
        print(f"Unique Merchants (Normalized): {len(unique_merchants)}", file=sys.stderr)
        
        print("Merchant,Category")
        
        for m in unique_merchants:
            try:
                # m is already normalized
                cat = categorize_merchant(m)
                # Escape quotes if necessary for CSV
                m_safe = f'"{m}"' if ',' in m else m
                print(f"{m_safe},{cat}")
            except Exception as e:
                # Log error to stderr and continue
                logger.error(f"Failed to process merchant '{m}': {e}")
                print(f"{m},ERROR")
        return

    # 2. Auto-Apply High Confidence Categories
    if args.auto_apply and transactions:
        analyzer = PortfolioAnalyzer(transactions, budget=args.budget)
        suggestions = analyzer.get_high_confidence_suggestions(threshold=args.auto_apply_threshold)
        
        if suggestions:
            print(f"\n🤖 AUTO-APPLY: Found {len(suggestions)} high-confidence suggestions (≥{args.auto_apply_threshold:.0%})")
            print(f"   {'Merchant':<35s}  {'Category':<15s}  {'Conf':>5s}  {'Reason'}")
            print("   " + "─" * 75)
            for s in suggestions:
                conf_pct = f"{s['confidence']:.0%}"
                print(f"   {s['merchant'][:35]:<35s}  {s['category']:<15s}  {conf_pct:>5s}  {s['reason'] or ''}")
            
            if args.dry_run:
                print(f"\n   ℹ️  DRY-RUN: Would add {len(suggestions)} rules to data/categories.csv")
            else:
                added = append_rules_to_csv(suggestions)
                if added > 0:
                    print(f"\n   ✅ Added {added} new rules to data/categories.csv")
                    print("      Re-run with --input to re-categorize transactions.")
                else:
                    print(f"\n   ℹ️  No new rules added (all already exist in CSV)")
        else:
            print(f"\n✓ No high-confidence suggestions (≥{args.auto_apply_threshold:.0%}) to auto-apply.")

    # 3. Export Category Suggestions
    if args.export_suggestions and transactions:
        analyzer = PortfolioAnalyzer(transactions, budget=args.budget)
        count = analyzer.export_category_suggestions(args.export_suggestions)
        if count > 0:
            print(f"\n✅ Exported {count} category suggestions to: {args.export_suggestions}")
            print("   Edit the 'Category' column and add to data/categories.csv")
        else:
            print("\n✓ No uncategorized merchants with 2+ transactions found.")

    # 4. Analyze
    if transactions:
        analyzer = PortfolioAnalyzer(transactions, budget=args.budget)
        
        # Determine format
        output_format = args.format
        if args.json_output:
            output_format = "json"
        
        if output_format == "json":
            report_data = analyzer.generate_json_report()
            
            # Filter to alerts only if requested
            if args.alerts_only:
                report_data = {
                    "generated_at": report_data.get("generated_at"),
                    "alerts": report_data.get("alerts", []),
                    "alert_count": len(report_data.get("alerts", []))
                }
            
            json_output = json.dumps(report_data, indent=2, default=str, ensure_ascii=False)
            
            if args.json_output:
                with open(args.json_output, "w", encoding="utf-8") as f:
                    f.write(json_output)
                logger.info(f"JSON report written to {args.json_output}")
            else:
                print(json_output)
        else:
            if args.alerts_only:
                # Generate only the alerts section
                report = analyzer.generate_report()  # This populates _alerts
                alerts = analyzer.get_alerts()
                
                if alerts:
                    print("\n🚨 SPENDING ALERTS")
                    print("=" * 50)
                    
                    # Group by type
                    cat_spikes = [a for a in alerts if a["type"] == "category_spike"]
                    daily_spikes = [a for a in alerts if a["type"] == "daily_spike"]
                    large_txns = [a for a in alerts if a["type"] in ("large_outlier", "large_first")]
                    new_vendors = [a for a in alerts if a["type"] == "new_merchant"]
                    
                    if cat_spikes:
                        print("\n📊 Category Overspending:")
                        for a in cat_spikes:
                            print(f"   {a['message']}")
                    
                    if daily_spikes:
                        print("\n📅 High Spending Days:")
                        for a in sorted(daily_spikes, key=lambda x: x["amount"], reverse=True)[:5]:
                            print(f"   • {a['date']}: €{a['amount']:.2f} (avg: €{a['average']:.0f})")
                    
                    if large_txns:
                        print("\n💸 Unusual Transactions:")
                        for a in large_txns[:5]:
                            print(f"   • {a['message']}")
                    
                    if new_vendors:
                        print("\n🆕 New Merchants This Week:")
                        for a in new_vendors[:5]:
                            print(f"   • {a['merchant'][:35]} (€{a['total_spent']:.2f})")
                    
                    print(f"\n   Total alerts: {len(alerts)}")
                else:
                    print("\n✅ No spending alerts detected.")
            else:
                report = analyzer.generate_report()
                print(f"\n{report}\n")
    else:
        logger.warning("No transactions available for analysis.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
