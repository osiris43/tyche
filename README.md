# Scanner for Related Companies and Options Analysis

This Python script provides a scanner that analyzes financial data for a given base ticker symbol. It fetches related companies from the Polygon API, identifies out-of-the-money (OTM) call options, and analyzes trade volumes for potential spikes. The script includes functionality to cache related companies locally in an SQLite database to reduce API dependency and improve performance.

## Features

- **Fetch Related Companies**: Recursively find related companies for a given ticker.
- **Analyze OTM Calls**: Identify out-of-the-money call options with expirations at least a month away.
- **Trade Volume Analysis**: Detect unusual spikes in trade volumes for OTM call options.
- **Database Caching**: Save and retrieve related companies from an SQLite database.

## Prerequisites

- Python 3.8 or later
- A Polygon.io API key (set as the environment variable POLYGON_API_KEY).

## Installation

1. Clone this repository:

``` bash
git clone https://github.com/osiris43/tyche.git
cd tyche 
```

2. Create a Python virtual environment:

``` bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required dependencies:

``` bash
pip install -r requirements/dev.txt
```

4. Ensure your Polygon API key is set:

``` bash
    export POLYGON_API_KEY=your_api_key  # On Windows: set POLYGON_API_KEY=your_api_key
```

## Usage
Running the Script

    Initialize the SQLite database (first-time setup):

python
>>> from related_companies_db import initialize_db
>>> initialize_db()

Run the scanner for a specific ticker:

    python related_companies_scanner.py

Example

To analyze related companies and OTM calls for KMI:

    The script will fetch related companies, identify OTM calls with expirations a month or more away, and analyze trade volumes.

Fetching related tickers for KMI up to 1 levels deep...
Found 5 related tickers: {'LNG', 'OKE', 'CVX', 'XOM', 'KMI'}

Fetching OTM calls for KMI...
Current price for KMI: 28.5
Found OTM calls: ['O:KMI250117C00030000', 'O:KMI250117C00032000']

Fetching trades for all OTM call options for KMI...
Analyzing size spikes for KMI OTM calls...
Average daily traded size (last 19 days): 1200.50
Spike detected! Total size on 2024-11-19 is more than 10x the average.

File Structure

.
├── scanner.py                  # Main script for the scanner
├── related_companies_db.py     # Module for SQLite database interactions
├── requirements/               # Directory for dependency requirements
│   └── dev.txt                 # Development dependencies
└── related_companies.db        # SQLite database (created after first run)

Future Enhancements

    Manual Overrides: Allow skipping the database lookup to refresh related companies.
    Visualization: Add graphical output for trade volume trends.
    Advanced Filtering: Include criteria for deeper analysis of related companies and options.

Troubleshooting
No Related Companies Returned

If the Polygon API fails to return related companies:

    Check your POLYGON_API_KEY environment variable.
    Ensure your API subscription includes access to related company data.
    Use the SQLite database to retrieve previously saved companies.

Polygon API Rate Limits

If you encounter rate limits:

    Reduce the depth of recursion (depth parameter in fetch_related_companies).
    Cache more data locally to minimize API calls.0