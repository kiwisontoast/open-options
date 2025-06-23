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


def calculate_portfolio_value():
    """
    Calculate total portfolio value including stocks, cash, and covered calls.

    Returns:
        tuple: (total_value, stock_value, cash_value, options_value, portfolio_breakdown)
    """
    stock_value = 0
    portfolio_breakdown = {}

    for ticker, data in portfolio.items():
        current_price = get_current_stock_price(ticker)
        shares = data["shares"]
        purchase_price = data["purchase_price"]
        current_value = shares * current_price
        gain_loss = current_value - (shares * purchase_price)
        gain_loss_percent = (
            (gain_loss / (shares * purchase_price)) * 100 if purchase_price > 0 else 0
        )

        portfolio_breakdown[ticker] = {
            "shares": shares,
            "purchase_price": purchase_price,
            "current_price": current_price,
            "current_value": current_value,
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

    total_value = stock_value + cash_balance + options_value

    return total_value, stock_value, cash_balance, options_value, portfolio_breakdown


def update_portfolio_display():
    """
    Update the portfolio display with current values and statistics.
    """
    total_value, stock_value, cash_value, options_value, breakdown = (
        calculate_portfolio_value()
    )

    # Update total values
    total_value_label.config(text=f"Total Portfolio Value: ${total_value:.2f}")
    stock_value_label.config(text=f"Stock Value: ${stock_value:.2f}")
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


def add_stock_to_portfolio():
    """
    Add a stock to the portfolio with purchase details.
    """
    try:
        ticker = ticker_entry.get().upper()
        shares = float(shares_entry.get())
        purchase_price = float(purchase_price_entry.get())
        purchase_date = purchase_date_entry.get()

        if not ticker or shares <= 0 or purchase_price <= 0:
            messagebox.showerror("Error", "Please enter valid values")
            return

        # Validate date format
        try:
            datetime.strptime(purchase_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Date must be in YYYY-MM-DD format")
            return

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

    except ValueError:
        messagebox.showerror("Error", "Please enter valid numeric values")


def remove_stock_from_portfolio():
    """
    Remove shares from the portfolio.
    """
    try:
        ticker = ticker_entry.get().upper()
        shares_to_remove = float(shares_entry.get())

        if ticker not in portfolio:
            messagebox.showerror("Error", f"{ticker} not found in portfolio")
            return

        if shares_to_remove >= portfolio[ticker]["shares"]:
            del portfolio[ticker]
        else:
            portfolio[ticker]["shares"] -= shares_to_remove

        save_portfolio_data(portfolio)
        update_portfolio_display()

        # Clear entries
        ticker_entry.delete(0, tk.END)
        shares_entry.delete(0, tk.END)

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

        # Check if we have at least 100 shares
        if ticker not in portfolio or portfolio[ticker]["shares"] < 100:
            messagebox.showerror(
                "Error", f"Need at least 100 shares of {ticker} for covered call"
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
    control_frame, text="Portfolio Management", font=("Arial", 12, "bold")
)
portfolio_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

ttk.Label(control_frame, text="Stock Ticker:").grid(
    row=1, column=0, sticky=tk.W, pady=2
)
ticker_entry = ttk.Entry(control_frame, width=10)
ticker_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)

ttk.Label(control_frame, text="Shares:").grid(row=2, column=0, sticky=tk.W, pady=2)
shares_entry = ttk.Entry(control_frame, width=10)
shares_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)

ttk.Label(control_frame, text="Purchase Price:").grid(
    row=3, column=0, sticky=tk.W, pady=2
)
purchase_price_entry = ttk.Entry(control_frame, width=10)
purchase_price_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2)

ttk.Label(control_frame, text="Date (YYYY-MM-DD):").grid(
    row=4, column=0, sticky=tk.W, pady=2
)
purchase_date_entry = ttk.Entry(control_frame, width=10)
purchase_date_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=2)

ttk.Button(control_frame, text="Add Stock", command=add_stock_to_portfolio).grid(
    row=5, column=0, pady=5
)
ttk.Button(
    control_frame, text="Remove Stock", command=remove_stock_from_portfolio
).grid(row=5, column=1, pady=5)

# Separator
ttk.Separator(control_frame, orient="horizontal").grid(
    row=6, column=0, columnspan=2, sticky="ew", pady=10
)

# Covered Calls section
cc_label = ttk.Label(control_frame, text="Covered Calls", font=("Arial", 12, "bold"))
cc_label.grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

ttk.Label(control_frame, text="Stock Ticker:").grid(
    row=8, column=0, sticky=tk.W, pady=2
)
cc_ticker_entry = ttk.Entry(control_frame, width=10)
cc_ticker_entry.grid(row=8, column=1, sticky=(tk.W, tk.E), pady=2)

