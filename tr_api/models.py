from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any

class EventType(str, Enum):
    # Card related
    CARD_SUCCESSFUL_TRANSACTION = "card_successful_transaction"
    CARD_REFUND = "card_refund"
    CARD_FAILED_TRANSACTION = "card_failed_transaction"
    CARD_SUCCESSFUL_VERIFICATION = "card_successful_verification"
    CARD_FAILED_VERIFICATION = "card_failed_verification"
    
    # Payments
    PAYMENT_INBOUND = "PAYMENT_INBOUND"
    PAYMENT_OUTBOUND = "PAYMENT_OUTBOUND"
    PAYMENT_INBOUND_SEPA_DIRECT_DEBIT = "PAYMENT_INBOUND_SEPA_DIRECT_DEBIT"
    
    # Benefits
    BENEFITS_SAVEBACK_EXECUTION = "benefits_saveback_execution"
    BENEFITS_SPARE_CHANGE_EXECUTION = "benefits_spare_change_execution"
    
    # Savings/Orders
    SAVINGS_PLAN_EXECUTED = "SAVINGS_PLAN_EXECUTED"
    ORDER_EXECUTED = "ORDER_EXECUTED"
    
    # Interest
    INTEREST_PAYOUT = "INTEREST_PAYOUT"

@dataclass
class TransactionAmount:
    value: float
    currency: str
    fraction_digits: int

    @property
    def decimal_value(self) -> float:
        return self.value / (10 ** self.fraction_digits)

@dataclass
class Transaction:
    id: str
    title: str
    subtitle: Optional[str]
    timestamp: str
    event_type: str
    amount: TransactionAmount
    status: str
    icon: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        amount_data = data.get("amount", {})
        amount = TransactionAmount(
            value=amount_data.get("value", 0),
            currency=amount_data.get("currency", "EUR"),
            fraction_digits=amount_data.get("fractionDigits", 2)
        )
        
        return cls(
            id=data.get("id"),
            title=data.get("title", ""),
            subtitle=data.get("subtitle"),
            timestamp=data.get("timestamp", ""),
            event_type=data.get("eventType", ""),
            amount=amount,
            status=data.get("status", ""),
            icon=data.get("icon")
        )

    def is_card_transaction(self) -> bool:
        return self.event_type in [
            EventType.CARD_SUCCESSFUL_TRANSACTION,
            EventType.CARD_REFUND,
            EventType.CARD_FAILED_TRANSACTION
        ]

    def to_csv_row(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "type": self.event_type,
            "title": self.title,
            "subtitle": self.subtitle or "",
            "amount": self.amount.decimal_value,
            "currency": self.amount.currency,
            "status": self.status
        }
