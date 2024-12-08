from collections import defaultdict
from datetime import datetime, timedelta
from polygon import RESTClient
import plotly.graph_objects as go

client = RESTClient()  # POLYGON_API_KEY environment variable is used


def visualize_trade_flows(ticker, trades_by_day):
    """
    Visualize the trade flows using Plotly.
    """
    sorted_dates = sorted(trades_by_day.keys())
    sizes = [trades_by_day[date] for date in sorted_dates]

    fig = go.Figure(data=[
        go.Bar(x=sorted_dates, y=sizes, name="Trade Sizes")
    ])

    fig.update_layout(
        title=f"{ticker} Options Trade Flows (10%+ OTM Calls)",
        xaxis_title="Date",
        yaxis_title="Total Trade Size",
        xaxis=dict(tickangle=-45),
        template="plotly_white"
    )

    fig.show()

def visualize_volume_by_strike(symbol, metrics_by_strike, expiration):
    """
    Visualize raw volume by strike as a bar chart.

    Args:
        symbol (str): Stock ticker.
        metrics_by_strike (dict): Metrics by strike.
    """
    strikes = sorted(metrics_by_strike.keys())
    volumes = [metrics_by_strike[strike]["volume"] for strike in strikes]

    fig = go.Figure(data=[go.Bar(x=strikes, y=volumes, name="Volume")])
    fig.update_layout(
        title=f"{symbol} Volume by Strike {expiration}  (OTM Calls)",
        xaxis_title="Strike Price",
        yaxis_title="Volume",
        template="plotly_white"
    )
    fig.show()

def visualize_trade_flows_by_strike(symbol, trades_by_strike):
    """
    Visualize trade flows by strike using a grouped bar chart.
    
    Args:
        symbol (str): The stock symbol.
        trades_by_strike (dict): Dictionary with strikes as keys and trade data by date.
    """
    # Prepare data for plotting
    strikes = sorted(trades_by_strike.keys())
    dates = sorted({date for strike_data in trades_by_strike.values() for date in strike_data})
    
    # Create traces for each strike
    data = []
    for strike in strikes:
        sizes = [trades_by_strike[strike].get(date, 0) for date in dates]
        data.append(go.Bar(name=f"Strike {strike}", x=dates, y=sizes))
    
    # Create the figure
    fig = go.Figure(data=data)
    fig.update_layout(
        title=f"{symbol} Options Trade Flows by Strike (10%+ OTM Calls)",
        xaxis_title="Date",
        yaxis_title="Total Trade Size",
        barmode="group",
        xaxis=dict(tickangle=-45),
        template="plotly_white"
    )
    fig.show()


def visualize_heatmap(symbol, trades_by_strike):
    """
    Visualize trade flows by strike as a heatmap.
    
    Args:
        symbol (str): The stock symbol.
        trades_by_strike (dict): Dictionary with strikes as keys and trade data by date.
    """
    # Prepare data for heatmap
    strikes = sorted(trades_by_strike.keys())
    dates = sorted({date for strike_data in trades_by_strike.values() for date in strike_data})
    z_data = [[trades_by_strike[strike].get(date, 0) for date in dates] for strike in strikes]
    
    # Create the heatmap
    fig = go.Figure(
        data=go.Heatmap(
            z=z_data,
            x=dates,
            y=strikes,
            colorscale="Viridis",
            colorbar=dict(title="Trade Size"),
        )
    )
    fig.update_layout(
        title=f"{symbol} Options Trade Heatmap (10%+ OTM Calls)",
        xaxis_title="Date",
        yaxis_title="Strike Price",
        template="plotly_white"
    )
    fig.show()


def get_friday_or_date():
    """
    Returns the nearest previous Friday if the given date is a Friday, Saturday, or Sunday.
    Otherwise, returns the given date.

    Args:
        input_date (str): The input date in "YYYY-MM-DD" format.

    Returns:
        str: The resulting date in "YYYY-MM-DD" format.
    """
    # Convert the input string to a datetime object
    date_obj = datetime.now()

    # Get the day of the week (0=Monday, ..., 6=Sunday)
    day_of_week = date_obj.weekday()
    target_date = date_obj

    # Want the last trading day before this one.  S,S,M = F.  This is because
    # my polygon license doesn't allow for day of data.
    if day_of_week in [5,6]:
        # Calculate the number of days to subtract to reach the previous Friday
        days_to_subtract = day_of_week - 4
        target_date = date_obj - timedelta(days=days_to_subtract)
    elif day_of_week == 0:
        days_to_subtract = 3
        target_date = date_obj - timedelta(days=days_to_subtract)
    else:
      days_to_subtract = 1
      target_date = date_obj - timedelta(days=days_to_subtract)
      # Otherwise, return the original date
    
    return target_date.strftime("%Y-%m-%d")


# Helper function for fetching current stock price (pseudo-code)
def get_current_price(ticker):
    """
    Fetch the current stock price for a ticker.
    Replace this with an actual API call or logic.
    """
    d = get_friday_or_date()
    print(d)
    request = client.get_daily_open_close_agg(ticker, d)

    return float(request.close)
                 