ttk.Label(control_frame, text="Exp Date (YYYY-MM-DD):").grid(
    row=9, column=0, sticky=tk.W, pady=2
)
cc_exp_date_entry = ttk.Entry(control_frame, width=10)
cc_exp_date_entry.grid(row=9, column=1, sticky=(tk.W, tk.E), pady=2)

ttk.Label(control_frame, text="Strike Price:").grid(
    row=10, column=0, sticky=tk.W, pady=2
)
cc_strike_entry = ttk.Entry(control_frame, width=10)
cc_strike_entry.grid(row=10, column=1, sticky=(tk.W, tk.E), pady=2)

ttk.Label(control_frame, text="Premium per Share:").grid(
    row=11, column=0, sticky=tk.W, pady=2
)
cc_premium_entry = ttk.Entry(control_frame, width=10)
cc_premium_entry.grid(row=11, column=1, sticky=(tk.W, tk.E), pady=2)

ttk.Button(control_frame, text="Add Covered Call", command=add_covered_call).grid(
    row=12, column=0, pady=5
)
ttk.Button(control_frame, text="Remove Selected", command=remove_covered_call).grid(
    row=12, column=1, pady=5
)

# Separator
ttk.Separator(control_frame, orient="horizontal").grid(
    row=13, column=0, columnspan=2, sticky="ew", pady=10
)

# Cash Management section
cash_label = ttk.Label(
    control_frame, text="Cash Management", font=("Arial", 12, "bold")
)
cash_label.grid(row=14, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

ttk.Label(control_frame, text="Amount:").grid(row=15, column=0, sticky=tk.W, pady=2)
cash_entry = ttk.Entry(control_frame, width=10)
cash_entry.grid(row=15, column=1, sticky=(tk.W, tk.E), pady=2)

ttk.Button(control_frame, text="Add Cash", command=add_cash).grid(
    row=16, column=0, pady=5
)
ttk.Button(control_frame, text="Remove Cash", command=remove_cash).grid(
    row=16, column=1, pady=5
)

# Configure control frame grid
control_frame.grid_columnconfigure(1, weight=1)

# Display section - Portfolio Values
values_frame = ttk.LabelFrame(display_frame, text="Portfolio Summary", padding=10)
values_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

total_value_label = ttk.Label(
    values_frame, text="Total Portfolio Value: $0.00", font=("Arial", 12, "bold")
)
total_value_label.grid(row=0, column=0, sticky=tk.W)

stock_value_label = ttk.Label(values_frame, text="Stock Value: $0.00")
stock_value_label.grid(row=1, column=0, sticky=tk.W)

cash_value_label = ttk.Label(values_frame, text="Cash: $0.00")
cash_value_label.grid(row=2, column=0, sticky=tk.W)

options_value_label = ttk.Label(values_frame, text="Options Value: $0.00")
options_value_label.grid(row=3, column=0, sticky=tk.W)

# Display section - Portfolio Holdings
portfolio_frame = ttk.LabelFrame(display_frame, text="Portfolio Holdings", padding=10)
portfolio_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
portfolio_frame.grid_rowconfigure(0, weight=1)
portfolio_frame.grid_columnconfigure(0, weight=1)

portfolio_listbox = tk.Listbox(portfolio_frame, font=("Courier", 10))
portfolio_listbox.grid(row=0, column=0, sticky="nsew")

portfolio_scrollbar = ttk.Scrollbar(
    portfolio_frame, orient="vertical", command=portfolio_listbox.yview
)
portfolio_scrollbar.grid(row=0, column=1, sticky="ns")
portfolio_listbox.configure(yscrollcommand=portfolio_scrollbar.set)

# Display section - Covered Calls
calls_frame = ttk.LabelFrame(display_frame, text="Covered Calls", padding=10)
calls_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))

covered_calls_listbox = tk.Listbox(calls_frame, font=("Courier", 10), height=6)
covered_calls_listbox.grid(row=0, column=0, sticky="ew")

calls_scrollbar = ttk.Scrollbar(
    calls_frame, orient="vertical", command=covered_calls_listbox.yview
)
calls_scrollbar.grid(row=0, column=1, sticky="ns")
covered_calls_listbox.configure(yscrollcommand=calls_scrollbar.set)
calls_frame.grid_columnconfigure(0, weight=1)

# Set theme
sv_ttk.set_theme("dark")

# Load data
portfolio = load_portfolio_data()
covered_calls = load_covered_calls_data()
cash_balance = load_cash_balance()

# Initial display update
update_portfolio_display()

# Start the main event loop
root.mainloop()
