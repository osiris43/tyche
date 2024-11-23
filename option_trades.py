import argparse
from datetime import datetime, timedelta
from polygon import RESTClient

client = RESTClient()  # POLYGON_API_KEY environment variable is used

parser = argparse.ArgumentParser(
    description="Analyze stock performance and compare with index."
)
parser.add_argument("symbol", type=str, help="Stock symbol (e.g., AAPL)")
parser.add_argument("option_type", type=str, help="Option type (call, put)")
parser.add_argument("expiration", type=str, help="Expiration date (YYYY-MM-DD)")
parser.add_argument("strike", type=float, help="Strike price")


def generate_option_ticker(underlying, expiration, option_type, strike_price):
    """
    Generate an options ticker in the format used by Polygon.io.

    Args:
        underlying (str): The underlying stock ticker (e.g., "GME").
        expiration (str): The expiration date in "YYYY-MM-DD" format.
        option_type (str): "C" for Call or "P" for Put.
        strike_price (float): The strike price.

    Returns:
        str: The formatted options ticker.
    """
    # Convert expiration date to YYMMDD format
    expiration_formatted = expiration[2:].replace("-", "")

    # Convert strike price to an 8-character string (scaled by 1000, padded with zeros)
    strike_price_formatted = f"{int(strike_price * 1000):08d}"

    # Combine all parts into the ticker
    option_ticker = f"O:{underlying.upper()}{expiration_formatted}{option_type.upper()}{strike_price_formatted}"

    print(option_ticker)
    return option_ticker


def get_trades(ticker):
    # Get today's date
    today = datetime.now()
    # Calculate yesterday's date
    yesterday = today - timedelta(days=2)
    yesterday_formatted = yesterday.strftime("%Y-%m-%d")

    trades = []

    for t in client.list_trades(ticker, timestamp_gt=yesterday_formatted):
        trades.append(t)

    trades.sort(key=lambda x: x.size, reverse=True)
    return trades


def main(underlying, expiration, option_type, strike_price):
    ticker = generate_option_ticker(underlying, expiration, option_type, strike_price)

    trades = get_trades(ticker)
    print(f"Number of trades: {len(trades)}")
    print(trades[0])
    print(trades[1])


if __name__ == "__main__":
    args = parser.parse_args()
    main(args.symbol, args.expiration, args.option_type, args.strike)
