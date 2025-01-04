from polygon import RESTClient
import os
import time
from helpers.options_helpers import fetch_related_companies  
from collections import defaultdict
from datetime import datetime, timedelta
import plotly.graph_objects as go

# Ensure the POLYGON_API_KEY is set as an environment variable
API_KEY = os.getenv("POLYGON_API_KEY")

if not API_KEY:
    raise EnvironmentError("POLYGON_API_KEY environment variable is not set.")

# Initialize the RESTClient
client = RESTClient(API_KEY)


client = RESTClient()  # POLYGON_API_KEY environment variable is used

def fetch_option_volume(ticker, days=20):
    """
    Fetch options volume for the past N days and group by date.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    option_flow = defaultdict(lambda: {"call": 0, "put": 0})

    for option in client.list_options_contracts(ticker):
        for trade in client.list_trades(option.ticker, timestamp_gt=start_date.strftime("%Y-%m-%d")):
            trade_date = datetime.utcfromtimestamp(trade.sip_timestamp / 1_000_000_000).strftime("%Y-%m-%d")
            if option.contract_type.lower() == "call":
                option_flow[trade_date]["call"] += trade.size
            elif option.contract_type.lower() == "put":
                option_flow[trade_date]["put"] += trade.size

    return option_flow



def detect_flow_spikes(option_flow):
    """
    Detect significant spikes in option flows.
    """
    dates = sorted(option_flow.keys())
    historical_call_volumes = [option_flow[date]["call"] for date in dates[:-1]]
    historical_put_volumes = [option_flow[date]["put"] for date in dates[:-1]]

    # Calculate historical averages
    avg_call_volume = sum(historical_call_volumes) / len(historical_call_volumes) if historical_call_volumes else 0
    avg_put_volume = sum(historical_put_volumes) / len(historical_put_volumes) if historical_put_volumes else 0

    # Check for spikes in the latest day
    latest_date = dates[-1]
    latest_call_volume = option_flow[latest_date]["call"]
    latest_put_volume = option_flow[latest_date]["put"]

    print(f"Average Call Volume: {avg_call_volume:.2f}, Latest: {latest_call_volume}")
    print(f"Average Put Volume: {avg_put_volume:.2f}, Latest: {latest_put_volume}")

    call_spike = latest_call_volume > 2 * avg_call_volume
    put_spike = latest_put_volume > 2 * avg_put_volume

    if call_spike or put_spike:
        print(f"Significant option flow spike detected on {latest_date}!")
    else:
        print(f"No significant spikes detected.")

def visualize_option_flows(option_flow, ticker):
    """
    Visualize option flows using Plotly.
    """
    dates = sorted(option_flow.keys())
    call_volumes = [option_flow[date]["call"] for date in dates]
    put_volumes = [option_flow[date]["put"] for date in dates]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=dates, y=call_volumes, name="Call Volume"))
    fig.add_trace(go.Bar(x=dates, y=put_volumes, name="Put Volume"))

    fig.update_layout(
        title=f"{ticker} Option Volume Over Time",
        xaxis_title="Date",
        yaxis_title="Volume",
        barmode="group",
        template="plotly_white"
    )
    fig.show()

def analyze_option_flows(tickers):
    """
    Analyze option flows for a list of tickers.
    """
    for ticker in tickers:
        print(f"Analyzing {ticker}...")
        option_flow = fetch_option_volume(ticker, days=20)
        detect_flow_spikes(option_flow)
        visualize_option_flows(option_flow, ticker)


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
    related_companies = fetch_related_companies(base_ticker, depth=2)
    #related_companies = []
    #related_companies.append(base_ticker)

    for ticker in related_companies:
        print(f"Checking EMA stacking for {ticker}...")
        if is_ema_stacked(ticker):
            print(f"{ticker} has stacked EMAs.")
            stacked_tickers.append(ticker)
        else:
            print(f"{ticker} does not have stacked EMAs.")

    return stacked_tickers

if __name__ == "__main__":
  import argparse

  parser = argparse.ArgumentParser(description="Search stocks for Ree's criteria")
  parser.add_argument("symbol", type=str, help="Stock symbol (e.g., AAPL)")
 
  args = parser.parse_args()
  stacked = find_stacked_tickers(args.symbol)
  analyze_option_flows(stacked)
  print("Tickers with stacked EMAs:", stacked)
