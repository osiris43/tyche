# options_helpers.py

def generate_option_ticker(underlying, expiration, option_type, strike_price):
    """
    Generate an options ticker in the format used by Polygon.io.
    """
    expiration_formatted = expiration[2:].replace("-", "")
    strike_price_formatted = f"{int(strike_price * 1000):08d}"
    return f"O:{underlying.upper()}{expiration_formatted}{option_type.upper()}{strike_price_formatted}"
