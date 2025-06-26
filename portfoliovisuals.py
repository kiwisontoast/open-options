# Import required libraries
import tkinter as tk
from tkinter import ttk, messagebox
import sv_ttk  # Sun Valley theme for ttk
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import ctypes


def toggle_theme():
    """
    Switch between light and dark themes for the application interface.
    """
    current_theme = sv_ttk.get_theme()
    if current_theme == "dark":
        sv_ttk.set_theme("light")
        theme_toggle_button.config(text="Switch to Dark Mode")
    else:
        sv_ttk.set_theme("dark")
        theme_toggle_button.config(text="Switch to Light Mode")


def save_portfolio_data(portfolio):
    """
    Save the current portfolio data to a file.
    Format: ticker:shares:purchase_price:purchase_date

    Args:
        portfolio (dict): Dictionary containing stock data
    """
    with open("portfolio.txt", "w") as file:
        for ticker, data in portfolio.items():
            shares = data["shares"]
            purchase_price = data["purchase_price"]
            purchase_date = data["purchase_date"]
            file.write(f"{ticker}:{shares}:{purchase_price}:{purchase_date}\n")


def load_portfolio_data():
    """
    Load portfolio data from a file.

    Returns:
        dict: Dictionary containing stock data with purchase info
    """
    portfolio = {}
    try:
        with open("portfolio.txt", "r") as file:
            for line in file.readlines():
                parts = line.strip().split(":")
                if len(parts) == 4:
                    ticker, shares, purchase_price, purchase_date = parts
                    portfolio[ticker] = {
                        "shares": float(shares),
                        "purchase_price": float(purchase_price),
                        "purchase_date": purchase_date,
                    }
    except FileNotFoundError:
        pass
    return portfolio


def save_covered_calls_data(covered_calls):
    """
    Save covered calls data to a file.
    Format: ticker:exp_date:days_to_exp:strike_price:premium:date_sold

    Args:
        covered_calls (dict): Dictionary containing covered calls data
    """
    with open("coveredcalls.txt", "w") as file:
        for call_id, data in covered_calls.items():
            ticker = data["ticker"]
            exp_date = data["exp_date"]
            days_to_exp = data["days_to_exp"]
            strike_price = data["strike_price"]
            premium = data["premium"]
            date_sold = data["date_sold"]
            file.write(
                f"{ticker}:{exp_date}:{days_to_exp}:{strike_price}:{premium}:{date_sold}\n"
            )


def load_covered_calls_data():
    """
    Load covered calls data from a file.

    Returns:
        dict: Dictionary containing covered calls data
    """
    covered_calls = {}
    try:
        with open("coveredcalls.txt", "r") as file:
            for i, line in enumerate(file.readlines()):
                parts = line.strip().split(":")
                if len(parts) == 6:
                    ticker, exp_date, days_to_exp, strike_price, premium, date_sold = (
                        parts
                    )
                    covered_calls[f"call_{i}"] = {
                        "ticker": ticker,
                        "exp_date": exp_date,
                        "days_to_exp": int(days_to_exp),
                        "strike_price": float(strike_price),
                        "premium": float(premium),
                        "date_sold": date_sold,
                    }
    except FileNotFoundError:
        pass
    return covered_calls


def save_cash_balance(cash):
    """
    Save cash balance to a file.

    Args:
        cash (float): Current cash balance
    """
    with open("cash.txt", "w") as file:
        file.write(str(cash))


def save_dividends_data(dividends):
    """
    Save dividends data to a file.
    Format: ticker:ex_div_date:payment_date:dividend_per_share:status

    Args:
        dividends (dict): Dictionary containing dividends data
    """
    with open("dividends.txt", "w") as file:
        for div_id, data in dividends.items():
            ticker = data["ticker"]
            ex_div_date = data["ex_div_date"]
            payment_date = data["payment_date"]
            dividend_per_share = data["dividend_per_share"]
            status = data["status"]
            file.write(
                f"{ticker}:{ex_div_date}:{payment_date}:{dividend_per_share}:{status}\n"
            )


def load_dividends_data():
    """
    Load dividends data from a file.

    Returns:
        dict: Dictionary containing dividends data
    """
    dividends = {}
    try:
        with open("dividends.txt", "r") as file:
            for i, line in enumerate(file.readlines()):
                parts = line.strip().split(":")
                if len(parts) == 5:
                    ticker, ex_div_date, payment_date, dividend_per_share, status = (
                        parts
                    )
                    dividends[f"div_{i}"] = {
                        "ticker": ticker,
                        "ex_div_date": ex_div_date,
                        "payment_date": payment_date,
                        "dividend_per_share": float(dividend_per_share),
                        "status": status,
                    }
    except FileNotFoundError:
        pass
    return dividends


def load_cash_balance():
    """
    Load cash balance from a file.

    Returns:
        float: Current cash balance
    """
    try:
        with open("cash.txt", "r") as file:
            return float(file.read().strip())
    except FileNotFoundError:
        return 0.0


def get_shares_in_contracts():
    """
    Calculate how many shares of each stock are tied up in covered call contracts.

    Returns:
        dict: Dictionary with ticker as key and number of shares in contracts as value
    """
    shares_in_contracts = {}

    for call_data in covered_calls.values():
        ticker = call_data["ticker"]
        if ticker in shares_in_contracts:
            shares_in_contracts[ticker] += 100
        else:
            shares_in_contracts[ticker] = 100

    return shares_in_contracts


