from collections import defaultdict
from datetime import datetime
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def _parse_month(txn: Dict) -> str:
    ts = txn.get("timestamp")
    try:
        if isinstance(ts, (int, float)):
            dt = datetime.fromtimestamp(ts / 1000 if ts > 10**11 else ts)
        elif isinstance(ts, str):
            ts = ts.replace("+0000", "+00:00").replace("Z", "+00:00")
            dt = datetime.fromisoformat(ts)
        else:
            return "Unknown"
        return dt.strftime("%Y-%m")
    except Exception:
        return "Unknown"


class PortfolioAnalyzer:
    """
    Full portfolio analysis: card spending, investments, and combined overview.
    """

    def __init__(self, transactions: List[Dict]):
        self.transactions = [t for t in transactions if self._is_executed(t)]

    @staticmethod
    def _is_executed(txn: Dict) -> bool:
        status = txn.get("status", "").upper()
        return status in ("EXECUTED", "CONFIRMED", "")

    def generate_report(self) -> str:
        card_txns = [t for t in self.transactions if t.get("category") == "card"]
        invest_txns = [t for t in self.transactions if t.get("category") == "investment"]
        transfer_in = [t for t in self.transactions if t.get("category") == "transfer_in"]
        transfer_out = [t for t in self.transactions if t.get("category") == "transfer_out"]

        sections = []
        sections.append(self._overview_section(card_txns, invest_txns, transfer_in, transfer_out))
        sections.append(self._card_section(card_txns))
        sections.append(self._subscription_section(card_txns))
        sections.append(self._investment_section(invest_txns))
        sections.append(self._transfer_section(transfer_in, transfer_out))
        sections.append(self._monthly_section())

        return "\n\n".join(sections)

    # ── Overview ────────────────────────────────────────────────────

    def _overview_section(self, card_txns, invest_txns, transfer_in_txns, transfer_out_txns) -> str:
        # Card
        card_spent = sum(abs(t["normalized_amount"]) for t in card_txns if t["normalized_amount"] < 0)
        card_refund = sum(t["normalized_amount"] for t in card_txns if t["normalized_amount"] > 0)
        card_net = card_spent - card_refund

        # Investment
        invest_out = sum(abs(t["normalized_amount"]) for t in invest_txns if t["normalized_amount"] < 0)
        invest_in = sum(t["normalized_amount"] for t in invest_txns if t["normalized_amount"] > 0)
        invest_net = invest_out - invest_in  # Net Invested (Cash -> Asset)

        # Transfers (Cash Flow)
        cash_in = sum(t["normalized_amount"] for t in transfer_in_txns)
        cash_out = sum(abs(t["normalized_amount"]) for t in transfer_out_txns)
        net_cash_flow = cash_in - cash_out  # Net Cash Added to Account

        lines = [
            "═══════════════════════════════════════",
            "       PORTFOLIO OVERVIEW (EUR)",
            "═══════════════════════════════════════",
            f"  Total Transactions:  {len(self.transactions):,}",
            "",
            "  ── SPENDING (CARD) ──",
            f"  Gross Spent:         {card_spent:>12,.2f}",
            f"  Refunds:             {card_refund:>12,.2f}",
            f"  Net Spent:           {card_net:>12,.2f}",
            "",
            "  ── INVESTMENTS ──",
            f"  Buys (Cash Out):     {invest_out:>12,.2f}",
            f"  Sells/Divs (Cash In):{invest_in:>12,.2f}",
            f"  Net Invested:        {invest_net:>12,.2f}",
            "",
            "  ── CASH FLOW ──",
            f"  Deposits:            {cash_in:>12,.2f}",
            f"  Withdrawals:         {cash_out:>12,.2f}",
            f"  Net Cash Added:      {net_cash_flow:>12,.2f}",
            "═══════════════════════════════════════",
        ]
        return "\n".join(lines)

    # ── Card Spending ───────────────────────────────────────────────

    def _card_section(self, card_txns) -> str:
        if not card_txns:
            return "── CARD SPENDING ──\n  No card transactions found."

        total_spent = sum(abs(t["normalized_amount"]) for t in card_txns if t["normalized_amount"] < 0)
        total_refund = sum(t["normalized_amount"] for t in card_txns if t["normalized_amount"] > 0)
        net = total_spent - total_refund

        # Merchant breakdown (net)
        merchants = defaultdict(float)
        for t in card_txns:
            merchants[t["merchant"]] += (-t["normalized_amount"])

        top = sorted(
            [(m, a) for m, a in merchants.items() if a > 0],
            key=lambda x: x[1], reverse=True
        )[:10]

        # Category breakdown
        by_category = defaultdict(lambda: {"out": 0.0, "in": 0.0, "count": 0})
        for t in card_txns:
            cat = t.get("spending_category", "Other") or "Other"
            val = t["normalized_amount"]
            by_category[cat]["count"] += 1
            if val < 0:
                by_category[cat]["out"] += abs(val)
            else:
                by_category[cat]["in"] += val

        lines = [
            "── CARD SPENDING DETAILS ────────────────",
            f"  Net Spent:     {net:>10,.2f}",
            "",
            "  By Category:",
        ]
        for cat, data in sorted(by_category.items(), key=lambda x: x[1]["out"], reverse=True):
            net_cat = data["out"] - data["in"]
            lines.append(f"    {cat:<20s}  {net_cat:>10,.2f}  ({data['count']} txns)")

        lines.append("")
        lines.append("  Top 10 Merchants (net):")
        for i, (m, a) in enumerate(top, 1):
            lines.append(f"    {i:>2}. {m:<30s} {a:>10,.2f}")

        return "\n".join(lines)

    # ── Subscriptions ───────────────────────────────────────────────

    def _subscription_section(self, card_txns) -> str:
        """
        Heuristic detection of recurring monthly payments.
        Criteria:
        - Same merchant
        - At least 2 transactions
        - Similar amount (within 10%)
        - Interval ~28-32 days
        """
        if not card_txns:
            return ""

        # Group by merchant
        by_merchant = defaultdict(list)
        for t in card_txns:
            # Only consider negative amounts (payments)
            if t["normalized_amount"] < 0:
                by_merchant[t["merchant"]].append(t)

        potential_subs = []

        for merchant, txns in by_merchant.items():
            if len(txns) < 2:
                continue

            # Sort by date
            txns.sort(key=lambda x: x.get("timestamp", 0))

            amounts = [abs(t["normalized_amount"]) for t in txns]
            avg_amount = sum(amounts) / len(amounts)

            # Check amount consistency (all within 10% of average)
            is_consistent_amount = all(0.9 * avg_amount <= a <= 1.1 * avg_amount for a in amounts)
            
            if not is_consistent_amount:
                continue

            # Check intervals
            timestamps = []
            for t in txns:
                ts = t.get("timestamp", 0)
                if isinstance(ts, str):
                    try:
                        # Normalize ISO string to timestamp
                        ts = ts.replace("Z", "+00:00")
                        dt = datetime.fromisoformat(ts)
                        timestamps.append(dt.timestamp())
                    except ValueError:
                        pass
                elif isinstance(ts, (int, float)):
                    if ts > 10**11: # Millis
                        timestamps.append(ts / 1000)
                    else:
                        timestamps.append(ts)
            
            if len(timestamps) < 2:
                continue

            intervals = []
            for i in range(1, len(timestamps)):
                diff_days = (timestamps[i] - timestamps[i-1]) / 86400
                intervals.append(diff_days)

            if not intervals:
                continue

            avg_interval = sum(intervals) / len(intervals)
            
            # Monthly (25-35 days) or Yearly (360-370 days)
            is_monthly = 25 <= avg_interval <= 35
            is_yearly = 360 <= avg_interval <= 370

            if is_monthly or is_yearly:
                freq = "Monthly" if is_monthly else "Yearly"
                last_date = _parse_month(txns[-1]) # Just show YYYY-MM
                potential_subs.append({
                    "merchant": merchant,
                    "amount": avg_amount,
                    "frequency": freq,
                    "count": len(txns),
                    "last_seen": last_date
                })

        if not potential_subs:
            return ""

        # Sort by amount desc
        potential_subs.sort(key=lambda x: x["amount"], reverse=True)

        lines = [
            "── POTENTIAL SUBSCRIPTIONS ──────────────",
            f"  {'Merchant':<30s}  {'Amount':>10s}  {'Freq':<8s}  {'Last'}",
            "  " + "─" * 60,
        ]
        
        total_monthly = 0
        for sub in potential_subs:
            lines.append(f"  {sub['merchant']:<30s}  {sub['amount']:>10.2f}  {sub['frequency']:<8s}  {sub['last_seen']}")
            if sub['frequency'] == "Monthly":
                total_monthly += sub["amount"]
            elif sub['frequency'] == "Yearly":
                total_monthly += sub["amount"] / 12

        lines.append("")
        lines.append(f"  Est. Monthly Cost: {total_monthly:>.2f}")
        return "\n".join(lines)

    # ── Investments ─────────────────────────────────────────────────

    def _investment_section(self, invest_txns) -> str:
        if not invest_txns:
            return "── INVESTMENTS ──\n  No investment transactions found."

        total_invested = sum(abs(t["normalized_amount"]) for t in invest_txns if t["normalized_amount"] < 0)
        total_received = sum(t["normalized_amount"] for t in invest_txns if t["normalized_amount"] > 0)

        # Group by subtitle type
        by_type = defaultdict(lambda: {"out": 0.0, "in": 0.0, "count": 0})
        for t in invest_txns:
            sub = t.get("subtitle_raw", "").strip() or "Other"
            val = t["normalized_amount"]
            by_type[sub]["count"] += 1
            if val < 0:
                by_type[sub]["out"] += abs(val)
            else:
                by_type[sub]["in"] += val

        # Group by asset
        by_asset = defaultdict(lambda: {"out": 0.0, "in": 0.0, "count": 0})
        for t in invest_txns:
            asset = t["merchant"]  # title = asset name
            val = t["normalized_amount"]
            by_asset[asset]["count"] += 1
            if val < 0:
                by_asset[asset]["out"] += abs(val)
            else:
                by_asset[asset]["in"] += val

        top_assets = sorted(by_asset.items(), key=lambda x: x[1]["out"], reverse=True)[:10]

        lines = [
            "── INVESTMENT DETAILS ───────────────────",
            f"  Net Invested:    {total_invested - total_received:>12,.2f}",
            "",
            "  By Type:",
        ]
        for sub, data in sorted(by_type.items(), key=lambda x: x[1]["out"], reverse=True):
            lines.append(f"    {sub:<25s}  Out: {data['out']:>10,.2f}  In: {data['in']:>10,.2f}  ({data['count']})")

        lines.append("")
        lines.append("  Top 10 Assets (by amount invested):")
        for i, (asset, data) in enumerate(top_assets, 1):
            net = data["in"] - data["out"]
            lines.append(f"    {i:>2}. {asset:<35s}  Invested: {data['out']:>10,.2f}  Received: {data['in']:>10,.2f}  Net: {net:>+10,.2f}")

        return "\n".join(lines)

    # ── Transfers ───────────────────────────────────────────────────

    def _transfer_section(self, t_in, t_out) -> str:
        if not t_in and not t_out:
            return ""

        total_in = sum(t["normalized_amount"] for t in t_in)
        total_out = sum(abs(t["normalized_amount"]) for t in t_out)

        lines = [
            "── TRANSFERS ────────────────────────────",
            f"  Deposits:      {total_in:>12,.2f}  ({len(t_in)})",
            f"  Withdrawals:   {total_out:>12,.2f}  ({len(t_out)})",
            f"  Net Flow:      {total_in - total_out:>12,.2f}",
        ]
        return "\n".join(lines)

    # ── Monthly ─────────────────────────────────────────────────────

    def _monthly_section(self) -> str:
        by_month = defaultdict(lambda: {"card_net": 0.0, "invest_net": 0.0, "cash_net": 0.0})

        for t in self.transactions:
            month = _parse_month(t)
            val = t.get("normalized_amount", 0)
            cat = t.get("category", "other")

            if cat == "card":
                by_month[month]["card_net"] += val # Negative = spent
            elif cat == "investment":
                by_month[month]["invest_net"] += val # Negative = bought
            elif cat in ("transfer_in", "transfer_out"):
                by_month[month]["cash_net"] += val

        lines = [
            "── MONTHLY BREAKDOWN ────────────────",
            f"  {'Month':<10s}  {'Card Net':>12s}  {'Invest Net':>12s}  {'Cash Net':>12s}",
            "  " + "─" * 60,
        ]
        for month in sorted(by_month.keys()):
            d = by_month[month]
            # Card Net: Show POSITIVE for spending (easier to read) -> -1 * val
            # Actually, "Card Net" usually implies spending. Let's show "Net Spent" as positive.
            card_spent_display = -d['card_net'] 
            
            # Invest Net: Show "Net Invested" (Out - In) -> -1 * val
            invest_net_display = -d['invest_net']

            lines.append(
                f"  {month:<10s}  {card_spent_display:>12,.2f}  {invest_net_display:>12,.2f}  {d['cash_net']:>12,.2f}"
            )

        # Add ASCII chart for card spending
        lines.append("")
        lines.append(self._spending_chart(by_month))

        return "\n".join(lines)

    def _spending_chart(self, by_month: dict, bar_width: int = 40) -> str:
        """Generate a simple ASCII bar chart for monthly card spending."""
        sorted_months = sorted(by_month.keys())
        if not sorted_months:
            return ""
        
        # Get last 12 months of spending
        recent_months = sorted_months[-12:]
        spending_values = [-by_month[m]["card_net"] for m in recent_months]  # Positive = spent
        
        max_spend = max(spending_values) if spending_values else 1
        if max_spend <= 0:
            return ""
        
        lines = [
            "",
            "  ── MONTHLY SPENDING TREND (Last 12 Months) ──",
            ""
        ]
        
        for i, month in enumerate(recent_months):
            spent = spending_values[i]
            bar_len = int((spent / max_spend) * bar_width) if max_spend > 0 else 0
            bar = "█" * bar_len
            # Shorten month display: 2024-01 -> Jan'24
            try:
                short_month = datetime.strptime(month, "%Y-%m").strftime("%b'%y")
            except:
                short_month = month[:7]
            lines.append(f"  {short_month:<7} │{bar:<{bar_width}} {spent:>8,.0f}€")
        
        lines.append(f"          └{'─' * bar_width}┘")
        return "\n".join(lines)
