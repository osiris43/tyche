from collections import defaultdict
from datetime import datetime, timedelta
from polygon import RESTClient
import plotly.graph_objects as go
from helpers.options_helpers import get_current_price 

client = RESTClient()  # POLYGON_API_KEY environment variable is used


def visualize_trade_flows(ticker, trades_by_day):
    """
    Visualize the trade flows using Plotly.

    Args:
        trades_by_day (dict): Dictionary with dates as keys and total trade sizes as values.
    """
    # Prepare data for plotting
    sorted_dates = sorted(trades_by_day.keys())
    sizes = [trades_by_day[date] for date in sorted_dates]

    # Create a Plotly bar chart
    fig = go.Figure(data=[
        go.Bar(x=sorted_dates, y=sizes, name="Trade Sizes")
    ])

    # Add layout details
    fig.update_layout(
        title=f"{ticker} Options Trade Flows (Last 20 Days)",
        xaxis_title="Date",
        yaxis_title="Total Trade Size",
        xaxis=dict(tickangle=-45),
        template="plotly_white"
    )

    # Display the chart
    fig.show()


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


def analyze_size_spikes(ticker, trades_by_day):
    """
    Analyze the aggregated trade sizes to detect spikes and visualize flows.

    Args:
        trades_by_day (dict): Dictionary with dates as keys and total trade sizes as values.

    Returns:
        None
    """
    # Sort dates
    sorted_dates = sorted(trades_by_day.keys())

    # Calculate average volume (excluding the latest day)
    historical_sizes = [trades_by_day[date] for date in sorted_dates[:-1]]
    if not historical_sizes:
        print("Not enough historical data for analysis.")
        return

    average_size = sum(historical_sizes) / len(historical_sizes)

    # Get the latest day's size
    latest_day = sorted_dates[-1]
    latest_size = trades_by_day[latest_day]

    print(
        f"Average daily traded size (last {len(historical_sizes)} days): {average_size:.2f}"
    )
    print(f"Total traded size for {latest_day}: {latest_size}")

    # Check for spikes
    if latest_size > 10 * average_size:
        print(
            f"Spike detected! Total size on {latest_day} is more than 10x the average."
        )
    else:
        print(f"No significant spike detected.")

    # Visualize trade flows
    visualize_trade_flows(ticker, trades_by_day)

def visualize_trade_flows_v2(ticker, trades_by_day_by_strike):
    """
    Visualize the trade flows using Plotly.

    Args:
        trades_by_day_by_strike (dict): Dictionary where keys are strikes and values are 
                                        dictionaries with dates as keys and trade sizes as values.
    """
    # Extract all unique dates
    all_dates = sorted({date for strike_data in trades_by_day_by_strike.values() for date in strike_data.keys()})

    # Create a bar for each strike
    data = []
    for strike, trades_by_day in trades_by_day_by_strike.items():
        # Align trade sizes with all dates (fill missing dates with 0)
        sizes = [trades_by_day.get(date, 0) for date in all_dates]
        data.append(go.Bar(x=all_dates, y=sizes, name=f"Strike {strike}"))

    # Create the figure with multiple bars
    fig = go.Figure(data=data)

    # Add layout details
    fig.update_layout(
        title=f"{ticker} Options Trade Flows by Strike (Last 20 Days)",
        xaxis_title="Date",
        yaxis_title="Total Trade Size",
        barmode="group",  # Group bars by date
        xaxis=dict(tickangle=-45),
        template="plotly_white"
    )

    # Display the chart
    fig.show()

def main(underlying, expiration):
    #ticker = generate_option_ticker(underlying, expiration, option_type, strike_price)
    current_price = get_current_price(underlying)   
    print(f"Current Price: {current_price}")
    otm_threshold = current_price * 1.10
    options = client.list_options_contracts(
        underlying, contract_type="call", expiration_date=expiration
    )

    otm_calls = [opt for opt in options if opt.strike_price > otm_threshold]
    print(f"Options Length: {len(otm_calls)}")
    metrics = {}

    for option in otm_calls:
      print(option.ticker)
      trades_by_day = get_trades(option.ticker, days=20)
      metrics[option.strike_price] = trades_by_day
    
    visualize_trade_flows_v2(underlying, metrics)
    #analyze_size_spikes(ticker, trades_by_day)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze options trade size spikes.")
    parser.add_argument("symbol", type=str, help="Stock symbol (e.g., AAPL)")
    parser.add_argument("expiration", type=str, help="Expiration date (YYYY-MM-DD)")

    args = parser.parse_args()
    main(args.symbol, args.expiration)