def get_available_shares(ticker):
    """
    Get the number of shares available for trading (not tied up in contracts).

    Args:
        ticker (str): Stock ticker symbol

    Returns:
        float: Number of shares available for trading
    """
    if ticker not in portfolio:
        return 0

    total_shares = portfolio[ticker]["shares"]
    shares_in_contracts = get_shares_in_contracts()
    contracted_shares = shares_in_contracts.get(ticker, 0)

    return max(0, total_shares - contracted_shares)


def check_expired_options():
    """
    Check for expired options and handle them automatically.
    Called when the program starts.
    """
    current_time = datetime.now()
    expiration_time = current_time.replace(
        hour=15, minute=0, second=0, microsecond=0
    )  # 3 PM

    expired_calls = []

    for call_id, call_data in list(covered_calls.items()):
        try:
            exp_date = datetime.strptime(call_data["exp_date"], "%Y-%m-%d")
            exp_datetime = exp_date.replace(hour=15, minute=0, second=0, microsecond=0)

            # Check if option has expired (past 3 PM on expiration date)
            if current_time >= exp_datetime:
                ticker = call_data["ticker"]
                strike_price = call_data["strike_price"]

                # Get current stock price
                current_price = get_current_stock_price(ticker)

                # Check if option is in the money (current price >= strike + 0.01)
                if current_price >= strike_price + 0.01:
                    # Option is exercised - stock is called away
                    if ticker in portfolio and portfolio[ticker]["shares"] >= 100:
                        # Remove 100 shares from portfolio
                        portfolio[ticker]["shares"] -= 100
                        if portfolio[ticker]["shares"] <= 0:
                            del portfolio[ticker]

                        # Add strike price * 100 to cash (from stock sale)
                        global cash_balance
                        cash_balance += strike_price * 100

                        expired_calls.append(
                            f"{ticker} EXERCISED: Stock called away at ${strike_price:.2f}, +${strike_price * 100:.2f} cash"
                        )
                    else:
                        expired_calls.append(
                            f"{ticker} ERROR: Not enough shares for exercise"
                        )
                else:
                    # Option expired worthless
                    expired_calls.append(f"{ticker} EXPIRED: Option expired worthless")

                # Remove the expired option
                del covered_calls[call_id]

        except ValueError:
            # Invalid date format, remove the option
            expired_calls.append(f"Invalid option removed: {call_data}")
            del covered_calls[call_id]

    if expired_calls:
        save_covered_calls_data(covered_calls)
        save_portfolio_data(portfolio)
        save_cash_balance(cash_balance)

        # Show summary of what happened
        message = "Options processed:\n\n" + "\n".join(expired_calls)
        messagebox.showinfo("Options Expiry Processing", message)


def check_dividend_payments():
    """
    Check for dividend payments that should be processed.
    Called when the program starts.
    """
    current_date = datetime.now().date()
    dividend_payments = []

    for div_id, div_data in list(dividends.items()):
        try:
            ex_div_date = datetime.strptime(div_data["ex_div_date"], "%Y-%m-%d").date()
            payment_date = datetime.strptime(
                div_data["payment_date"], "%Y-%m-%d"
            ).date()
            ticker = div_data["ticker"]
            dividend_per_share = div_data["dividend_per_share"]
            status = div_data["status"]

            # Check if payment date has arrived and dividend hasn't been paid yet
            if current_date >= payment_date and status == "pending":
                # Check if we owned shares on ex-dividend date
                if ticker in portfolio:
                    # Get purchase date to see if we owned shares on ex-div date
                    purchase_date = datetime.strptime(
                        portfolio[ticker]["purchase_date"], "%Y-%m-%d"
                    ).date()

                    # Must have purchased before ex-dividend date
                    if purchase_date < ex_div_date:
                        # Calculate dividend payment
                        shares_owned = portfolio[ticker]["shares"]
                        total_dividend = shares_owned * dividend_per_share

                        # Add dividend to cash
                        global cash_balance
                        cash_balance += total_dividend

                        # Mark dividend as paid
                        dividends[div_id]["status"] = "paid"

                        dividend_payments.append(
                            f"{ticker}: ${total_dividend:.2f} dividend received ({shares_owned:.0f} shares × ${dividend_per_share:.2f})"
                        )
                    else:
                        # Mark as ineligible
                        dividends[div_id]["status"] = "ineligible"
                        dividend_payments.append(
                            f"{ticker}: Not eligible - purchased after ex-dividend date"
                        )
                else:
                    # Mark as ineligible (no shares)
                    dividends[div_id]["status"] = "ineligible"
                    dividend_payments.append(
                        f"{ticker}: Not eligible - no shares owned"
                    )

        except ValueError:
            # Invalid date format, remove the dividend
            dividend_payments.append(f"Invalid dividend removed: {div_data}")
            del dividends[div_id]

    if dividend_payments:
        save_dividends_data(dividends)
        save_cash_balance(cash_balance)

        # Show summary of dividend payments
        message = "Dividend payments processed:\n\n" + "\n".join(dividend_payments)
        messagebox.showinfo("Dividend Processing", message)


def get_current_stock_price(ticker):
    """
    Get current stock price for a ticker.

    Args:
        ticker (str): Stock ticker symbol

    Returns:
        float: Current stock price
    """
    try:
        data = yf.Ticker(ticker).history(period="1d")
        return data["Close"].iloc[-1]
    except:
        return 0.0


