# Portfolio and Options Tracker

A comprehensive Python desktop application for tracking stock portfolios and covered call options. Built with Tkinter and featuring real-time market data integration, this tool provides accurate portfolio valuation and sophisticated options management for retail investors.

## Summary

This application simulates a realistic brokerage account experience, complete with cash management, stock trading restrictions, and automatic options handling. It tracks your investments with real-time market prices, manages covered call positions, and automatically processes option expirations and exercises. The tool enforces realistic trading rules, such as requiring sufficient cash for purchases and preventing the sale of shares tied up in options contracts.

## Features

### 📈 **Portfolio Management**
- **Real-time stock tracking** with live market prices via Yahoo Finance
- **Purchase history** with dates and cost basis tracking
- **Gain/Loss calculation** showing both dollar amounts and percentages
- **Average cost basis** calculation for multiple purchases of the same stock

### 💰 **Cash Management**
- **Realistic cash requirements** - must have sufficient funds before buying stocks
- **Automatic cash flow** - selling stocks adds proceeds to cash balance
- **Manual cash management** - add deposits or track withdrawals
- **Complete transaction tracking** with automatic deductions and credits

### 📊 **Options Trading (Covered Calls)**
- **100-share requirement validation** for covered call creation
- **Premium collection** - automatically adds option premiums to cash balance
- **Contract expiration tracking** with countdown timers
- **Automatic exercise handling** at 3 PM on expiration date
- **Manual exercise capability** with "Call Away" functionality
- **In-the-money detection** - automatically exercises if stock price ≥ strike + $0.01

### 🔒 **Trading Restrictions**
- **Share segregation** - clearly separates available shares from those in contracts
- **Prevents overselling** - cannot sell shares tied up in covered calls
- **Contract tracking** - shows which shares are committed to options
- **Realistic limitations** - mimics actual brokerage account restrictions

### 🎨 **User Interface**
- **Modern dark/light theme** toggle using Sun Valley TTK theme
- **Organized layout** with separate sections for stocks, options, cash, and dividends
- **Real-time updates** - portfolio values update automatically
- **Detailed displays** - comprehensive information for all positions
- **Error handling** - clear messages for invalid operations

### 💾 **Data Persistence**
- **Automatic saving** - all data saved to local text files
- **Multiple data files** - separate files for portfolio, options, cash, and dividends
- **Session persistence** - data survives between application restarts
- **Simple file format** - easy to backup or manually edit if needed

## Installation

### Prerequisites
```bash
pip install tkinter yfinance sv-ttk matplotlib numpy
```

### Download
```bash
git clone https://github.com/yourusername/portfolio-options-tracker.git
cd portfolio-options-tracker
python portfolio_tracker.py
```

## How to Use

### 🚀 **Getting Started**

1. **Launch the application**
   ```bash
   python portfolio_tracker.py
   ```

2. **Add initial cash** (required before buying stocks)
   - Enter amount in the "Cash Management" section
   - Click "Add Cash"

3. **Start building your portfolio**

### 📈 **Managing Your Stock Portfolio**

#### **Buying Stocks**
1. **Enter stock details:**
   - **Stock Ticker**: Enter the symbol (e.g., AAPL, MSFT)
   - **Shares**: Number of shares to purchase
   - **Purchase Price**: Price per share you paid
   - **Date**: Purchase date in YYYY-MM-DD format

2. **Click "Buy Stock"**
   - Application verifies sufficient cash balance
   - Deducts purchase amount from cash
   - Adds shares to your portfolio

#### **Selling Stocks**
1. **Enter ticker and share amount** to sell
2. **Click "Sell Stock"**
   - Sells at current market price
   - Adds proceeds to cash balance
   - Only allows selling available (non-contracted) shares

### 📊 **Trading Covered Calls**

#### **Creating Covered Calls**
1. **Ensure you have 100+ available shares** of the target stock
2. **Enter covered call details:**
   - **Stock Ticker**: Must match a stock you own
   - **Exp Date**: Expiration date (YYYY-MM-DD)
   - **Strike Price**: The strike price for your call
   - **Premium per Share**: Premium you received

3. **Click "Add Covered Call"**
   - Validates you have sufficient available shares
   - Adds premium × 100 to your cash balance
   - Locks 100 shares in the contract

