from collections import defaultdict
from datetime import datetime, timedelta
from polygon import RESTClient

client = RESTClient()  # POLYGON_API_KEY environment variable is used


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


def analyze_size_spikes(trades_by_day):
    """
    Analyze the aggregated trade sizes to detect spikes.

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


def main(underlying, expiration, option_type, strike_price):
    ticker = generate_option_ticker(underlying, expiration, option_type, strike_price)
    trades_by_day = get_trades(ticker, days=20)
    analyze_size_spikes(trades_by_day)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze options trade size spikes.")
    parser.add_argument("symbol", type=str, help="Stock symbol (e.g., AAPL)")
    parser.add_argument("option_type", type=str, help="Option type (call, put)")
    parser.add_argument("expiration", type=str, help="Expiration date (YYYY-MM-DD)")
    parser.add_argument("strike", type=float, help="Strike price")

    args = parser.parse_args()
    main(args.symbol, args.expiration, args.option_type, args.strike)