def fetch_upcoming_dividends():
    """
    Automatically fetch upcoming dividends for stocks in portfolio using yfinance.
    Called when the program starts.
    """
    new_dividends_found = []

    for ticker in portfolio.keys():
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Get dividend information
            ex_div_date = info.get("exDividendDate")
            dividend_rate = info.get("dividendRate")  # Annual dividend rate
            dividend_yield = info.get("dividendYield")

            # If we have ex-dividend date and annual rate, calculate quarterly dividend
            if ex_div_date and dividend_rate:
                # Convert timestamp to date if needed
                if isinstance(ex_div_date, (int, float)):
                    ex_div_date = datetime.fromtimestamp(ex_div_date).date()
                elif isinstance(ex_div_date, str):
                    ex_div_date = datetime.strptime(ex_div_date, "%Y-%m-%d").date()

                # Calculate quarterly dividend (most common)
                quarterly_dividend = dividend_rate / 4

                # Estimate payment date (typically 2-3 weeks after ex-div date)
                payment_date = ex_div_date + timedelta(days=21)

                # Check if this dividend is already tracked
                already_tracked = False
                for div_data in dividends.values():
                    if div_data["ticker"] == ticker and div_data[
                        "ex_div_date"
                    ] == ex_div_date.strftime("%Y-%m-%d"):
                        already_tracked = True
                        break

                # Add new dividend if not already tracked
                if not already_tracked and ex_div_date >= datetime.now().date():
                    div_id = f"div_{len(dividends)}"
                    dividends[div_id] = {
                        "ticker": ticker,
                        "ex_div_date": ex_div_date.strftime("%Y-%m-%d"),
                        "payment_date": payment_date.strftime("%Y-%m-%d"),
                        "dividend_per_share": quarterly_dividend,
                        "status": "pending",
                    }
                    new_dividends_found.append(
                        f"{ticker}: ${quarterly_dividend:.2f} on {ex_div_date}"
                    )

        except Exception as e:
            # Skip stocks that can't be fetched
            continue

    # Save new dividends if any were found
    if new_dividends_found:
        save_dividends_data(dividends)
        message = "New dividends detected:\n\n" + "\n".join(new_dividends_found)
        messagebox.showinfo("Automatic Dividend Detection", message, parent=root)


def check_historical_dividends():
    """
    Check for historical dividends that may have been missed while program was closed.
    This runs on startup to catch any dividends that occurred while the program wasn't running.
    """
    historical_payments = []
    current_date = datetime.now().date()

    for ticker in portfolio.keys():
        try:
            stock = yf.Ticker(ticker)
            # Get dividend history for the last 6 months
            start_date = current_date - timedelta(days=180)
            dividends_history = stock.dividends

            if not dividends_history.empty:
                # Filter to recent dividends
                recent_dividends = dividends_history[
                    dividends_history.index.date >= start_date
                ]

                for div_date, div_amount in recent_dividends.items():
                    div_date = div_date.date()

                    # Check if we owned the stock before this dividend
                    purchase_date = datetime.strptime(
                        portfolio[ticker]["purchase_date"], "%Y-%m-%d"
                    ).date()

                    # If we owned the stock before the dividend date and it's in the past
                    if purchase_date < div_date and div_date <= current_date:

                        # Check if this dividend is already tracked
                        already_tracked = False
                        for div_data in dividends.values():
                            if (
                                div_data["ticker"] == ticker
                                and abs(
                                    (
                                        datetime.strptime(
                                            div_data["ex_div_date"], "%Y-%m-%d"
                                        ).date()
                                        - div_date
                                    ).days
                                )
                                <= 5
                            ):
                                already_tracked = True
                                break

                        # If not tracked, add it as a completed dividend
                        if not already_tracked:
                            # Estimate ex-dividend date (usually a few days before payment)
                            ex_div_date = div_date - timedelta(days=3)

                            # Calculate total dividend payment
                            shares_owned = portfolio[ticker]["shares"]
                            total_dividend = shares_owned * div_amount

                            # Add to cash balance
                            global cash_balance
                            cash_balance += total_dividend

                            # Add to dividend tracking as "paid"
                            div_id = f"div_{len(dividends)}"
                            dividends[div_id] = {
                                "ticker": ticker,
                                "ex_div_date": ex_div_date.strftime("%Y-%m-%d"),
                                "payment_date": div_date.strftime("%Y-%m-%d"),
                                "dividend_per_share": float(div_amount),
                                "status": "paid",
                            }

                            historical_payments.append(
                                f"{ticker}: ${total_dividend:.2f} dividend credited ({shares_owned:.0f} shares × ${div_amount:.2f})"
                            )

        except Exception as e:
            # Skip stocks that can't be fetched
            continue

    # Save changes if any historical dividends were found
    if historical_payments:
        save_dividends_data(dividends)
        save_cash_balance(cash_balance)
        message = "Historical dividends credited:\n\n" + "\n".join(historical_payments)
        messagebox.showinfo("Historical Dividend Processing", message, parent=root)


