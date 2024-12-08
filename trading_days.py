import sys
from datetime import datetime
import pandas as pd
from pandas_market_calendars import get_calendar

def calculate_trading_days(start_date_str):
    try:
        # Parse the input date
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        today = datetime.now()

        if start_date > today:
            print("The start date cannot be in the future.")
            return

        # Get the NYSE trading calendar
        nyse = get_calendar('NYSE')

        # Get the valid trading sessions
        trading_days = nyse.valid_days(start_date=start_date, end_date=today)

        # Count the trading days
        num_trading_days = len(trading_days)
        print(f"There have been {num_trading_days} trading days since {start_date.strftime('%Y-%m-%d')}.")
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python trading_days_calculator.py <start_date>")
        print("Example: python trading_days_calculator.py 2020-01-01")
    else:
        start_date_str = sys.argv[1]
        calculate_trading_days(start_date_str)
