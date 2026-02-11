from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Tuple
import logging
import os
import csv

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

    def __init__(self, transactions: List[Dict], budget: float = None):
        self.transactions = [t for t in transactions if self._is_executed(t)]
        self.budget = budget  # Optional monthly spending budget

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
        sections.append(self._spending_insights_section(card_txns, transfer_in))
        sections.append(self._card_section(card_txns))
        sections.append(self._subscription_section(card_txns))
        sections.append(self._uncategorized_section(card_txns))
        sections.append(self._investment_section(invest_txns))
        sections.append(self._transfer_section(transfer_in, transfer_out))
        sections.append(self._budget_history_section(card_txns))
        sections.append(self._monthly_section())

        return "\n\n".join(s for s in sections if s)

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

    # ── Spending Insights ───────────────────────────────────────────

    def _spending_insights_section(self, card_txns, transfer_in_txns) -> str:
        """
        Advanced spending metrics: averages, YoY comparison, savings rate.
        """
        if not card_txns:
            return ""

        # Calculate spending by month
        by_month = defaultdict(float)
        for t in card_txns:
            month = _parse_month(t)
            if t["normalized_amount"] < 0:
                by_month[month] += abs(t["normalized_amount"])

        sorted_months = sorted(by_month.keys())
        if len(sorted_months) < 2:
            return ""

        # Current month and previous months
        current_month = sorted_months[-1]
        current_spend = by_month[current_month]
        
        # Calculate averages (excluding current incomplete month)
        historical_months = sorted_months[:-1]
        if historical_months:
            avg_monthly = sum(by_month[m] for m in historical_months) / len(historical_months)
        else:
            avg_monthly = current_spend

        # Last 3 months average (excluding current)
        recent_months = historical_months[-3:] if len(historical_months) >= 3 else historical_months
        avg_recent = sum(by_month[m] for m in recent_months) / len(recent_months) if recent_months else avg_monthly

        # YoY comparison
        try:
            current_dt = datetime.strptime(current_month, "%Y-%m")
            yoy_month = f"{current_dt.year - 1}-{current_dt.month:02d}"
            yoy_spend = by_month.get(yoy_month, 0)
            yoy_change = ((current_spend - yoy_spend) / yoy_spend * 100) if yoy_spend > 0 else None
        except:
            yoy_spend = 0
            yoy_change = None

        # Savings rate (deposits vs card spending this month)
        deposits_by_month = defaultdict(float)
        for t in transfer_in_txns:
            month = _parse_month(t)
            deposits_by_month[month] += t["normalized_amount"]
        
        current_deposits = deposits_by_month.get(current_month, 0)
        savings_rate = ((current_deposits - current_spend) / current_deposits * 100) if current_deposits > 0 else None

        # Month-to-date pace (extrapolate)
        today = datetime.now()
        day_of_month = today.day
        days_in_month = 30  # Approximation
        projected_spend = (current_spend / day_of_month) * days_in_month if day_of_month > 0 else current_spend

        lines = [
            "── SPENDING INSIGHTS ────────────────────",
            f"  Current Month ({current_month}):",
            f"    Spent (MTD):        {current_spend:>10,.2f}",
            f"    Projected (30d):    {projected_spend:>10,.2f}",
            "",
            f"  Averages:",
            f"    All-Time Monthly:   {avg_monthly:>10,.2f}",
            f"    Recent (3mo):       {avg_recent:>10,.2f}",
        ]

        # MTD vs average indicator
        pace_vs_avg = ((current_spend / day_of_month * days_in_month) / avg_recent - 1) * 100 if avg_recent > 0 and day_of_month > 0 else 0
        if pace_vs_avg > 15:
            lines.append(f"    ⚠️  Pace: +{pace_vs_avg:.0f}% above recent avg")
        elif pace_vs_avg < -15:
            lines.append(f"    ✅ Pace: {pace_vs_avg:.0f}% below recent avg")

        lines.append("")
        lines.append("  Year-over-Year:")
        if yoy_spend > 0:
            lines.append(f"    {yoy_month}:            {yoy_spend:>10,.2f}")
            if yoy_change is not None:
                direction = "↑" if yoy_change > 0 else "↓"
                lines.append(f"    Change:              {direction} {abs(yoy_change):>8.1f}%")
        else:
            lines.append("    (No data for same month last year)")

        if savings_rate is not None:
            lines.append("")
            lines.append(f"  Savings Rate (MTD):    {savings_rate:>9.1f}%")
            if savings_rate < 0:
                lines.append(f"    ⚠️  Spending > Deposits")

        # Budget tracking
        if self.budget and self.budget > 0:
            lines.append("")
            lines.append("  Budget Tracker:")
            lines.append(f"    Monthly Budget:      {self.budget:>10,.2f}")
            lines.append(f"    Spent (MTD):         {current_spend:>10,.2f}")
            remaining = self.budget - current_spend
            pct_used = (current_spend / self.budget) * 100
            lines.append(f"    Remaining:           {remaining:>10,.2f} ({100-pct_used:.0f}%)")
            
            # Budget pace check
            expected_pct = (day_of_month / days_in_month) * 100
            if pct_used > expected_pct + 15:
                lines.append(f"    🔴 Over pace: {pct_used:.0f}% used at day {day_of_month}/{days_in_month}")
            elif pct_used > expected_pct:
                lines.append(f"    🟡 Slightly over pace: {pct_used:.0f}% used")
            else:
                lines.append(f"    🟢 On track: {pct_used:.0f}% used")
            
            # Projected vs budget
            if projected_spend > self.budget:
                overage = projected_spend - self.budget
                lines.append(f"    ⚠️  Projected to exceed budget by {overage:,.2f}")

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
            
            # Weekly (5-9 days), Monthly (25-35 days), or Yearly (360-370 days)
            is_weekly = 5 <= avg_interval <= 9
            is_monthly = 25 <= avg_interval <= 35
            is_yearly = 360 <= avg_interval <= 370

            if is_weekly or is_monthly or is_yearly:
                freq = "Weekly" if is_weekly else ("Monthly" if is_monthly else "Yearly")
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
            if sub['frequency'] == "Weekly":
                total_monthly += sub["amount"] * 4.33  # ~4.33 weeks/month
            elif sub['frequency'] == "Monthly":
                total_monthly += sub["amount"]
            elif sub['frequency'] == "Yearly":
                total_monthly += sub["amount"] / 12

        lines.append("")
        lines.append(f"  Est. Monthly Cost: {total_monthly:>.2f}")
        return "\n".join(lines)

    # ── Uncategorized (Auto-Learn) ──────────────────────────────────

    def _uncategorized_section(self, card_txns) -> str:
        """
        Identify frequently uncategorized merchants and suggest categories.
        Shows merchants tagged as "Other" that appear multiple times.
        """
        if not card_txns:
            return ""

        # Find uncategorized merchants with multiple transactions
        uncategorized = defaultdict(lambda: {"count": 0, "total": 0.0, "last_seen": ""})
        for t in card_txns:
            if t.get("spending_category", "Other") == "Other":
                merchant = t["merchant"]
                uncategorized[merchant]["count"] += 1
                uncategorized[merchant]["total"] += abs(t.get("normalized_amount", 0))
                month = _parse_month(t)
                if month > uncategorized[merchant]["last_seen"]:
                    uncategorized[merchant]["last_seen"] = month

        # Filter to merchants with 2+ transactions (recurring/important)
        frequent_uncategorized = [
            (m, d) for m, d in uncategorized.items() 
            if d["count"] >= 2
        ]
        
        if not frequent_uncategorized:
            return ""

        # Sort by total spending (highest first)
        frequent_uncategorized.sort(key=lambda x: x[1]["total"], reverse=True)
        
        # Limit to top 15
        top_uncategorized = frequent_uncategorized[:15]
        
        # Try to suggest categories based on common keywords (with confidence)
        suggestions = []
        for merchant, data in top_uncategorized:
            category, confidence, reason = self._suggest_category(merchant, with_confidence=True)
            suggestions.append({
                "merchant": merchant,
                "count": data["count"],
                "total": data["total"],
                "last_seen": data["last_seen"],
                "suggested": category,
                "confidence": confidence,
                "reason": reason
            })

        lines = [
            "── UNCATEGORIZED MERCHANTS ──────────────",
            "  (Merchants with 2+ transactions in 'Other' category)",
            "",
            f"  {'Merchant':<28s}  {'Total':>9s}  {'#':>3s}  {'Suggested':<14s}  {'Conf'}",
            "  " + "─" * 72,
        ]
        
        for s in suggestions:
            sugg_text = s["suggested"] or "?"
            # Confidence indicator: ●●● (high), ●●○ (medium), ●○○ (low), ○○○ (none)
            conf = s["confidence"]
            if conf >= 0.85:
                conf_icon = "●●●"
            elif conf >= 0.70:
                conf_icon = "●●○"
            elif conf > 0:
                conf_icon = "●○○"
            else:
                conf_icon = "○○○"
            
            lines.append(
                f"  {s['merchant'][:28]:<28s}  {s['total']:>9.2f}  {s['count']:>3d}  {sugg_text:<14s}  {conf_icon}"
            )
        
        lines.append("")
        lines.append(f"  💡 {len(suggestions)} merchants need categorization")
        lines.append("     Run with --export-suggestions to generate CSV")
        
        return "\n".join(lines)

    def _suggest_category(self, merchant: str, with_confidence: bool = False):
        """
        Heuristic category suggestion based on common keywords.
        
        Args:
            merchant: Merchant name to analyze
            with_confidence: If True, returns (category, confidence, reason) tuple
                            If False, returns just category string (backward compatible)
        
        Returns:
            If with_confidence=False: category string or None
            If with_confidence=True: (category, confidence, reason) or (None, 0, None)
                confidence: 0.0-1.0 score
                reason: explanation of why this category was suggested
        """
        name = merchant.lower()
        
        # Patterns with specificity weights (higher = more specific/confident)
        # Format: (keywords, category, base_confidence, specificity_multiplier)
        patterns = [
            # Food/Dining - High confidence specific terms
            (["ristorante", "trattoria", "osteria", "pizzeria"], "Restaurant", 0.95, 1.0),
            (["restaurant", "bistro", "brasserie"], "Restaurant", 0.90, 1.0),
            (["cafe", "caffè", "coffee"], "Restaurant", 0.75, 0.9),
            (["pizza", "sushi", "kebab", "burger", "ramen"], "Restaurant", 0.80, 0.95),
            (["bar ", " bar", "pub ", " pub"], "Restaurant", 0.65, 0.8),
            (["boulangerie", "patisserie"], "Grocery", 0.90, 1.0),
            (["bakery", "pain"], "Grocery", 0.75, 0.9),
            
            # Grocery - High confidence
            (["supermarket", "supermercato", "supermarché"], "Grocery", 0.95, 1.0),
            (["alimentari", "potraviny", "epicerie"], "Grocery", 0.90, 1.0),
            (["market", "marche", "marché"], "Grocery", 0.70, 0.85),
            (["grocery"], "Grocery", 0.85, 0.95),
            
            # Shopping - Medium confidence (generic terms)
            (["boutique"], "Shopping", 0.75, 0.9),
            (["shop", "store", "magasin"], "Shopping", 0.55, 0.7),
            
            # Health/Pharmacy
            (["pharmacie", "farmacia", "apotheke", "lekaren"], "Health", 0.95, 1.0),
            (["pharmacy", "drogerie"], "Health", 0.85, 0.95),
            (["doctor", "dentist", "medecin", "dentaire"], "Health", 0.90, 1.0),
            (["clinic", "clinique", "klinik"], "Health", 0.85, 0.95),
            
            # Transport - High confidence specific
            (["uber", "bolt", "lyft", "freenow"], "Transport", 0.95, 1.0),
            (["taxi", "cab "], "Transport", 0.85, 0.95),
            (["parking", "aparcament", "parcheggio"], "Transport", 0.90, 1.0),
            (["shell", "bp ", "esso", "total", "eni ", "q8"], "Transport", 0.90, 1.0),
            (["gas", "fuel", "petrol", "essence"], "Transport", 0.75, 0.85),
            (["train", "bus", "metro", "tram", "sncf", "ratp", "bvg"], "Transport", 0.90, 1.0),
            (["transit", "transport"], "Transport", 0.70, 0.8),
            (["rent a car", "car rental", "autonoleggio", "sixt", "hertz", "avis"], "Transport", 0.95, 1.0),
            (["park ", "garage"], "Transport", 0.60, 0.75),
            
            # Entertainment - High confidence
            (["cinema", "cinéma", "kino"], "Entertainment", 0.95, 1.0),
            (["movie", "film", "theatre", "theater", "teatro"], "Entertainment", 0.85, 0.95),
            (["museum", "musée", "museo", "muzeum"], "Entertainment", 0.95, 1.0),
            (["gallery", "galerie"], "Entertainment", 0.80, 0.9),
            (["gym", "fitness", "crossfit"], "Entertainment", 0.90, 1.0),
            (["sport", "climbing", "padel", "tennis", "ski"], "Entertainment", 0.80, 0.9),
            (["ticket", "billet", "biglietto", "entrada"], "Entertainment", 0.60, 0.75),
            (["zoo", "aquarium"], "Entertainment", 0.90, 1.0),
            
            # Travel - High confidence
            (["hotel", "hostel", "motel"], "Travel", 0.90, 1.0),
            (["airbnb", "booking.com", "expedia"], "Travel", 0.95, 1.0),
            (["airline", "airways", "aero"], "Travel", 0.90, 1.0),
            (["flight", "airport"], "Travel", 0.80, 0.9),
            
            # Services
            (["laundry", "laverie", "pressing", "dry clean"], "Services", 0.90, 1.0),
            (["fedex", "ups", "dhl", "chronopost", "colissimo"], "Services", 0.95, 1.0),
            (["post", "poste", "posta"], "Services", 0.70, 0.8),
            
            # Utilities/Subscription
            (["netflix", "spotify", "amazon prime", "disney+", "hbo"], "Subscription", 0.98, 1.0),
            (["mobile", "telecom", "telefon", "vodafone", "orange", "free mobile"], "Utilities", 0.90, 1.0),
            (["subscription", "premium", "membership"], "Subscription", 0.75, 0.85),
        ]
        
        best_match = None
        best_confidence = 0.0
        matched_keyword = None
        
        for keywords, category, base_conf, specificity in patterns:
            for keyword in keywords:
                if keyword in name:
                    # Calculate confidence with adjustments
                    confidence = base_conf * specificity
                    
                    # Boost if keyword appears at the start
                    if name.startswith(keyword.strip()):
                        confidence = min(1.0, confidence * 1.1)
                    
                    # Boost for longer/more specific keyword matches
                    if len(keyword) > 6:
                        confidence = min(1.0, confidence * 1.05)
                    
                    # Penalize very short merchant names (could be ambiguous)
                    if len(name) < 5:
                        confidence *= 0.8
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = category
                        matched_keyword = keyword.strip()
        
        if with_confidence:
            if best_match:
                reason = f"matched '{matched_keyword}'"
                return (best_match, round(best_confidence, 2), reason)
            return (None, 0.0, None)
        
        return best_match

    def export_category_suggestions(self, output_path: str) -> int:
        """
        Export uncategorized merchants to CSV for user review.
        Returns number of suggestions exported.
        
        CSV columns:
        - Merchant: The merchant name
        - Category: Blank (for user to fill in)
        - Transactions: Number of transactions
        - TotalSpent: Total amount spent
        - Suggested: AI-suggested category
        - Confidence: Confidence score (0.0-1.0)
        - Reason: Why this category was suggested
        """
        card_txns = [t for t in self.transactions if t.get("category") == "card"]
        
        # Collect uncategorized
        uncategorized = defaultdict(lambda: {"count": 0, "total": 0.0})
        for t in card_txns:
            if t.get("spending_category", "Other") == "Other":
                merchant = t["merchant"]
                uncategorized[merchant]["count"] += 1
                uncategorized[merchant]["total"] += abs(t.get("normalized_amount", 0))
        
        # Filter to 2+ transactions and get suggestions with confidence
        to_export = []
        for m, d in uncategorized.items():
            if d["count"] >= 2:
                category, confidence, reason = self._suggest_category(m, with_confidence=True)
                to_export.append({
                    "merchant": m,
                    "count": d["count"],
                    "total": d["total"],
                    "suggested": category or "",
                    "confidence": confidence,
                    "reason": reason or ""
                })
        
        if not to_export:
            return 0
        
        # Sort by confidence (highest first), then by total spent
        to_export.sort(key=lambda x: (-x["confidence"], -x["total"]))
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Merchant", "Category", "Transactions", "TotalSpent", "Suggested", "Confidence", "Reason"])
            for item in to_export:
                # Category column left blank for user to fill
                writer.writerow([
                    item["merchant"], 
                    "", 
                    item["count"], 
                    f"{item['total']:.2f}", 
                    item["suggested"],
                    f"{item['confidence']:.2f}",
                    item["reason"]
                ])
        
        logger.info(f"Exported {len(to_export)} category suggestions to {output_path}")
        return len(to_export)

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

    # ── Historical Budget ───────────────────────────────────────

    def _budget_history_section(self, card_txns) -> str:
        """
        Show month-by-month budget adherence (if budget is set).
        """
        if not self.budget or self.budget <= 0:
            return ""

        # Calculate spending by month
        by_month = defaultdict(float)
        for t in card_txns:
            if t["normalized_amount"] < 0:
                month = _parse_month(t)
                by_month[month] += abs(t["normalized_amount"])

        if not by_month:
            return ""

        sorted_months = sorted(by_month.keys())
        # Show last 6 months
        recent_months = sorted_months[-6:]

        lines = [
            "── BUDGET HISTORY (Last 6 Months) ───────",
            f"  Monthly Budget: {self.budget:,.2f} EUR",
            "",
            f"  {'Month':<10s}  {'Spent':>10s}  {'Budget':>10s}  {'Status':>12s}  {'Visual'}",
            "  " + "─" * 60,
        ]

        over_count = 0
        total_over = 0.0

        for month in recent_months:
            spent = by_month[month]
            remaining = self.budget - spent
            pct_used = (spent / self.budget) * 100

            # Visual bar (max 20 chars)
            bar_len = min(int(pct_used / 5), 20)  # 5% per char, max 20
            bar = "█" * bar_len
            
            if spent > self.budget:
                status = f"🔴 +{abs(remaining):,.0f}"
                over_count += 1
                total_over += abs(remaining)
            elif pct_used > 90:
                status = f"🟡 {remaining:,.0f}"
            else:
                status = f"🟢 {remaining:,.0f}"

            lines.append(
                f"  {month:<10s}  {spent:>10,.2f}  {self.budget:>10,.2f}  {status:>12s}  │{bar:<20s}│"
            )

        lines.append("")
        if over_count > 0:
            lines.append(f"  ⚠️  Over budget {over_count} of {len(recent_months)} months (total: {total_over:,.2f} over)")
        else:
            lines.append(f"  ✅ On budget all {len(recent_months)} months")

        return "\n".join(lines)

    # ── JSON Report ──────────────────────────────────────────────

    def generate_json_report(self) -> dict:
        """
        Generate structured JSON report for programmatic use.
        """
        card_txns = [t for t in self.transactions if t.get("category") == "card"]
        invest_txns = [t for t in self.transactions if t.get("category") == "investment"]
        transfer_in = [t for t in self.transactions if t.get("category") == "transfer_in"]
        transfer_out = [t for t in self.transactions if t.get("category") == "transfer_out"]

        # Card metrics
        card_spent = sum(abs(t["normalized_amount"]) for t in card_txns if t["normalized_amount"] < 0)
        card_refund = sum(t["normalized_amount"] for t in card_txns if t["normalized_amount"] > 0)
        
        # Investment metrics
        invest_out = sum(abs(t["normalized_amount"]) for t in invest_txns if t["normalized_amount"] < 0)
        invest_in = sum(t["normalized_amount"] for t in invest_txns if t["normalized_amount"] > 0)
        
        # Transfer metrics
        cash_in = sum(t["normalized_amount"] for t in transfer_in)
        cash_out = sum(abs(t["normalized_amount"]) for t in transfer_out)

        # Monthly breakdown
        by_month = defaultdict(lambda: {"card": 0.0, "investment": 0.0, "deposits": 0.0, "withdrawals": 0.0})
        for t in self.transactions:
            month = _parse_month(t)
            val = t.get("normalized_amount", 0)
            cat = t.get("category", "other")
            if cat == "card" and val < 0:
                by_month[month]["card"] += abs(val)
            elif cat == "investment" and val < 0:
                by_month[month]["investment"] += abs(val)
            elif cat == "transfer_in":
                by_month[month]["deposits"] += val
            elif cat == "transfer_out":
                by_month[month]["withdrawals"] += abs(val)

        # Spending by category
        by_spending_cat = defaultdict(float)
        for t in card_txns:
            if t["normalized_amount"] < 0:
                cat = t.get("spending_category", "Other") or "Other"
                by_spending_cat[cat] += abs(t["normalized_amount"])

        # Top merchants
        merchants = defaultdict(float)
        for t in card_txns:
            if t["normalized_amount"] < 0:
                merchants[t["merchant"]] += abs(t["normalized_amount"])
        top_merchants = sorted(merchants.items(), key=lambda x: x[1], reverse=True)[:20]

        # Subscriptions
        subscriptions = self._detect_subscriptions(card_txns)

        # Budget history
        budget_history = None
        if self.budget and self.budget > 0:
            budget_history = self._budget_history(by_month)

        # Uncategorized merchants with AI suggestions
        uncategorized_merchants = self._get_uncategorized_with_confidence(card_txns)

        return {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_transactions": len(self.transactions),
                "card_transactions": len(card_txns),
                "investment_transactions": len(invest_txns),
            },
            "spending": {
                "gross_spent": round(card_spent, 2),
                "refunds": round(card_refund, 2),
                "net_spent": round(card_spent - card_refund, 2),
            },
            "investments": {
                "total_bought": round(invest_out, 2),
                "total_received": round(invest_in, 2),
                "net_invested": round(invest_out - invest_in, 2),
            },
            "cash_flow": {
                "deposits": round(cash_in, 2),
                "withdrawals": round(cash_out, 2),
                "net": round(cash_in - cash_out, 2),
            },
            "spending_by_category": {k: round(v, 2) for k, v in sorted(by_spending_cat.items(), key=lambda x: x[1], reverse=True)},
            "top_merchants": [{"merchant": m, "spent": round(v, 2)} for m, v in top_merchants],
            "subscriptions": subscriptions,
            "monthly": {month: {k: round(v, 2) for k, v in data.items()} for month, data in sorted(by_month.items())},
            "budget": {
                "monthly_limit": self.budget,
                "history": budget_history
            } if self.budget else None,
            "uncategorized": uncategorized_merchants,
        }

    def _detect_subscriptions(self, card_txns: List[Dict]) -> List[Dict]:
        """Helper to detect subscriptions for JSON output."""
        by_merchant = defaultdict(list)
        for t in card_txns:
            if t["normalized_amount"] < 0:
                by_merchant[t["merchant"]].append(t)

        results = []
        for merchant, txns in by_merchant.items():
            if len(txns) < 2:
                continue
            txns.sort(key=lambda x: x.get("timestamp", 0))
            amounts = [abs(t["normalized_amount"]) for t in txns]
            avg_amount = sum(amounts) / len(amounts)
            if not all(0.9 * avg_amount <= a <= 1.1 * avg_amount for a in amounts):
                continue
            timestamps = []
            for t in txns:
                ts = t.get("timestamp", 0)
                if isinstance(ts, str):
                    try:
                        ts = ts.replace("Z", "+00:00")
                        dt = datetime.fromisoformat(ts)
                        timestamps.append(dt.timestamp())
                    except ValueError:
                        pass
                elif isinstance(ts, (int, float)):
                    timestamps.append(ts / 1000 if ts > 10**11 else ts)
            if len(timestamps) < 2:
                continue
            intervals = [(timestamps[i] - timestamps[i-1]) / 86400 for i in range(1, len(timestamps))]
            if not intervals:
                continue
            avg_interval = sum(intervals) / len(intervals)
            if 5 <= avg_interval <= 9:
                freq = "weekly"
            elif 25 <= avg_interval <= 35:
                freq = "monthly"
            elif 360 <= avg_interval <= 370:
                freq = "yearly"
            else:
                continue
            results.append({
                "merchant": merchant,
                "amount": round(avg_amount, 2),
                "frequency": freq,
                "transaction_count": len(txns),
            })
        return sorted(results, key=lambda x: x["amount"], reverse=True)

    def _budget_history(self, by_month: dict) -> List[Dict]:
        """Calculate historical budget adherence per month."""
        if not self.budget:
            return []
        
        history = []
        for month in sorted(by_month.keys()):
            spent = by_month[month]["card"]
            remaining = self.budget - spent
            pct_used = (spent / self.budget) * 100 if self.budget > 0 else 0
            status = "under" if spent <= self.budget else "over"
            history.append({
                "month": month,
                "spent": round(spent, 2),
                "budget": self.budget,
                "remaining": round(remaining, 2),
                "pct_used": round(pct_used, 1),
                "status": status,
            })
        return history

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

    def _get_uncategorized_with_confidence(self, card_txns: List[Dict]) -> List[Dict]:
        """
        Get uncategorized merchants with AI category suggestions and confidence scores.
        
        Returns a list of dicts with:
        - merchant: name
        - transaction_count: number of transactions
        - total_spent: total amount
        - suggested_category: AI suggestion (or null)
        - confidence: 0.0-1.0 score
        - confidence_level: "high", "medium", "low", or "none"
        - reason: explanation for suggestion
        """
        uncategorized = defaultdict(lambda: {"count": 0, "total": 0.0})
        for t in card_txns:
            if t.get("spending_category", "Other") == "Other":
                merchant = t["merchant"]
                uncategorized[merchant]["count"] += 1
                uncategorized[merchant]["total"] += abs(t.get("normalized_amount", 0))
        
        results = []
        for merchant, data in uncategorized.items():
            if data["count"] >= 2:  # Only include recurring uncategorized
                category, confidence, reason = self._suggest_category(merchant, with_confidence=True)
                
                # Map confidence to human-readable level
                if confidence >= 0.85:
                    level = "high"
                elif confidence >= 0.70:
                    level = "medium"
                elif confidence > 0:
                    level = "low"
                else:
                    level = "none"
                
                results.append({
                    "merchant": merchant,
                    "transaction_count": data["count"],
                    "total_spent": round(data["total"], 2),
                    "suggested_category": category,
                    "confidence": confidence,
                    "confidence_level": level,
                    "reason": reason,
                })
        
        # Sort by confidence (highest first), then by total spent
        results.sort(key=lambda x: (-x["confidence"], -x["total_spent"]))
        return results

    def get_high_confidence_suggestions(self, threshold: float = 0.90) -> List[Dict]:
        """
        Get merchants that have high-confidence category suggestions.
        
        Args:
            threshold: Minimum confidence score (default 0.90)
        
        Returns:
            List of dicts with 'merchant', 'category', 'confidence', 'reason'
            ready to be auto-applied.
        """
        card_txns = [t for t in self.transactions if t.get("category") == "card"]
        all_suggestions = self._get_uncategorized_with_confidence(card_txns)
        
        # Filter by threshold and ensure we have a suggested category
        high_conf = [
            {
                "merchant": s["merchant"],
                "category": s["suggested_category"],
                "confidence": s["confidence"],
                "reason": s["reason"],
                "transaction_count": s["transaction_count"],
                "total_spent": s["total_spent"],
            }
            for s in all_suggestions
            if s["suggested_category"] and s["confidence"] >= threshold
        ]
        
        return high_conf
