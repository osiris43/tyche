from polygon import RESTClient
import os
import time
from src.helpers.options_helpers import (
    get_contracts_by_underlying,
    get_monthly_expirations,
)
from collections import defaultdict
from datetime import datetime, timedelta
import plotly.graph_objects as go
from dotenv import load_dotenv

load_dotenv()  # take environment variables

# Ensure the POLYGON_API_KEY is set as an environment variable
API_KEY = os.getenv("POLYGON_API_KEY")

if not API_KEY:
    raise EnvironmentError("POLYGON_API_KEY environment variable is not set.")

# Initialize the RESTClient
client = RESTClient(API_KEY)


def main(underlying):
    monthly = get_monthly_expirations()
    contracts = []

    for expiration in monthly:
        contracts.extend(get_contracts_by_underlying(underlying, expiration))

    print(contracts)


if __name__ == "__main__":
    import argparse

    print("Hello")
    parser = argparse.ArgumentParser(description="Daily Natual Gas Report")
    parser.add_argument("symbol", type=str, help="Stock symbol (e.g., AR)")

    args = parser.parse_args()

    main(args.symbol)