def get_trades_and_metrics_for_otm_calls(symbol, expiration, current_price, days=20):
    """
    Fetch trades and metrics (Volume, Open Interest, IV) for all OTM call options.

    Args:
        symbol (str): Stock ticker.
        expiration (str): Expiration date.
        current_price (float): Current stock price.
        days (int): Number of days to look back.

    Returns:
        dict: Metrics including volume, open interest, and IV by strike.
    """
    otm_threshold = current_price #* 1.10
    metrics_by_strike = defaultdict(lambda: {"volume": 0, "open_interest": 0, "iv": 0.0})

    # Fetch options chains for the given expiration
    options = client.list_options_contracts(
        symbol, contract_type="call", expiration_date=expiration
    )

    otm_calls = [opt for opt in options if opt.strike_price > otm_threshold]

    for option in otm_calls:
        try:
            # Fetch additional metrics for the option
            metrics = client.get_snapshot_option(symbol, option.ticker)  # Adjust API call if needed
            strike_data = metrics_by_strike[option.strike_price]

            # Aggregate volume and open interest
            strike_data["volume"] += metrics.day.volume
            strike_data["open_interest"] += metrics.open_interest
            strike_data["iv"] = metrics.implied_volatility

        except Exception as e:
            print(f"Error fetching metrics for {option.ticker}: {e}")

    return metrics_by_strike

def analyze_option_metrics(metrics_by_strike):
    """
    Analyze option metrics to identify notable activity.

    Args:
        metrics_by_strike (dict): Metrics (volume, OI, IV) by strike.

    Returns:
        list: Strikes with significant activity or anomalies.
    """
    anomalies = []

    for strike, metrics in metrics_by_strike.items():
        v_oi_ratio = metrics["volume"] / metrics["open_interest"] if metrics["open_interest"] > 0 else 0
        iv = metrics["iv"] if metrics["iv"] is not None else 0

        print(f"Strike {strike}: Volume={metrics['volume']}, OI={metrics['open_interest']}, IV={iv:.2f}, V/OI Ratio={v_oi_ratio:.2f}")

        # Identify anomalies
        if v_oi_ratio > 1.5:  # High volume relative to open interest
            anomalies.append((strike, v_oi_ratio, iv))

    return anomalies

def visualize_v_oi_ratios(symbol, metrics_by_strike, expiration):
    """
    Visualize Volume to Open Interest Ratios by strike.

    Args:
        symbol (str): Stock ticker.
        metrics_by_strike (dict): Metrics by strike.
    """
    strikes = sorted(metrics_by_strike.keys())
    v_oi_ratios = [
        metrics_by_strike[strike]["volume"] / metrics_by_strike[strike]["open_interest"]
        if metrics_by_strike[strike]["open_interest"] > 0 else 0
        for strike in strikes
    ]

    fig = go.Figure(data=[go.Bar(x=strikes, y=v_oi_ratios, name="V/OI Ratio")])
    fig.update_layout(
        title=f"{symbol} Volume to Open Interest Ratios {expiration} (OTM Calls)",
        xaxis_title="Strike Price",
        yaxis_title="V/OI Ratio",
        template="plotly_white"
    )
    fig.show()

def analyze_size_spikes(symbol, expiration, trades_by_day):
    """
    Analyze trade sizes to detect spikes and visualize flows.
    """
    sorted_dates = sorted(trades_by_day.keys())

    historical_sizes = [trades_by_day[date] for date in sorted_dates[:-1]]
    if not historical_sizes:
        print("Not enough historical data for analysis.")
        return

    average_size = sum(historical_sizes) / len(historical_sizes)

    latest_day = sorted_dates[-1]
    latest_size = trades_by_day[latest_day]

    print(f"Average daily traded size (last {len(historical_sizes)} days): {average_size:.2f}")
    print(f"Total traded size for {latest_day}: {latest_size}")

    if latest_size > 10 * average_size:
        print(f"Spike detected! Total size on {latest_day} is more than 10x the average.")
    else:
        print("No significant spike detected.")

    visualize_trade_flows(symbol, trades_by_day)


def main(symbol, expiration):
    """
    Main function to analyze option-specific metrics for OTM calls.
    """
    current_price = get_current_price(symbol)
    print(f"Current price for {symbol}: {current_price:.2f}")

    metrics_by_strike = get_trades_and_metrics_for_otm_calls(symbol, expiration, current_price, days=20)

    # Analyze metrics
    anomalies = analyze_option_metrics(metrics_by_strike)

    print("\nAnomalies Detected:")
    for strike, v_oi_ratio, iv in anomalies:
        print(f"Strike {strike}: V/OI Ratio={v_oi_ratio:.2f}, IV={iv:.2f}")

    # Visualize metrics
    visualize_v_oi_ratios(symbol, metrics_by_strike, expiration)
    visualize_volume_by_strike(symbol, metrics_by_strike, expiration)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze 10%+ OTM call options trade size spikes.")
    parser.add_argument("symbol", type=str, help="Stock symbol (e.g., AAPL)")
    parser.add_argument("expiration", type=str, help="Expiration date (YYYY-MM-DD)")

    args = parser.parse_args()
    main(args.symbol, args.expiration)
