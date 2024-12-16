from polygon import RESTClient
import os
import time
from helpers.options_helpers import fetch_related_companies  

# Ensure the POLYGON_API_KEY is set as an environment variable
API_KEY = os.getenv("POLYGON_API_KEY")

if not API_KEY:
    raise EnvironmentError("POLYGON_API_KEY environment variable is not set.")

# Initialize the RESTClient
client = RESTClient(API_KEY)

def is_ema_stacked(ticker):
    """
    Check if a ticker's EMAs are stacked in descending order.
    
    Args:
        ticker (str): Stock ticker.

    Returns:
        bool: True if EMAs are stacked, False otherwise.
    """
    ema_windows = [8, 21, 34, 55, 89]
    ema_values = []

    for window in ema_windows:
        ema = client.get_ema(
            ticker=ticker,
            timespan="day",
            window=window,
            series_type="close",
            limit=1
        )
        # Extract the most recent EMA value
        if ema:
            latest_ema = ema.values[0].value
            ema_values.append(latest_ema)
        else:
            # If EMA data is missing, assume it's not stacked
            return False
        time.sleep(5) 

        # Guard clause: Check if EMAs are not stacked
        if len(ema_values) > 1 and ema_values[-2] <= ema_values[-1]:
            return False

    return True

def find_stacked_tickers(base_ticker):
    """
    Find related tickers with EMAs stacked in descending order.
    
    Args:
        base_ticker (str): The base stock ticker.

    Returns:
        list: Tickers with stacked EMAs.
    """
    stacked_tickers = []

    # Fetch related companies
    related_companies = fetch_related_companies(base_ticker, depth=1)
    #related_companies = []
    #related_companies.append(base_ticker)

    for ticker in related_companies:
        print(f"Checking EMA stacking for {ticker}...")
        if is_ema_stacked(ticker):
            print(f"{ticker} has stacked EMAs.")
            stacked_tickers.append(ticker)
        else:
            print(f"{ticker} does not have stacked EMAs.")

        time.sleep(5)

    return stacked_tickers

if __name__ == "__main__":
  import argparse

  parser = argparse.ArgumentParser(description="Search stocks for Ree's criteria")
  parser.add_argument("symbol", type=str, help="Stock symbol (e.g., AAPL)")
 
  args = parser.parse_args()
  stacked = find_stacked_tickers(args.symbol)
  print("Tickers with stacked EMAs:", stacked)
