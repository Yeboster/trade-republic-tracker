# Trade Republic Portfolio Tracker (WIP)

This project aims to provide a reliable way to fetch and analyze your Trade Republic portfolio and transactions, with a specific focus on **card transactions** (spending analysis).

## Features
- [x] Authentication (Login/OTP)
- [x] WebSocket Subscription (Timeline)
- [x] Card Transactions Filtering (Implemented in `main.py`)
- [x] Data Export (CSV) - Exports `card_transactions.csv`
- [ ] Detailed Spending Analysis (Merchant Categories, Monthly breakdown)

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your credentials:
   ```
   TR_PHONE_NUMBER=+49123456789
   TR_PIN=1234
   ```

3. Run the script:
   ```bash
   python main.py
   ```
   - First run will require OTP (check your phone).
   - Tokens are saved to `tokens.json`.
   - The script will fetch your timeline, filter card transactions, and save them to `card_transactions.csv`.

## Iteration Progress

- **Iteration 1 & 2:** Basic Auth & WebSocket (Done)
- **Iteration 3 (Current):** Transaction History & Card Filtering (Done)
- **Iteration 4:** Data Parsing & CSV Export (Basic Version Done)
- **Iteration 5:** Spending Analysis (Next Step)

## Reference
Inspired by [dhojayev/traderepublic-portfolio-downloader](https://github.com/dhojayev/traderepublic-portfolio-downloader).