def calculate_portfolio_value():
    """
    Calculate total portfolio value including stocks, cash, and covered calls.

    Returns:
        tuple: (total_value, stock_value, cash_value, options_value, portfolio_breakdown, shares_in_contracts)
    """
    stock_value = 0
    portfolio_breakdown = {}
    shares_in_contracts = get_shares_in_contracts()

    for ticker, data in portfolio.items():
        current_price = get_current_stock_price(ticker)
        shares = data["shares"]
        purchase_price = data["purchase_price"]
        current_value = shares * current_price
        gain_loss = current_value - (shares * purchase_price)
        gain_loss_percent = (
            (gain_loss / (shares * purchase_price)) * 100 if purchase_price > 0 else 0
        )

        # Calculate available vs contracted shares
        available_shares = get_available_shares(ticker)
        contracted_shares = shares_in_contracts.get(ticker, 0)

        portfolio_breakdown[ticker] = {
            "shares": shares,
            "available_shares": available_shares,
            "contracted_shares": contracted_shares,
            "purchase_price": purchase_price,
            "current_price": current_price,
            "current_value": current_value,
            "available_value": available_shares * current_price,
            "contracted_value": contracted_shares * current_price,
            "gain_loss": gain_loss,
            "gain_loss_percent": gain_loss_percent,
            "purchase_date": data["purchase_date"],
        }
        stock_value += current_value

    # Calculate options value (current premium value)
    options_value = 0
    for call_data in covered_calls.values():
        # For simplicity, we'll use the original premium as current value
        # In a real application, you'd fetch current option prices
        options_value += call_data["premium"] * 100

    total_value = stock_value + cash_balance

    return (
        total_value,
        stock_value,
        cash_balance,
        options_value,
        portfolio_breakdown,
        shares_in_contracts,
    )


def update_portfolio_display():
    """
    Update the portfolio display with current values and statistics.
    """
    (
        total_value,
        stock_value,
        cash_value,
        options_value,
        breakdown,
        shares_in_contracts,
    ) = calculate_portfolio_value()

    # Calculate available vs contracted values
    available_stock_value = sum(data["available_value"] for data in breakdown.values())
    contracted_stock_value = sum(
        data["contracted_value"] for data in breakdown.values()
    )

    # Update total values
    total_value_label.config(text=f"Total Portfolio Value: ${total_value:.2f}")
    stock_value_label.config(
        text=f"Stock Value (Available): ${available_stock_value:.2f}"
    )
    contracted_value_label.config(
        text=f"Stock Value (In Contracts): ${contracted_stock_value:.2f}"
    )
    cash_value_label.config(text=f"Cash: ${cash_value:.2f}")
    options_value_label.config(text=f"Options Value: ${options_value:.2f}")

    # Clear and update portfolio listbox
    portfolio_listbox.delete(0, tk.END)
    for ticker, data in breakdown.items():
        gain_loss_text = (
            f"+${data['gain_loss']:.2f}"
            if data["gain_loss"] >= 0
            else f"-${abs(data['gain_loss']):.2f}"
        )
        percent_text = f"({data['gain_loss_percent']:+.2f}%)"

        if data["contracted_shares"] > 0:
            portfolio_listbox.insert(
                tk.END,
                f"{ticker}: {data['available_shares']:.0f} available + {data['contracted_shares']:.0f} contracted "
                f"@ ${data['current_price']:.2f} | Total: ${data['current_value']:.2f} | {gain_loss_text} {percent_text}",
            )
        else:
            portfolio_listbox.insert(
                tk.END,
                f"{ticker}: {data['shares']:.0f} shares @ ${data['current_price']:.2f} | "
                f"Value: ${data['current_value']:.2f} | {gain_loss_text} {percent_text}",
            )

    # Update covered calls listbox
    covered_calls_listbox.delete(0, tk.END)
    for call_id, call_data in covered_calls.items():
        # Calculate days remaining
        try:
            exp_date = datetime.strptime(call_data["exp_date"], "%Y-%m-%d")
            days_remaining = (exp_date - datetime.now()).days
        except:
            days_remaining = call_data["days_to_exp"]

        covered_calls_listbox.insert(
            tk.END,
            f"{call_data['ticker']} | Strike: ${call_data['strike_price']:.2f} | "
            f"Premium: ${call_data['premium']:.2f} | Days: {days_remaining} | "
            f"Exp: {call_data['exp_date']}",
        )

    # Update dividends listbox
    dividends_listbox.delete(0, tk.END)
    for div_id, div_data in dividends.items():
        # Calculate days to payment
        try:
            payment_date = datetime.strptime(div_data["payment_date"], "%Y-%m-%d")
            days_to_payment = (payment_date - datetime.now()).days
        except:
            days_to_payment = 0

        # Color code by status
        status_text = div_data["status"].upper()
        if div_data["status"] == "paid":
            status_color = "✓"
        elif div_data["status"] == "pending":
            status_color = "⏳"
        else:
            status_color = "✗"

        dividends_listbox.insert(
            tk.END,
            f"{div_data['ticker']} | ${div_data['dividend_per_share']:.2f}/share | "
            f"Ex: {div_data['ex_div_date']} | Pay: {div_data['payment_date']} | "
            f"Days: {days_to_payment} | {status_color} {status_text}",
        )