#### **Managing Active Calls**
- **View all positions** in the "Covered Calls" section
- **Days remaining** automatically calculated
- **Manual exercise** using "Call Away (Exercise)" button
- **Automatic processing** on expiration day

### 💎 **Intelligent Dividend Management**
- **Automatic dividend detection** - scans for announced dividends on portfolio stocks
- **Historical dividend recovery** - credits missed dividends from the past 6 months
- **Smart eligibility verification** - only credits dividends if stock was owned before ex-dividend date
- **Real-time dividend processing** - automatically pays dividends on payment date
- **Manual dividend tracking** - option to add custom dividend entries
- **Complete dividend lifecycle** - from announcement to payment with status tracking

### 💰 **Understanding Your Portfolio Value**

#### **Portfolio Summary Shows:**
- **Total Portfolio Value**: Complete account value (stocks + cash)
- **Stock Value (Available)**: Shares you can freely trade
- **Stock Value (In Contracts)**: Shares tied up in covered calls
- **Cash**: Available buying power
- **Options Value**: Current value of your option positions (for reference only)

#### **Portfolio Holdings Display:**
```
AAPL: 50 available + 100 contracted @ $150.25 | Total: $22,537.50 | +$2,537.50 (+12.73%)
MSFT: 75 shares @ $280.40 | Value: $21,030.00 | +$1,030.00 (+5.15%)
```

#### **Dividend Tracking Display:**
```
AAPL | $0.25/share | Ex: 2024-08-09 | Pay: 2024-08-16 | Days: 12 | ⏳ PENDING
MSFT | $0.30/share | Ex: 2024-05-15 | Pay: 2024-05-22 | Days: -30 | ✓ PAID
```

### ⚙️ **Automatic Features**

#### **Option Expiration (Runs at startup)**
- **Checks all positions** for expiration at 3 PM on expiration date
- **Auto-exercise if ITM**: Stock called away if price ≥ strike + $0.01
- **Expire worthless**: Option simply removed if out-of-the-money
- **Cash handling**: Strike price × 100 added if exercised

#### **Dividend Processing (Runs at startup)**
- **Historical Recovery**: Scans past 6 months for missed dividends and credits them
- **Announcement Detection**: Automatically detects new dividend announcements
- **Eligibility Verification**: Only credits dividends if stock was owned before ex-dividend date
- **Payment Processing**: Automatically processes payments on scheduled dates

#### **Real-time Updates**
- **Market prices** updated when viewing portfolio
- **Gain/loss calculations** reflect current market values
- **Days to expiration** countdown automatically
- **Dividend status** updates automatically

### 📁 **Data Files**

The application creates four data files in the same directory:

- **`portfolio.txt`**: Stock holdings with purchase details
- **`coveredcalls.txt`**: Active covered call positions
- **`dividends.txt`**: Dividend tracking and history
- **`cash.txt`**: Current cash balance

**Backup recommendation**: Regularly backup these files to preserve your data.

### 🎨 **Customization**

- **Theme Toggle**: Switch between dark and light modes using the theme button
- **Window Resizing**: Application window can be resized vertically
- **Manual Data Editing**: Data files use simple text format for manual editing if needed

### ❗ **Important Notes**

- **Internet required**: Application needs internet connection for real-time stock prices and dividend data
- **Market hours**: Stock prices update during market hours
- **Date format**: Always use YYYY-MM-DD format for dates
- **Share requirements**: Need exactly 100+ available shares for each covered call
- **Cash requirements**: Must have sufficient cash before any stock purchase
- **Automatic processing**: Dividend detection and option expiration handling occurs on program startup

### 🔧 **Troubleshooting**

**Cannot buy stocks**: Ensure you have sufficient cash balance
**Cannot create covered call**: Verify you have 100+ available (non-contracted) shares
**Price not updating**: Check internet connection and verify ticker symbol
**Option not expiring**: Ensure system date/time is correct
**Dividends not detected**: Check internet connection; some dividend data may be delayed
**Missing historical dividends**: Manually add using dividend tracking section if automatic detection fails

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is open source and available under the [MIT License](LICENSE).

---

**Disclaimer**: This tool is for educational and personal portfolio tracking purposes only. Not intended as financial advice. Always consult with financial professionals for investment decisions.
