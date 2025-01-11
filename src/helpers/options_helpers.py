from polygon import RESTClient
from datetime import datetime, timedelta

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

    # Otherwise, hit the API (handle the case where API is down or empty response)
    try:
        related_companies = client.get_related_companies(ticker)
        related_tickers = [
            related.ticker for related in related_companies
        ]  # Adjust if structure differs

        print(
            f"Fetched {len(related_tickers)} related tickers for {ticker} from the API."
        )
        seen.update(related_tickers)

        # Recurse for each related ticker
        for related_ticker in related_tickers:
            if related_ticker not in seen:
                fetch_related_companies(related_ticker, depth - 1, seen)

        return seen

    except Exception as e:
        print(f"Error fetching related companies for {ticker}: {e}")
        return seen


def get_last_trading_day():
    # Convert the input string to a datetime object
    date_obj = datetime.now()

    # Get the day of the week (0=Monday, ..., 6=Sunday)
    day_of_week = date_obj.weekday()
    target_date = date_obj

    # Want the last trading day before this one.  S,S,M = F.  This is because
    # my polygon license doesn't allow for day of data.
    if day_of_week in [5, 6]:
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
    d = get_last_trading_day()
    print(d)
    request = client.get_daily_open_close_agg(ticker, d)

    return float(request.close)


def get_contracts_by_underlying(underlying, expiration, percentage=1.0):
    current_price = get_current_price(underlying)
    print(f"Current Price: {current_price}")
    otm_threshold = current_price * percentage
    options = client.list_options_contracts(
        underlying, contract_type="call", expiration_date=expiration
    )

    otm_calls = [opt for opt in options if opt.strike_price > otm_threshold]
    print(f"Options Length: {len(otm_calls)}")

    return otm_calls


from datetime import datetime, timedelta


def get_monthly_expirations():
    """
    Returns an array of dates (yyyy-mm-dd) for the third Friday of the next six months.

    Returns:
        list: List of date strings in yyyy-mm-dd format.
    """
    today = datetime.now()
    monthly_expirations = []

    for i in range(0, 8):  # Next 6 months
        # Calculate the first day of the month
        first_day_of_month = (today.replace(day=1) + timedelta(days=32 * i)).replace(
            day=1
        )

        # Find the first Friday of the month
        first_friday_offset = (4 - first_day_of_month.weekday()) % 7
        first_friday = first_day_of_month + timedelta(days=first_friday_offset)

        # Calculate the third Friday
        third_friday = first_friday + timedelta(weeks=2)

        # Format as yyyy-mm-dd and add to the list
        monthly_expirations.append(third_friday.strftime("%Y-%m-%d"))

    return monthly_expirations