def add_stock_to_portfolio():
    """
    Add a stock to the portfolio with purchase details.
    Requires sufficient cash balance for the purchase.
    """
    try:
        ticker = ticker_entry.get().upper()
        shares = float(shares_entry.get())
        purchase_price = float(purchase_price_entry.get())
        purchase_date = purchase_date_entry.get()

        if not ticker or shares <= 0 or purchase_price <= 0:
            messagebox.showerror("Error", "Please enter valid values")
            return

        # Calculate total cost of purchase
        total_cost = shares * purchase_price

        # Check if we have sufficient cash
        global cash_balance
        if total_cost > cash_balance:
            messagebox.showerror(
                "Insufficient Funds",
                f"Purchase cost: ${total_cost:.2f}\n"
                f"Available cash: ${cash_balance:.2f}\n"
                f"Need ${total_cost - cash_balance:.2f} more cash",
            )
            return

        # Validate date format
        try:
            datetime.strptime(purchase_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Date must be in YYYY-MM-DD format")
            return

        # Deduct cost from cash balance
        cash_balance -= total_cost
        save_cash_balance(cash_balance)

        if ticker in portfolio:
            # Update existing position (average cost)
            existing_shares = portfolio[ticker]["shares"]
            existing_cost = portfolio[ticker]["purchase_price"] * existing_shares
            new_cost = purchase_price * shares
            total_shares = existing_shares + shares
            avg_price = (existing_cost + new_cost) / total_shares

            portfolio[ticker]["shares"] = total_shares
            portfolio[ticker]["purchase_price"] = avg_price
        else:
            portfolio[ticker] = {
                "shares": shares,
                "purchase_price": purchase_price,
                "purchase_date": purchase_date,
            }

        save_portfolio_data(portfolio)
        update_portfolio_display()

        # Clear entries
        ticker_entry.delete(0, tk.END)
        shares_entry.delete(0, tk.END)
        purchase_price_entry.delete(0, tk.END)
        purchase_date_entry.delete(0, tk.END)

        messagebox.showinfo(
            "Purchase Successful",
            f"Purchased {shares} shares of {ticker} at ${purchase_price:.2f} each.\n"
            f"Total cost: ${total_cost:.2f}\n"
            f"Remaining cash: ${cash_balance:.2f}",
        )

    except ValueError:
        messagebox.showerror("Error", "Please enter valid numeric values")


def remove_stock_from_portfolio():
    """
    Remove shares from the portfolio and add proceeds to cash.
    Only allows selling available shares (not in contracts).
    """
    try:
        ticker = ticker_entry.get().upper()
        shares_to_remove = float(shares_entry.get())

        if ticker not in portfolio:
            messagebox.showerror("Error", f"{ticker} not found in portfolio")
            return

        # Check available shares (not in contracts)
        available_shares = get_available_shares(ticker)
        if shares_to_remove > available_shares:
            contracted_shares = get_shares_in_contracts().get(ticker, 0)
            messagebox.showerror(
                "Error",
                f"You have {portfolio[ticker]['shares']:.0f} total shares of {ticker}\n"
                f"Available for sale: {available_shares:.0f} shares\n"
                f"In contracts: {contracted_shares:.0f} shares\n"
                f"Cannot sell {shares_to_remove:.0f} shares",
            )
            return

        # Get current market price for the sale
        current_price = get_current_stock_price(ticker)
        if current_price == 0:
            messagebox.showerror("Error", f"Could not get current price for {ticker}")
            return

        # Calculate proceeds from sale
        sale_proceeds = shares_to_remove * current_price

        # Add proceeds to cash balance
        global cash_balance
        cash_balance += sale_proceeds
        save_cash_balance(cash_balance)

        # Remove shares from portfolio
        if shares_to_remove >= portfolio[ticker]["shares"]:
            del portfolio[ticker]
        else:
            portfolio[ticker]["shares"] -= shares_to_remove

        save_portfolio_data(portfolio)
        update_portfolio_display()

        # Clear entries
        ticker_entry.delete(0, tk.END)
        shares_entry.delete(0, tk.END)

        messagebox.showinfo(
            "Stock Sold",
            f"Sold {shares_to_remove} shares of {ticker} at ${current_price:.2f} each.\n"
            f"Proceeds: ${sale_proceeds:.2f} added to cash balance.",
        )

    except ValueError:
        messagebox.showerror("Error", "Please enter valid numeric values")


def add_covered_call():
    """
    Add a covered call position.
    """
    try:
        ticker = cc_ticker_entry.get().upper()
        exp_date = cc_exp_date_entry.get()
        strike_price = float(cc_strike_entry.get())
        premium = float(cc_premium_entry.get())

        if not ticker or strike_price <= 0 or premium <= 0:
            messagebox.showerror("Error", "Please enter valid values")
            return

        # Check if we have at least 100 available shares (not in contracts)
        available_shares = get_available_shares(ticker)
        if available_shares < 100:
            total_shares = portfolio.get(ticker, {}).get("shares", 0)
            contracted_shares = get_shares_in_contracts().get(ticker, 0)
            messagebox.showerror(
                "Error",
                f"Need at least 100 available shares of {ticker} for covered call\n"
                f"Total shares: {total_shares:.0f}\n"
                f"Available: {available_shares:.0f}\n"
                f"In contracts: {contracted_shares:.0f}",
            )
            return

        # Validate date format
        try:
            exp_datetime = datetime.strptime(exp_date, "%Y-%m-%d")
            days_to_exp = (exp_datetime - datetime.now()).days
        except ValueError:
            messagebox.showerror("Error", "Date must be in YYYY-MM-DD format")
            return

        # Add cash from premium (premium * 100 shares)
        global cash_balance
        cash_balance += premium * 100
        save_cash_balance(cash_balance)

        # Create covered call entry
        call_id = f"call_{len(covered_calls)}"
        covered_calls[call_id] = {
            "ticker": ticker,
            "exp_date": exp_date,
            "days_to_exp": days_to_exp,
            "strike_price": strike_price,
            "premium": premium,
            "date_sold": datetime.now().strftime("%Y-%m-%d"),
        }

        save_covered_calls_data(covered_calls)
        update_portfolio_display()

        # Clear entries
        cc_ticker_entry.delete(0, tk.END)
        cc_exp_date_entry.delete(0, tk.END)
        cc_strike_entry.delete(0, tk.END)
        cc_premium_entry.delete(0, tk.END)

        messagebox.showinfo(
            "Success", f"Covered call added! ${premium * 100:.2f} added to cash balance"
        )

    except ValueError:
        messagebox.showerror("Error", "Please enter valid numeric values")


def manual_call_away():
    """
    Manually call away stock for a selected covered call.
    """
    selection = covered_calls_listbox.curselection()
    if not selection:
        messagebox.showerror("Error", "Please select a covered call to exercise")
        return

    index = selection[0]
    call_id = list(covered_calls.keys())[index]
    call_data = covered_calls[call_id]

    ticker = call_data["ticker"]
    strike_price = call_data["strike_price"]

    # Check if we have the shares
    if ticker not in portfolio or portfolio[ticker]["shares"] < 100:
        messagebox.showerror("Error", f"Not enough shares of {ticker} in portfolio")
        return

    # Remove 100 shares from portfolio
    portfolio[ticker]["shares"] -= 100
    if portfolio[ticker]["shares"] <= 0:
        del portfolio[ticker]

    # Add strike price * 100 to cash (from stock sale)
    global cash_balance
    cash_balance += strike_price * 100

    # Remove the covered call
    del covered_calls[call_id]

    save_covered_calls_data(covered_calls)
    save_portfolio_data(portfolio)
    save_cash_balance(cash_balance)
    update_portfolio_display()

    messagebox.showinfo(
        "Stock Called Away",
        f"{ticker} called away at ${strike_price:.2f} per share\n"
        f"Received: ${strike_price * 100:.2f}",
    )


def remove_covered_call():
    """
    Remove a covered call (when closed or expired).
    """
    selection = covered_calls_listbox.curselection()
    if not selection:
        messagebox.showerror("Error", "Please select a covered call to remove")
        return

    index = selection[0]
    call_id = list(covered_calls.keys())[index]
    del covered_calls[call_id]

    save_covered_calls_data(covered_calls)
    update_portfolio_display()


def add_dividend():
    """
    Add a dividend tracking entry.
    """
    try:
        ticker = div_ticker_entry.get().upper()
        ex_div_date = div_ex_date_entry.get()
        payment_date = div_payment_date_entry.get()
        dividend_per_share = float(div_amount_entry.get())

        if not ticker or dividend_per_share <= 0:
            messagebox.showerror("Error", "Please enter valid values")
            return

        # Validate date formats
        try:
            datetime.strptime(ex_div_date, "%Y-%m-%d")
            datetime.strptime(payment_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Dates must be in YYYY-MM-DD format")
            return

        # Check that payment date is after ex-dividend date
        ex_date_obj = datetime.strptime(ex_div_date, "%Y-%m-%d")
        pay_date_obj = datetime.strptime(payment_date, "%Y-%m-%d")

        if pay_date_obj <= ex_date_obj:
            messagebox.showerror("Error", "Payment date must be after ex-dividend date")
            return

        # Create dividend entry
        div_id = f"div_{len(dividends)}"
        dividends[div_id] = {
            "ticker": ticker,
            "ex_div_date": ex_div_date,
            "payment_date": payment_date,
            "dividend_per_share": dividend_per_share,
            "status": "pending",
        }

        save_dividends_data(dividends)
        update_portfolio_display()

        # Clear entries
        div_ticker_entry.delete(0, tk.END)
        div_ex_date_entry.delete(0, tk.END)
        div_payment_date_entry.delete(0, tk.END)
        div_amount_entry.delete(0, tk.END)

        messagebox.showinfo("Success", f"Dividend tracking added for {ticker}")

    except ValueError:
        messagebox.showerror("Error", "Please enter valid numeric values")


def remove_dividend():
    """
    Remove a selected dividend entry.
    """
    selection = dividends_listbox.curselection()
    if not selection:
        messagebox.showerror("Error", "Please select a dividend to remove")
        return

    index = selection[0]
    div_id = list(dividends.keys())[index]
    del dividends[div_id]

    save_dividends_data(dividends)
    update_portfolio_display()


def add_cash():
    """
    Add cash to the account.
    """
    try:
        amount = float(cash_entry.get())
        if amount <= 0:
            messagebox.showerror("Error", "Please enter a positive amount")
            return

        global cash_balance
        cash_balance += amount
        save_cash_balance(cash_balance)
        update_portfolio_display()

        cash_entry.delete(0, tk.END)

    except ValueError:
        messagebox.showerror("Error", "Please enter a valid amount")


def remove_cash():
    """
    Remove cash from the account.
    """
    try:
        amount = float(cash_entry.get())
        if amount <= 0:
            messagebox.showerror("Error", "Please enter a positive amount")
            return

        global cash_balance
        if amount > cash_balance:
            messagebox.showerror("Error", "Insufficient cash balance")
            return

        cash_balance -= amount
        save_cash_balance(cash_balance)
        update_portfolio_display()

        cash_entry.delete(0, tk.END)

    except ValueError:
        messagebox.showerror("Error", "Please enter a valid amount")


# Initialize main window and configure basic settings
root = tk.Tk()
root.title("Portfolio and Options Tracker")
root.protocol("WM_DELETE_WINDOW", lambda: root.quit())

# Configure window behavior
root.resizable(True, True)

# Windows-specific configuration to remove maximize button
if root.tk.call("tk", "windowingsystem") == "win32":
    root.state("normal")
    hwnd = root.winfo_id()
    style = ctypes.windll.user32.GetWindowLongW(hwnd, -16)
    style = style & ~0x10000  # Remove WS_MAXIMIZEBOX
    ctypes.windll.user32.SetWindowLongW(hwnd, -16, style)

# Set initial window size
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
window_width = int(screen_width * 0.9)
window_height = int(screen_height * 0.8)
root.geometry(f"{window_width}x{window_height}")

# Configure main frame
main_frame = ttk.Frame(root)
main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

# Configure root grid weights
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)
main_frame.grid_rowconfigure(1, weight=1)
main_frame.grid_columnconfigure(1, weight=1)

# Create theme toggle button
theme_toggle_button = ttk.Button(
    main_frame, text="Switch to Light Mode", command=toggle_theme
)
theme_toggle_button.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)

