from polygon import RESTClient
import os
from datetime import datetime, timedelta
from collections import defaultdict
import plotly.graph_objects as g

# Ensure the POLYGON_API_KEY is set as an environment variable
API_KEY = os.getenv("POLYGON_API_KEY")

if not API_KEY:
    raise EnvironmentError("POLYGON_API_KEY environment variable is not set.")

# Initialize the RESTClient
client = RESTClient(API_KEY)

def generate_option_ticker(underlying, expiration, option_type, strike_price):
    """
    Generate an options ticker in the format used by Polygon.io.
    """
    expiration_formatted = expiration[2:].replace("-", "")
    strike_price_formatted = f"{int(strike_price * 1000):08d}"
    return f"O:{underlying.upper()}{expiration_formatted}{option_type.upper()}{strike_price_formatted}"

def get_trades(ticker, days=20):
    """
    Fetch trades for the past N days and aggregate their sizes by date.

    Args:
        ticker (str): The option ticker.
        days (int): Number of days to look back.

    Returns:
        dict: A dictionary with dates as keys and total trade size as values.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    trades_by_day = defaultdict(int)

    # Fetch trades from Polygon
    for t in client.list_trades(ticker, timestamp_gt=start_date.strftime("%Y-%m-%d")):
        # Convert SIP timestamp to a date
        trade_date = datetime.utcfromtimestamp(
            t.sip_timestamp / 1_000_000_000
        ).strftime("%Y-%m-%d")
        trades_by_day[trade_date] += t.size  # Aggregate trade size

    return trades_by_day

# Utility Functions
def get_ticker_details(ticker):
    """
    Fetch details for a specific ticker.
    Args:
        ticker (str): Stock ticker (e.g., "AAPL").
    Returns:
        dict: Details about the ticker.
    """
    try:
        details = client.get_ticker_details(ticker)
        return details
    except Exception as e:
        print(f"Error fetching details for {ticker}: {e}")


def list_trades(ticker, days=1):
    """
    Fetch trades for a specific ticker from the last `days` days.
    Args:
        ticker (str): Options ticker (e.g., "O:AAPL240119C00150000").
        days (int): Number of days of trades to fetch.
    Returns:
        list: A list of trades.
    """
    from datetime import datetime, timedelta

    start_date = datetime.now() - timedelta(days=days)
    start_date_str = start_date.strftime("%Y-%m-%d")

    try:
        trades = client.list_trades(ticker, timestamp_gt=start_date_str)
        return list(trades)
    except Exception as e:
        print(f"Error fetching trades for {ticker}: {e}")


def get_aggregates(
    ticker, multiplier=1, timespan="day", from_date="2023-01-01", to_date="2023-12-31"
):
    """
    Fetch aggregate data for a ticker.
    Args:
        ticker (str): Stock ticker (e.g., "AAPL").
        multiplier (int): Size of the time window.
        timespan (str): One of "minute", "hour", "day", "week", "month", or "quarter".
        from_date (str): Start date (YYYY-MM-DD).
        to_date (str): End date (YYYY-MM-DD).
    Returns:
        list: Aggregate data points.
    """
    try:
        aggregates = client.get_aggs(ticker, multiplier, timespan, from_date, to_date)
        return list(aggregates)
    except Exception as e:
        print(f"Error fetching aggregates for {ticker}: {e}")


def list_tickers(limit=10):
    """
    Fetch a list of tickers.
    Args:
        limit (int): Maximum number of tickers to fetch.
    Returns:
        list: A list of tickers.
    """
    try:
        tickers = client.list_tickers(limit=limit)
        return list(tickers)
    except Exception as e:
        print(f"Error fetching tickers: {e}")


def get_client():
    return client

def get_date_from_sip(sip):
  trade_date = datetime.utcfromtimestamp(sip / 1000).strftime("%Y-%m-%d")
  print(trade_date)
  
# Display a welcome message
def welcome_message():
    print(
        """
Welcome to the Polygon API Explorer!
------------------------------------
Available utilities:
1. `get_ticker_details(ticker)`: Fetch details for a specific stock ticker.
2. `list_trades(ticker, days=1)`: Fetch recent trades for a ticker.
3. `get_aggregates(ticker, multiplier=1, timespan="day", from_date, to_date)`: Fetch aggregate data for a ticker.
4. `list_tickers(limit=10)`: Fetch a list of tickers.
5. `generate_option_ticker(underlying, expiration, option_type, strike_price)
Polygon Client is initialized as `client`.

Example:
>>> list_tickers()
>>> get_ticker_details("AAPL")
"""
    )


# Display the welcome message when the script is loaded
welcome_message()
