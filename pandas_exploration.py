from polygon import RESTClient
import pandas as pd
import os
from datetime import datetime, timedelta
import plotly.express as px
from helpers.options_helpers import generate_option_ticker

# Ensure the POLYGON_API_KEY is set as an environment variable
API_KEY = os.getenv("POLYGON_API_KEY")

if not API_KEY:
    raise EnvironmentError("POLYGON_API_KEY environment variable is not set.")

# Initialize the RESTClient
client = RESTClient(API_KEY)

def get_trades_as_dataframe(ticker, strike, days=20):
    """
    Fetch trades for the past N days and return as a DataFrame.

    Args:
        ticker (str): The option ticker.
        days (int): Number of days to look back.

    Returns:
        pd.DataFrame: A DataFrame containing all trade data.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Fetch trades from Polygon
    trades = []
    for t in client.list_trades(ticker, timestamp_gt=start_date.strftime("%Y-%m-%d")):
        trades.append({
            "trade_date": datetime.utcfromtimestamp(t.sip_timestamp / 1_000_000_000).strftime("%Y-%m-%d"),
            "price": t.price,
            "size": t.size,
            "strike_price": strike 
        })

    # Convert to DataFrame
    df_trades = pd.DataFrame(trades)
    return df_trades

def visualize_trades(df):
    """
    Visualize trades with Plotly.

    Args:
        df (pd.DataFrame): DataFrame containing trades data.

    Returns:
        None
    """
    if df.empty:
        print("No trades found for visualization.")
        return

    # Create scatter plot with Plotly
    fig = px.scatter(
        df,
        x="trade_date",
        y="strike_price",
        size="size",
        color="price",
        title="Options Trades Visualization",
        labels={"trade_date": "Date", "strike_price": "Strike Price", "size": "Trade Size", "price": "Trade Price"}
    )
    fig.update_traces(marker=dict(opacity=0.7), selector=dict(mode='markers'))
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Strike Price",
        legend_title="Price",
    )
    fig.show()

def main(underlying, expiration, option_type, strike_price):
    ticker = generate_option_ticker(underlying, expiration, option_type, strike_price)
    trades_by_day = get_trades_as_dataframe(ticker, strike_price, days=20)
    print(trades_by_day)

    # Visualize trades
    visualize_trades(trades_by_day)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze options trade size spikes.")
    parser.add_argument("symbol", type=str, help="Stock symbol (e.g., AAPL)")
    parser.add_argument("option_type", type=str, help="Option type (call, put)")
    parser.add_argument("expiration", type=str, help="Expiration date (YYYY-MM-DD)")
    parser.add_argument("strike", type=float, help="Strike price")

    args = parser.parse_args()
    main(args.symbol, args.expiration, args.option_type, args.strike)