# Create left control panel
control_frame = ttk.Frame(main_frame)
control_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))

# Create right display panel
display_frame = ttk.Frame(main_frame)
display_frame.grid(row=1, column=1, sticky="nsew")
display_frame.grid_rowconfigure(1, weight=1)
display_frame.grid_rowconfigure(3, weight=1)
display_frame.grid_columnconfigure(0, weight=1)

# Portfolio section
portfolio_label = ttk.Label(
    control_frame, text="Portfolio Management", font=("Arial", 10, "bold")
)
portfolio_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))

ttk.Label(control_frame, text="Stock Ticker:", font=("Arial", 8)).grid(
    row=1, column=0, sticky=tk.W, pady=1
)
ticker_entry = ttk.Entry(control_frame, width=8, font=("Arial", 8))
ticker_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=1)

ttk.Label(control_frame, text="Shares:", font=("Arial", 8)).grid(
    row=2, column=0, sticky=tk.W, pady=1
)
shares_entry = ttk.Entry(control_frame, width=8, font=("Arial", 8))
shares_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=1)

ttk.Label(control_frame, text="Purchase Price:", font=("Arial", 8)).grid(
    row=3, column=0, sticky=tk.W, pady=1
)
purchase_price_entry = ttk.Entry(control_frame, width=8, font=("Arial", 8))
purchase_price_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=1)

