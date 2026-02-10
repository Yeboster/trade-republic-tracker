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

        sections = []
        sections.append(self._overview_section(card_txns, invest_txns))
        sections.append(self._card_section(card_txns))
        sections.append(self._investment_section(invest_txns))
        sections.append(self._monthly_section())

        return "\n\n".join(sections)

    # ── Overview ────────────────────────────────────────────────────

    def _overview_section(self, card_txns, invest_txns) -> str:
        card_out = sum(abs(t["normalized_amount"]) for t in card_txns if t["normalized_amount"] < 0)
        card_in = sum(t["normalized_amount"] for t in card_txns if t["normalized_amount"] > 0)

        invest_out = sum(abs(t["normalized_amount"]) for t in invest_txns if t["normalized_amount"] < 0)
        invest_in = sum(t["normalized_amount"] for t in invest_txns if t["normalized_amount"] > 0)

        total_out = card_out + invest_out
        total_in = card_in + invest_in

        lines = [
            "═══════════════════════════════════════",
            "       PORTFOLIO OVERVIEW (EUR)",
            "═══════════════════════════════════════",
            f"  Total Transactions:  {len(self.transactions):,}",
            f"  Card Transactions:   {len(card_txns):,}",
            f"  Investment Events:   {len(invest_txns):,}",
            "",
            f"  Total Outflow:       {total_out:>12,.2f}",
            f"  Total Inflow:        {total_in:>12,.2f}",
            f"  Net:                 {total_in - total_out:>12,.2f}",
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

        lines = [
            "── CARD SPENDING ─────────────────────",
            f"  Gross Spent:   {total_spent:>10,.2f}",
            f"  Refunds:       {total_refund:>10,.2f}",
            f"  Net Spent:     {net:>10,.2f}",
            "",
            "  Top 10 Merchants (net):",
        ]
        for i, (m, a) in enumerate(top, 1):
            lines.append(f"    {i:>2}. {m:<30s} {a:>10,.2f}")

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
            "── INVESTMENTS ──────────────────────",
            f"  Total Invested:  {total_invested:>12,.2f}",
            f"  Total Received:  {total_received:>12,.2f}",
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

    # ── Monthly ─────────────────────────────────────────────────────

    def _monthly_section(self) -> str:
        by_month = defaultdict(lambda: {"card_out": 0.0, "card_in": 0.0, "invest_out": 0.0, "invest_in": 0.0})

        for t in self.transactions:
            month = _parse_month(t)
            val = t.get("normalized_amount", 0)
            cat = t.get("category", "other")

            if cat == "card":
                if val < 0:
                    by_month[month]["card_out"] += abs(val)
                else:
                    by_month[month]["card_in"] += val
            elif cat == "investment":
                if val < 0:
                    by_month[month]["invest_out"] += abs(val)
                else:
                    by_month[month]["invest_in"] += val

        lines = [
            "── MONTHLY BREAKDOWN ────────────────",
            f"  {'Month':<10s}  {'Card Spent':>12s}  {'Card Rfnd':>10s}  {'Invested':>12s}  {'Received':>10s}",
            "  " + "─" * 60,
        ]
        for month in sorted(by_month.keys()):
            d = by_month[month]
            lines.append(
                f"  {month:<10s}  {d['card_out']:>12,.2f}  {d['card_in']:>10,.2f}  {d['invest_out']:>12,.2f}  {d['invest_in']:>10,.2f}"
            )

        return "\n".join(lines)
