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

## Configuration

All country-specific metadata is now managed in `country_config.json`. This file must be present in the project root and should contain an entry for each country you wish to fetch data for.

### Required fields for each country:
- `domain_code`: ENTSO-E domain code (required)
- `timezone`: IANA timezone string (required)

### Optional fields for tax-inclusive calculations:
- `energy_tax`: Numeric (optional)
- `renewable_energy_tax`: Numeric (optional)
- `vat_rate`: Numeric (optional)
- `currency`: String (optional)

If any of the tax fields are missing for a country, tax-inclusive columns (such as `weighted_avg_kwh_all_in_price`) will not be present in the output for that country.

### Example country_config.json
```json
{
  "NL": {
    "domain_code": "10YNL----------L",
    "timezone": "Europe/Amsterdam",
    "energy_tax": 0.1228,
    "renewable_energy_tax": 0.001,
    "vat_rate": 0.21,
    "currency": "EUR"
  },
  "DE": {
    "domain_code": "10Y1001A1001A83F",
    "timezone": "Europe/Berlin"
  }
}
```

## Supported Countries

The list of supported countries is dynamic and based on the keys present in `country_config.json`. You can add or remove countries by editing this file. Countries with only `domain_code` and `timezone` will still allow data fetching, but tax-inclusive columns will be omitted.

## Output Columns

- Daily price metrics CSVs will include columns for min, max, and weighted average prices in both EUR/MWh and EUR/kWh.
- If tax fields are present for a country, a `weighted_avg_kwh_all_in_price` column will be included, representing the all-in price based on the weighted average.
- If tax fields are missing, this column will not be present for that country.

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

## Usage

**You must specify either `--local-time` or `--utc` when running the script. If neither is provided, the script will exit with an error.**

Run the retriever as before. The script will automatically use the configuration in `country_config.json` for all country-specific logic.

---

For further details, see the code docstrings or contact the maintainer.