ttk.Label(control_frame, text="Date (YYYY-MM-DD):", font=("Arial", 8)).grid(
    row=4, column=0, sticky=tk.W, pady=1
)
purchase_date_entry = ttk.Entry(control_frame, width=8, font=("Arial", 8))
purchase_date_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=1)

ttk.Button(control_frame, text="Add Stock", command=add_stock_to_portfolio).grid(
    row=5, column=0, pady=3
)
ttk.Button(
    control_frame, text="Remove Stock", command=remove_stock_from_portfolio
).grid(row=5, column=1, pady=3)

# Separator
ttk.Separator(control_frame, orient="horizontal").grid(
    row=6, column=0, columnspan=2, sticky="ew", pady=5
)

# Covered Calls section
cc_label = ttk.Label(control_frame, text="Covered Calls", font=("Arial", 10, "bold"))
cc_label.grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))

ttk.Label(control_frame, text="Stock Ticker:", font=("Arial", 8)).grid(
    row=8, column=0, sticky=tk.W, pady=1
)
cc_ticker_entry = ttk.Entry(control_frame, width=8, font=("Arial", 8))
cc_ticker_entry.grid(row=8, column=1, sticky=(tk.W, tk.E), pady=1)

ttk.Label(control_frame, text="Exp Date (YYYY-MM-DD):", font=("Arial", 8)).grid(
    row=9, column=0, sticky=tk.W, pady=1
)
cc_exp_date_entry = ttk.Entry(control_frame, width=8, font=("Arial", 8))
cc_exp_date_entry.grid(row=9, column=1, sticky=(tk.W, tk.E), pady=1)

ttk.Label(control_frame, text="Strike Price:", font=("Arial", 8)).grid(
    row=10, column=0, sticky=tk.W, pady=1
)
cc_strike_entry = ttk.Entry(control_frame, width=8, font=("Arial", 8))
cc_strike_entry.grid(row=10, column=1, sticky=(tk.W, tk.E), pady=1)

ttk.Label(control_frame, text="Premium per Share:", font=("Arial", 8)).grid(
    row=11, column=0, sticky=tk.W, pady=1
)
cc_premium_entry = ttk.Entry(control_frame, width=8, font=("Arial", 8))
cc_premium_entry.grid(row=11, column=1, sticky=(tk.W, tk.E), pady=1)

ttk.Button(control_frame, text="Add Covered Call", command=add_covered_call).grid(
    row=12, column=0, pady=3
)
ttk.Button(control_frame, text="Remove Selected", command=remove_covered_call).grid(
    row=12, column=1, pady=3
)
ttk.Button(control_frame, text="Call Away (Exercise)", command=manual_call_away).grid(
    row=13, column=0, columnspan=2, pady=3
)

# Separator
ttk.Separator(control_frame, orient="horizontal").grid(
    row=14, column=0, columnspan=2, sticky="ew", pady=5
)

# Dividends section
div_label = ttk.Label(
    control_frame, text="Dividend Tracking", font=("Arial", 10, "bold")
)
div_label.grid(row=15, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))

ttk.Label(control_frame, text="Stock Ticker:", font=("Arial", 8)).grid(
    row=16, column=0, sticky=tk.W, pady=1
)
div_ticker_entry = ttk.Entry(control_frame, width=8, font=("Arial", 8))
div_ticker_entry.grid(row=16, column=1, sticky=(tk.W, tk.E), pady=1)

ttk.Label(control_frame, text="Ex-Div Date (YYYY-MM-DD):", font=("Arial", 8)).grid(
    row=17, column=0, sticky=tk.W, pady=1
)
div_ex_date_entry = ttk.Entry(control_frame, width=8, font=("Arial", 8))
div_ex_date_entry.grid(row=17, column=1, sticky=(tk.W, tk.E), pady=1)

