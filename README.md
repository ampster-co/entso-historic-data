# ENTSO-E Historic Price Data Retriever

This project retrieves historic electricity price data from the ENTSO-E Transparency Platform for multiple countries, calculates daily metrics (min, max, weighted average), and exports the results to CSV files for analysis.

## Features

- Retrieves day-ahead electricity prices from ENTSO-E API
- Supports multiple countries (specify with --countries flag)
- Calculates daily metrics (min, max, weighted average)
- Exports data to CSV files for analysis
- Handles API rate limits by retrieving data in chunks
- Supports loading API key from .env file or command line argument
- Supports custom date ranges (--start-date, --end-date, --years)
- Supports local timezone conversion with --local-time flag

## Requirements

- Python 3.6 or higher
- Required Python packages (install with `pip install -r requirements.txt`):
  - pandas
  - numpy
  - python-dotenv
  - entsoe-py
  - pytz
  - openpyxl (for Excel export functionality)

## Installation

1. Clone this repository or download the source code
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your ENTSO-E API key:
   ```
   ENTSOE_API_KEY=your_api_key_here
   ```

## Usage

### Command Line Interface

```bash
# Retrieve data for Netherlands (last 3 years)
python entso_py_retriever.py --countries NL --years 3

# Retrieve data for Netherlands with local timezone
python entso_py_retriever.py --countries NL --years 3 --local-time

# Retrieve data for multiple countries (last 3 years)
python entso_py_retriever.py --countries NL,DE,FR --years 3

# Retrieve data for multiple countries with combined files
python entso_py_retriever.py --countries NL,DE,FR --years 3 --combined

# Retrieve data for a specific date range
python entso_py_retriever.py --countries NL --start-date 2020-01-01 --end-date 2022-12-31

# Show help message
python entso_py_retriever.py --help
```

### Interactive Runner Scripts

For a more user-friendly experience, you can use the provided runner scripts:

- **Windows**: Run `run.bat`
- **Linux/macOS**: Run `./run.sh` (make sure it's executable with `chmod +x run.sh`)

These scripts provide a menu-based interface for retrieving data with various options.

### Python Runner Script

You can also use the Python runner script for a more interactive experience:

```bash
python run_entsoe_py.py --countries NL --years 3
```

## Output Files

The script generates the following output files:

- `{country}_price_metrics_{timezone}.csv`: Daily price metrics (min, max, weighted avg) for each country
- `{country}_raw_prices_{timezone}.csv`: Raw hourly price data for each country
- `combined_price_metrics_{timezone}.csv`: Combined daily metrics for all countries (if --combined flag is used)
- `combined_raw_prices_{timezone}.csv`: Combined raw hourly data for all countries (if --combined flag is used)

The `{timezone}` in the filename indicates whether the data is in UTC or local timezone:
- When using default UTC time: `nl_price_metrics_utc.csv`
- When using local time: `nl_price_metrics_local_CEST.csv` (timezone abbreviation may vary)

### Excel Export

The project also includes a script to export the CSV data to Excel format:

```bash
# Export all CSV files to Excel
python export_to_excel.py
```

This script:
- Creates a single Excel file with multiple sheets
- Includes a summary sheet with information about the data
- Formats the data for better readability
- Handles large datasets by limiting the number of rows per sheet
- Includes country codes in the filename (e.g., `entso_price_data_NL_20250605_152855.xlsx`)
- Automatically detects which countries are included in the data

The Excel file contains the following sheets:
- Summary: Overview of the data and sheet contents
- Daily Metrics (Local Time): Min, max, and weighted average prices per day in local timezone
- Daily Metrics (UTC): Min, max, and weighted average prices per day in UTC timezone
- Raw Prices (Local Time): Hourly price data in local timezone (limited to 10,000 rows)
- Raw Prices (UTC): Hourly price data in UTC timezone (limited to 10,000 rows)

## Timezone Handling

By default, all timestamps are in UTC timezone, which is the standard for energy market data. However, you can use the `--local-time` flag to convert timestamps to the local timezone of each country:

```bash
python entso_py_retriever.py --countries NL,DE,FR --years 3 --local-time
```

This will:
1. Convert timestamps to the appropriate timezone for each country
2. Include the timezone information in the output filenames
3. Add a 'timezone' column to the output data

When using local time with multiple countries (with `--combined` flag), the combined files will use a 'local_mixed' suffix to indicate that they contain data from multiple timezones.

## API Key

You need an API key from the ENTSO-E Transparency Platform to use this script. You can get one by:

1. Registering for an account at https://transparency.entsoe.eu/
2. Logging in to your account
3. Going to 'My Account' > 'Web API Security Token'
4. Requesting a new token if you don't already have one

You can provide the API key in one of the following ways:

1. Command line argument: `--api-key YOUR_API_KEY`
2. Environment variable: `ENTSOE_API_KEY=YOUR_API_KEY`
3. `.env` file with `ENTSOE_API_KEY=YOUR_API_KEY`
