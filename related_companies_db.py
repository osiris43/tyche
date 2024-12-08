import sqlite3
from datetime import datetime

DB_PATH = "related_companies.db"

def initialize_db():
    """
    Initializes the SQLite database and creates the related_companies table if it doesn't exist.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS related_companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            base_ticker TEXT NOT NULL,
            related_ticker TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_related_companies(base_ticker, related_tickers):
    """
    Saves related companies to the database.

    Args:
        base_ticker (str): The ticker for which related companies were fetched.
        related_tickers (list): A list of related tickers.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()

    for related_ticker in related_tickers:
        cursor.execute("""
            INSERT INTO related_companies (base_ticker, related_ticker, timestamp)
            VALUES (?, ?, ?)
        """, (base_ticker, related_ticker, timestamp))

    conn.commit()
    conn.close()

def get_related_companies_from_db(base_ticker):
    """
    Retrieves related companies for a given ticker from the database.

    Args:
        base_ticker (str): The ticker to search for.

    Returns:
        list: A list of related tickers.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT related_ticker FROM related_companies
        WHERE base_ticker = ?
    """, (base_ticker,))
    rows = cursor.fetchall()
    conn.close()

    return [row[0] for row in rows]
