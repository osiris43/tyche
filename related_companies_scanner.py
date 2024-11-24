from collections import defaultdict
from datetime import datetime, timedelta
from polygon import RESTClient
import time

client = RESTClient()  # Ensure POLYGON_API_KEY is set in your environment


def generate_option_ticker(underlying, expiration, option_type, strike_price):
    """
    Generate an options ticker in the format used by Polygon.io.
    """
    expiration_formatted = expiration[2:].replace("-", "")
    strike_price_formatted = f"{int(strike_price * 1000):08d}"
    return f"O:{underlying.upper()}{expiration_formatted}{option_type.upper()}{strike_price_formatted}"


def fetch_related_companies(ticker, depth=3, seen=None):
    """
    Recursively fetch related companies up to the specified depth.

    Args:
        ticker (str): Initial stock ticker (e.g., "LNG").
        depth (int): Maximum recursion depth.
        seen (set): Set of already-seen tickers to avoid duplicates.

    Returns:
        set: A set of related tickers.
    """
    if seen is None:
        seen = set()

    # Base case: Stop recursion if depth is 0
    if depth == 0:
        return seen

    try:
        # Fetch related companies for the current ticker
        related_companies = client.get_related_companies(ticker)

        # Extract tickers from the related company objects
        for related in related_companies:
            related_ticker = related.ticker
            if related_ticker not in seen:
                seen.add(related_ticker)
                # Recurse on the related ticker
                fetch_related_companies(related_ticker, depth - 1, seen)

        return seen
    except Exception as e:
        print(f"Error fetching related companies for {ticker}: {e}")
        return seen


def get_trades(option_tickers):
    """
    Fetch trades for a list of option tickers and aggregate their sizes by date.

    Args:
        option_tickers (list): A list of option tickers (e.g., ["O:KMI250117C00030000", ...]).

    Returns:
        dict: A dictionary with dates as keys and total trade size as values across all tickers.
    """
    trades_by_day = defaultdict(int)

    for option_ticker in option_tickers:
        try:
            # Fetch trades from Polygon
            for t in client.list_trades(option_ticker):
                # Convert SIP timestamp to a date
                trade_date = datetime.utcfromtimestamp(
                    t.sip_timestamp / 1_000_000_000
                ).strftime("%Y-%m-%d")
                trades_by_day[trade_date] += t.size  # Aggregate trade size
        except Exception as e:
            print(f"Error fetching trades for {option_ticker}: {e}")

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

    # If the day is Friday (4), Saturday (5), or Sunday (6), find the previous Friday
    if day_of_week >= 4:
        # Calculate the number of days to subtract to reach the previous Friday
        days_to_subtract = day_of_week - 4
        friday_date = date_obj - timedelta(days=days_to_subtract)
        return friday_date.strftime("%Y-%m-%d")

    # Otherwise, return the original date
    return date_obj.strftime("%Y-%m-%d")


# Helper function for fetching current stock price (pseudo-code)
def get_current_price(ticker):
    """
    Fetch the current stock price for a ticker.
    Replace this with an actual API call or logic.
    """
    request = client.get_daily_open_close_agg(ticker, get_friday_or_date())

    return float(request.close)


def get_otm_calls(ticker):
    """
    Fetch all OTM call options for a given ticker.

    Args:
        ticker (str): The stock ticker (e.g., "KMI").

    Returns:
        list: A list of OTM call option tickers.
    """

    next_month = datetime.now() + timedelta(days=30)
    print(next_month.strftime("%Y-%m-%d"))
    try:
        # Fetch the current stock price
        current_price = get_current_price(ticker)
        print(f"Current price for {ticker}: {current_price}")

        # Fetch the options chain for the ticker
        options = client.list_options_contracts(
            ticker, params={"expiration_date.gt": next_month.strftime("%Y-%m-%d")}
        )
        otm_calls = []

        # Filter for OTM call options
        for option in options:
            if option.contract_type == "call" and option.strike_price > current_price:
                otm_calls.append(option.ticker)  # Use the full option ticker

        return otm_calls

    except Exception as e:
        print(f"Error fetching OTM calls for {ticker}: {e}")
        return []


def run_scanner_on_otm_calls(base_ticker, depth=3):
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
    related_tickers = fetch_related_companies(base_ticker, depth)
    print(f"Found {len(related_tickers)} related tickers: {related_tickers}")

    all_results = {}

    for ticker in related_tickers:
        try:
            print(f"\nFetching OTM calls for {ticker}...")
            otm_calls = get_otm_calls(ticker)

            for option_ticker in otm_calls:
                print(f"Running scanner for OTM call option: {option_ticker}")
                trades_by_day = get_trades(otm_calls)
                scan_result = analyze_size_spikes(trades_by_day)
                all_results[option_ticker] = scan_result

        except Exception as e:
            print(f"Error processing {ticker}: {e}")

    return all_results


# Example usage
if __name__ == "__main__":
    base_ticker = "KMI"
    depth = 1  # Adjust recursion depth

    results = run_scanner_on_otm_calls(base_ticker, depth=depth)
    print("Scanner Results:")
    # print(results)