ttk.Label(control_frame, text="Payment Date (YYYY-MM-DD):", font=("Arial", 8)).grid(
    row=18, column=0, sticky=tk.W, pady=1
)
div_payment_date_entry = ttk.Entry(control_frame, width=8, font=("Arial", 8))
div_payment_date_entry.grid(row=18, column=1, sticky=(tk.W, tk.E), pady=1)

ttk.Label(control_frame, text="Dividend per Share:", font=("Arial", 8)).grid(
    row=19, column=0, sticky=tk.W, pady=1
)
div_amount_entry = ttk.Entry(control_frame, width=8, font=("Arial", 8))
div_amount_entry.grid(row=19, column=1, sticky=(tk.W, tk.E), pady=1)

ttk.Button(control_frame, text="Add Dividend", command=add_dividend).grid(
    row=20, column=0, pady=3
)
ttk.Button(control_frame, text="Remove Selected", command=remove_dividend).grid(
    row=20, column=1, pady=3
)

# Separator
ttk.Separator(control_frame, orient="horizontal").grid(
    row=21, column=0, columnspan=2, sticky="ew", pady=5
)

# Cash Management section
cash_label = ttk.Label(
    control_frame, text="Cash Management", font=("Arial", 10, "bold")
)
cash_label.grid(row=22, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))

ttk.Label(control_frame, text="Amount:", font=("Arial", 8)).grid(
    row=23, column=0, sticky=tk.W, pady=1
)
cash_entry = ttk.Entry(control_frame, width=8, font=("Arial", 8))
cash_entry.grid(row=23, column=1, sticky=(tk.W, tk.E), pady=1)

ttk.Button(control_frame, text="Add Cash", command=add_cash).grid(
    row=24, column=0, pady=3
)
ttk.Button(control_frame, text="Remove Cash", command=remove_cash).grid(
    row=24, column=1, pady=3
)

# Configure control frame grid
control_frame.grid_columnconfigure(1, weight=1)

# Display section - Portfolio Values
values_frame = ttk.LabelFrame(display_frame, text="Portfolio Summary", padding=5)
values_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))

total_value_label = ttk.Label(
    values_frame, text="Total Portfolio Value: $0.00", font=("Arial", 10, "bold")
)
total_value_label.grid(row=0, column=0, sticky=tk.W)

stock_value_label = ttk.Label(
    values_frame, text="Stock Value: $0.00", font=("Arial", 9)
)
stock_value_label.grid(row=1, column=0, sticky=tk.W)

cash_value_label = ttk.Label(values_frame, text="Cash: $0.00", font=("Arial", 9))
cash_value_label.grid(row=2, column=0, sticky=tk.W)

contracted_value_label = ttk.Label(
    values_frame, text="Stock Value (In Contracts): $0.00", font=("Arial", 9)
)
contracted_value_label.grid(row=3, column=0, sticky=tk.W)

options_value_label = ttk.Label(
    values_frame, text="Options Value: $0.00", font=("Arial", 9)
)
options_value_label.grid(row=4, column=0, sticky=tk.W)

# Display section - Portfolio Holdings
portfolio_frame = ttk.LabelFrame(display_frame, text="Portfolio Holdings", padding=5)
portfolio_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 5))
portfolio_frame.grid_rowconfigure(0, weight=1)
portfolio_frame.grid_columnconfigure(0, weight=1)

portfolio_listbox = tk.Listbox(portfolio_frame, font=("Courier", 8))
portfolio_listbox.grid(row=0, column=0, sticky="nsew")

portfolio_scrollbar = ttk.Scrollbar(
    portfolio_frame, orient="vertical", command=portfolio_listbox.yview
)
portfolio_scrollbar.grid(row=0, column=1, sticky="ns")
portfolio_listbox.configure(yscrollcommand=portfolio_scrollbar.set)

# Display section - Covered Calls
calls_frame = ttk.LabelFrame(display_frame, text="Covered Calls", padding=5)
calls_frame.grid(row=2, column=0, sticky="ew", pady=(0, 5))

covered_calls_listbox = tk.Listbox(calls_frame, font=("Courier", 8), height=4)
covered_calls_listbox.grid(row=0, column=0, sticky="ew")

calls_scrollbar = ttk.Scrollbar(
    calls_frame, orient="vertical", command=covered_calls_listbox.yview
)
calls_scrollbar.grid(row=0, column=1, sticky="ns")
covered_calls_listbox.configure(yscrollcommand=calls_scrollbar.set)
calls_frame.grid_columnconfigure(0, weight=1)

# Display section - Dividends
dividends_frame = ttk.LabelFrame(display_frame, text="Dividend Tracking", padding=5)
dividends_frame.grid(row=3, column=0, sticky="ew", pady=(0, 5))

dividends_listbox = tk.Listbox(dividends_frame, font=("Courier", 8), height=4)
dividends_listbox.grid(row=0, column=0, sticky="ew")

dividends_scrollbar = ttk.Scrollbar(
    dividends_frame, orient="vertical", command=dividends_listbox.yview
)
dividends_scrollbar.grid(row=0, column=1, sticky="ns")
dividends_listbox.configure(yscrollcommand=dividends_scrollbar.set)
dividends_frame.grid_columnconfigure(0, weight=1)

# Set theme
sv_ttk.set_theme("dark")

# Load data
portfolio = load_portfolio_data()
covered_calls = load_covered_calls_data()
dividends = load_dividends_data()
cash_balance = load_cash_balance()

# Check for expired options, historical dividends, upcoming dividends, and current dividend payments on startup
check_expired_options()
check_historical_dividends()
fetch_upcoming_dividends()
check_dividend_payments()

# Initial display update
update_portfolio_display()

# Start the main event loop
root.mainloop()
