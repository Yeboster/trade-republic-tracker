# Trade Republic Tracker

A Python-based tool to track Trade Republic portfolio and transactions, with a focus on **Card Spending Analysis**.

## Status
**Current Iteration:** 3 (Transaction Fetching)
**Goal:** Replace the need for manual CSV exports by directly accessing the API.

## Features
- [x] **Authentication**: Login with Phone + PIN + 2FA (SMS).
- [x] **WebSocket Client**: Connects to Trade Republic's real-time API.
- [x] **Timeline Fetching**: Retrieves transaction history.
- [x] **Card Analysis**: Filters for card transactions (Spending).

## Usage

### Prerequisites
- Python 3.8+
- `pip install -r requirements.txt`

### Running
1. **First Login (Interactive):**
   ```bash
   python main.py --phone "+49123456789" --pin "1234"
   ```
   You will be prompted for the SMS OTP.
   After successful login, the **Session Token** will be printed.

2. **Subsequent Runs (Cached Session):**
   ```bash
   python main.py --session "<YOUR_SESSION_TOKEN>"
   ```

## Findings & API Notes

### Authentication
- **Endpoint**: `https://api.traderepublic.com/api/v1/auth/web/login`
- **Flow**:
  1. POST `login` (Phone, PIN) -> Returns `processId`.
  2. POST `login/<processId>/<OTP>` -> Returns `tr_session` and `tr_refresh` cookies.

### WebSocket Protocol
- **Endpoint**: `wss://api.traderepublic.com/`
- **Connect**: Sends `connect 33 {"locale": "en", ...}`
- **Subscribe**: Sends `sub <id> {"type": "timelineTransactions", "token": "...", "after": "<cursor>"}`
- **Response**: `<id> <state> <payload>` (e.g., `1 A {...}`)
  - `A`: Data payload (Action?)
  - `C`: Continue?
  - `E`: Error

### Transaction Data
- **Card Transactions** are identified by `eventType`:
  - `card_successful_transaction`
  - `card_failed_transaction`
  - `card_refund`
- **Payload** includes:
  - `title`: Merchant Name (e.g., "Rewe")
  - `amount.value`: Amount
  - `timestamp`: Date/Time

## Next Steps
- [ ] **Iteration 4**: CSV Export with Merchant Category Parsing.
- [ ] **Iteration 5**: Spending Analytics (Monthly totals, etc.).
- [ ] **Security**: Securely store tokens (keyring?).
