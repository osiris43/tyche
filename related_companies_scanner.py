from collections import defaultdict
from datetime import datetime, timedelta
from polygon import RESTClient
import time

from related_companies_db import initialize_db, save_related_companies, get_related_companies_from_db

client = RESTClient()  # Ensure POLYGON_API_KEY is set in your environment


def generate_option_ticker(underlying, expiration, option_type, strike_price):
    """
    Generate an options ticker in the format used by Polygon.io.
    """
    expiration_formatted = expiration[2:].replace("-", "")
    strike_price_formatted = f"{int(strike_price * 1000):08d}"
    return f"O:{underlying.upper()}{expiration_formatted}{option_type.upper()}{strike_price_formatted}"


def fetch_related_companies(ticker, depth=3, seen=None, use_db=False):
    """
    Recursively fetch related companies up to the specified depth.

    Args:
        ticker (str): Initial stock ticker (e.g., "LNG").
        depth (int): Maximum recursion depth.
        seen (set): Set of already-seen tickers to avoid duplicates.
        use_db (bool): Whether to check the database for related companies.

    Returns:
        set: A set of related tickers.
    """
    if seen is None:
        seen = set()

    seen.add(ticker)
    # Base case: Stop recursion if depth is 0
    if depth == 0:
        return seen

    if use_db:
        # Check the database first
        related_tickers = get_related_companies_from_db(ticker)
        if related_tickers:
            print(f"Found {len(related_tickers)} related tickers for {ticker} in the database.")
            seen.update(related_tickers)
            return seen

    # Otherwise, hit the API (handle the case where API is down or empty response)
    try:
        related_companies = client.get_related_companies(ticker)
        related_tickers = [related.ticker for related in related_companies]  # Adjust if structure differs

        print(f"Fetched {len(related_tickers)} related tickers for {ticker} from the API.")
        save_related_companies(ticker, related_tickers)  # Save to the database
        seen.update(related_tickers)

        # Recurse for each related ticker
        for related_ticker in related_tickers:
            if related_ticker not in seen:
                fetch_related_companies(related_ticker, depth - 1, seen, use_db)

        return seen

    except Exception as e:
        print(f"Error fetching related companies for {ticker}: {e}")
        return seen

def get_trades(option_ticker):
    """
    Fetch trades for a single option ticker and aggregate by date.
    """
    trades_by_day = defaultdict(int)
    try:
        # Fetch trades from Polygon
        for t in client.list_trades(option_ticker):
            trade_date = datetime.utcfromtimestamp(
                t.sip_timestamp / 1_000_000_000
            ).strftime("%Y-%m-%d")
            trades_by_day[trade_date] += t.size
    except Exception as e:
        print(f"Error fetching trades for {option_ticker}: {e}")

    return trades_by_day


def analyze_size_spikes(trades_by_day):
    """
    Analyze the aggregated trade sizes to detect spikes.
    """
    # Sort dates
    sorted_dates = sorted(trades_by_day.keys())

    if len(sorted_dates) < 2:
        print("Not enough historical data for analysis.")
        return

    # Calculate average volume (excluding the latest day)
    historical_sizes = [trades_by_day[date] for date in sorted_dates[:-1]]
    average_size = sum(historical_sizes) / len(historical_sizes)

    # Get the latest day's size
    latest_day = sorted_dates[-1]
    latest_size = trades_by_day[latest_day]

    # Check for spikes
    if latest_size > 10 * average_size:
        print(
            f"Average daily traded size (last {len(historical_sizes)} days): {average_size:.2f}"
        )
        print(f"Total traded size for {latest_day}: {latest_size}")
        print(
            f"Spike detected! Total size on {latest_day} is more than 10x the average."
        )

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
    request = client.get_daily_open_close_agg(ticker, get_friday_or_date())

    return float(request.close)


def get_otm_calls(ticker, expiration_limit_days=180):
    """
    Fetch all OTM call options for a given ticker within a specified expiration limit.

    Args:
        ticker (str): The stock ticker (e.g., "KMI").
        expiration_limit_days (int): The maximum number of days from today for expiration.

    Returns:
        list: A list of OTM call option tickers.
    """
    expiration_limit_date = datetime.now() + timedelta(days=expiration_limit_days)

    try:
        # Fetch the current stock price
        current_price = get_current_price(ticker)
        print(f"Current price for {ticker}: {current_price}")

        # Fetch the options chain for the ticker
        options = client.list_options_contracts(ticker)

        otm_calls = []

        # Filter for OTM call options within the expiration limit
        for option in options:
            option_expiration_date = datetime.strptime(option.expiration_date, "%Y-%m-%d")
            if (
                option.contract_type == "call"
                and option.strike_price > current_price
                and option_expiration_date <= expiration_limit_date
            ):
                otm_calls.append(option.ticker)  # Use the full option ticker

        print(f"Found {len(otm_calls)} OTM calls for {ticker} within {expiration_limit_days} days.")
        return otm_calls

    except Exception as e:
        print(f"Error fetching OTM calls for {ticker}: {e}")
        return []


def run_scanner_on_otm_calls(base_ticker, depth=3, expiration_limit_days=180):
    """
    Run the scanner on OTM call options for related tickers.

    Args:
        base_ticker (str): The initial stock ticker.
        expiration (str): The expiration date.
        option_type (str): The option type ("C" for Call).
        depth (int): The depth for fetching related tickers.

    Returns:
        dict: Scanner results for all OTM call options.
    """
    print(f"Fetching related tickers for {base_ticker} up to {depth} levels deep...")
    related_tickers = fetch_related_companies(base_ticker, depth, use_db=True)
    print(f"Found {len(related_tickers)} related tickers: {related_tickers}")

    all_results = {}

    for ticker in related_tickers:
        try:
            print(f"\nFetching OTM calls for {ticker}...")
            otm_calls = get_otm_calls(ticker, expiration_limit_days)

            for option_ticker in otm_calls:
              print(f"Running scanner for OTM call option: {option_ticker}")
              trades_by_day = get_trades(option_ticker)  # Isolated trade data for this ticker
              analyze_size_spikes(trades_by_day)

        except Exception as e:
            print(f"Error processing {ticker}: {e}")

    return all_results

if __name__ == "__main__":
    import argparse

    initialize_db()

    parser = argparse.ArgumentParser(description="Scan OTM call options for related tickers.")
    parser.add_argument("base_ticker", type=str, help="Base stock ticker (e.g., KMI)")
    parser.add_argument("--depth", type=int, default=1, help="Recursion depth for related tickers (default: 3)")
    parser.add_argument(
        "--expiration_limit_days",
        type=int,
        default=180,
        help="Max days until expiration (default: 180)"
    )

    args = parser.parse_args()

    results = run_scanner_on_otm_calls(
        args.base_ticker,
        depth=args.depth,
        expiration_limit_days=args.expiration_limit_days
    )
    print("Scanner Results:")
