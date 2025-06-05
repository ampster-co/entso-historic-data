#!/usr/bin/env python3
"""
ENTSO-E Historic Price Data Retriever using entsoe-py

This script retrieves historic electricity price data from the ENTSO-E Transparency Platform
for multiple countries over the last 3 years, calculates daily minimum, maximum, and weighted
average prices, and exports the results to CSV files.

Features:
- Retrieves day-ahead electricity prices from ENTSO-E API
- Supports multiple countries (specify with --countries flag)
- Calculates daily metrics (min, max, weighted average)
- Exports data to CSV files for analysis
- Handles API rate limits by retrieving data in chunks
- Supports loading API key from .env file or command line argument
- Supports custom date ranges (--start-date, --end-date, --years)
- Supports local timezone conversion with --local-time flag

Usage:
    python entso_py_retriever.py [--api-key YOUR_API_KEY] --countries NL,DE,FR [--combined] [--local-time] --years 3
    python entso_py_retriever.py [--api-key YOUR_API_KEY] --countries NL,DE,FR [--combined] [--local-time] --years 5
    python entso_py_retriever.py [--api-key YOUR_API_KEY] --countries NL,DE,FR [--combined] [--local-time] --start-date 2020-01-01 --end-date 2022-12-31

Environment Variables:
    ENTSOE_API_KEY: Your ENTSO-E API key (can be set in .env file)

Output Files:
    {country}_price_metrics_{timezone}.csv: Daily price metrics (min, max, weighted avg)
    {country}_raw_prices_{timezone}.csv: Raw hourly price data
    combined_price_metrics_{timezone}.csv: Combined daily metrics (if --combined flag is used)
    combined_raw_prices_{timezone}.csv: Combined raw hourly data (if --combined flag is used)

Command Line Arguments:
    --api-key: Your ENTSO-E API key
    --countries: Comma-separated list of country codes (e.g., NL,DE,FR)
    --combined: Create combined files for all countries
    --local-time: Convert timestamps to local timezone for each country
    --start-date: Start date for data retrieval (YYYY-MM-DD)
    --end-date: End date for data retrieval (YYYY-MM-DD)
    --years: Number of years to retrieve (from today)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import time
import os
import logging
import pytz
import argparse
import dotenv
import sys
from typing import Dict, List, Tuple, Optional, Any
from entsoe import EntsoePandasClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Country code mapping
COUNTRY_CODES = {
    'AL': '10YAL-KESH-----5',  # Albania
    'AT': '10YAT-APG------L',  # Austria
    'BA': '10YBA-JPCC-----D',  # Bosnia and Herzegovina
    'BE': '10YBE----------2',  # Belgium
    'BG': '10YCA-BULGARIA-R',  # Bulgaria
    'CH': '10YCH-SWISSGRIDZ',  # Switzerland
    'CZ': '10YCZ-CEPS-----N',  # Czech Republic
    'DE': '10Y1001A1001A83F',  # Germany
    'DK': '10Y1001A1001A65H',  # Denmark
    'EE': '10Y1001A1001A39I',  # Estonia
    'ES': '10YES-REE------0',  # Spain
    'FI': '10YFI-1--------U',  # Finland
    'FR': '10YFR-RTE------C',  # France
    'GB': '10YGB----------A',  # United Kingdom
    'GR': '10YGR-HTSO-----Y',  # Greece
    'HR': '10YHR-HEP------M',  # Croatia
    'HU': '10YHU-MAVIR----U',  # Hungary
    'IE': '10YIE-1001A00010',  # Ireland
    'IT': '10YIT-GRTN-----B',  # Italy
    'LT': '10YLT-1001A0008Q',  # Lithuania
    'LU': '10YLU-CEGEDEL-NQ',  # Luxembourg
    'LV': '10YLV-1001A00074',  # Latvia
    'ME': '10YCS-CG-TSO---S',  # Montenegro
    'MK': '10YMK-MEPSO----8',  # North Macedonia
    'NL': '10YNL----------L',  # Netherlands
    'NO': '10YNO-0--------C',  # Norway
    'PL': '10YPL-AREA-----S',  # Poland
    'PT': '10YPT-REN------W',  # Portugal
    'RO': '10YRO-TEL------P',  # Romania
    'RS': '10YCS-SERBIATSOV',  # Serbia
    'SE': '10YSE-1--------K',  # Sweden
    'SI': '10YSI-ELES-----O',  # Slovenia
    'SK': '10YSK-SEPS-----K',  # Slovakia
}

# Country timezone mapping
COUNTRY_TIMEZONES = {
    'AL': 'Europe/Tirane',     # Albania
    'AT': 'Europe/Vienna',     # Austria
    'BA': 'Europe/Sarajevo',   # Bosnia and Herzegovina
    'BE': 'Europe/Brussels',   # Belgium
    'BG': 'Europe/Sofia',      # Bulgaria
    'CH': 'Europe/Zurich',     # Switzerland
    'CZ': 'Europe/Prague',     # Czech Republic
    'DE': 'Europe/Berlin',     # Germany
    'DK': 'Europe/Copenhagen', # Denmark
    'EE': 'Europe/Tallinn',    # Estonia
    'ES': 'Europe/Madrid',     # Spain
    'FI': 'Europe/Helsinki',   # Finland
    'FR': 'Europe/Paris',      # France
    'GB': 'Europe/London',     # United Kingdom
    'GR': 'Europe/Athens',     # Greece
    'HR': 'Europe/Zagreb',     # Croatia
    'HU': 'Europe/Budapest',   # Hungary
    'IE': 'Europe/Dublin',     # Ireland
    'IT': 'Europe/Rome',       # Italy
    'LT': 'Europe/Vilnius',    # Lithuania
    'LU': 'Europe/Luxembourg', # Luxembourg
    'LV': 'Europe/Riga',       # Latvia
    'ME': 'Europe/Podgorica',  # Montenegro
    'MK': 'Europe/Skopje',     # North Macedonia
    'NL': 'Europe/Amsterdam',  # Netherlands
    'NO': 'Europe/Oslo',       # Norway
    'PL': 'Europe/Warsaw',     # Poland
    'PT': 'Europe/Lisbon',     # Portugal
    'RO': 'Europe/Bucharest',  # Romania
    'RS': 'Europe/Belgrade',   # Serbia
    'SE': 'Europe/Stockholm',  # Sweden
    'SI': 'Europe/Ljubljana',  # Slovenia
    'SK': 'Europe/Bratislava', # Slovakia
}

def print_usage():
    """
    Print usage information for the script.
    """
    print("\nUsage:")
    print("  python entso_py_retriever.py [--api-key YOUR_API_KEY] --countries NL,DE,FR [--combined] [--local-time] --years 3")
    print("  python entso_py_retriever.py [--api-key YOUR_API_KEY] --countries NL,DE,FR [--combined] [--local-time] --years 5")
    print("  python entso_py_retriever.py [--api-key YOUR_API_KEY] --countries NL,DE,FR [--combined] [--local-time] --start-date 2020-01-01 --end-date 2022-12-31")
    print("\nCommand Line Arguments:")
    print("  --api-key: Your ENTSO-E API key")
    print("  --countries: Comma-separated list of country codes (e.g., NL,DE,FR)")
    print("  --combined: Create combined files for all countries")
    print("  --local-time: Convert timestamps to local timezone for each country")
    print("  --start-date: Start date for data retrieval (YYYY-MM-DD)")
    print("  --end-date: End date for data retrieval (YYYY-MM-DD)")
    print("  --years: Number of years to retrieve (from today)")
    print("\nExamples:")
    print("  # Retrieve data for Netherlands (last 3 years)")
    print("  python entso_py_retriever.py --api-key YOUR_API_KEY --countries NL --years 3")
    print("\n  # Retrieve data for multiple countries with local timezone")
    print("  python entso_py_retriever.py --api-key YOUR_API_KEY --countries NL,DE,FR --local-time --years 3")
    print("\n  # Retrieve data for a specific date range")
    print("  python entso_py_retriever.py --api-key YOUR_API_KEY --countries NL --start-date 2020-01-01 --end-date 2022-12-31")
    print("\n  # Retrieve data for the last N years")
    print("  python entso_py_retriever.py --api-key YOUR_API_KEY --countries NL --years 5")
    print("\n  # Show this help message")
    print("  python entso_py_retriever.py --help")

def get_api_key() -> str:
    """
    Get the ENTSO-E API key from environment variables or command line arguments.
    
    The function checks for the API key in the following order of priority:
    1. Command line argument (--api-key)
    2. Environment variable (ENTSOE_API_KEY)
    
    Returns:
        str: The ENTSO-E API key
    
    Raises:
        SystemExit: If no API key is provided
    """
    parser = argparse.ArgumentParser(description='Retrieve ENTSO-E historic price data')
    parser.add_argument('--api-key', type=str, help='ENTSO-E API key')
    args, _ = parser.parse_known_args()
    
    # Try to load from .env file
    dotenv.load_dotenv()
    
    # Priority: 1. Command line argument, 2. Environment variable
    if args.api_key:
        return args.api_key
    elif os.environ.get('ENTSOE_API_KEY'):
        return os.environ.get('ENTSOE_API_KEY')
    else:
        logger.error("No API key provided. Please provide an API key via --api-key argument or ENTSOE_API_KEY environment variable.")
        logger.error("You can get an API key from the ENTSO-E Transparency Platform: https://transparency.entsoe.eu/")
        logger.error("1. Register for an account")
        logger.error("2. Log in to your account")
        logger.error("3. Go to 'My Account' > 'Web API Security Token'")
        logger.error("4. Request a new token if you don't already have one")
        print_usage()
        sys.exit(1)

def get_countries() -> List[str]:
    """
    Get the list of countries to retrieve data for from command line arguments.
    
    Returns:
        List[str]: List of country codes
    
    Raises:
        SystemExit: If no countries are provided or if all provided countries are invalid
    """
    parser = argparse.ArgumentParser(description='Retrieve ENTSO-E historic price data')
    parser.add_argument('--countries', type=str, help='Comma-separated list of country codes (e.g., NL,DE,FR)')
    args, _ = parser.parse_known_args()
    
    if not args.countries:
        logger.error("No countries provided. Please provide at least one country code via --countries argument.")
        print_usage()
        sys.exit(1)
    
    # Split by comma and strip whitespace
    countries = [country.strip().upper() for country in args.countries.split(',')]
    
    # Validate country codes
    valid_countries = []
    for country in countries:
        if country in COUNTRY_CODES:
            valid_countries.append(country)
        else:
            logger.warning(f"Invalid country code: {country}. Skipping.")
    
    if not valid_countries:
        logger.error("No valid country codes provided. Please provide at least one valid country code.")
        logger.error("Available country codes: " + ", ".join(sorted(COUNTRY_CODES.keys())))
        print_usage()
        sys.exit(1)
    
    return valid_countries

def should_create_combined_files() -> bool:
    """
    Check if combined files should be created based on command line arguments.
    
    Returns:
        bool: True if combined files should be created, False otherwise
    """
    parser = argparse.ArgumentParser(description='Retrieve ENTSO-E historic price data')
    parser.add_argument('--combined', action='store_true', help='Create combined files for all countries')
    args, _ = parser.parse_known_args()
    
    return args.combined

def should_use_local_time() -> bool:
    """
    Check if timestamps should be converted to local timezone based on command line arguments.
    
    Returns:
        bool: True if local timezone should be used, False otherwise (default to UTC)
    """
    parser = argparse.ArgumentParser(description='Retrieve ENTSO-E historic price data')
    parser.add_argument('--local-time', action='store_true', help='Convert timestamps to local timezone for each country')
    args, _ = parser.parse_known_args()
    
    return args.local_time

def get_date_range() -> Tuple[datetime, datetime]:
    """
    Get the date range for data retrieval from command line arguments.
    
    The function checks for the date range in the following order of priority:
    1. Start date and end date arguments (--start-date, --end-date)
    2. Years argument (--years)
    3. Exit with error if no date range is provided
    
    Returns:
        Tuple[datetime, datetime]: Tuple containing (start_date, end_date)
    
    Raises:
        SystemExit: If no date range is provided
    """
    parser = argparse.ArgumentParser(description='Retrieve ENTSO-E historic price data')
    parser.add_argument('--start-date', type=str, help='Start date for data retrieval (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date for data retrieval (YYYY-MM-DD)')
    parser.add_argument('--years', type=int, help='Number of years to retrieve (from today)')
    args, _ = parser.parse_known_args()
    
    end_date = datetime.now()
    date_range_provided = False
    
    # Priority: 1. Start date and end date, 2. Years
    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
            date_range_provided = True
            
            if args.end_date:
                try:
                    end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
                except ValueError:
                    logger.warning(f"Invalid end date format: {args.end_date}. Using current date.")
            
            logger.info(f"Using date range: {start_date.date()} to {end_date.date()}")
            return start_date, end_date
        except ValueError:
            logger.warning(f"Invalid start date format: {args.start_date}. Please provide a valid date in YYYY-MM-DD format.")
            print_usage()
            sys.exit(1)
    
    if args.years:
        if args.years > 0:
            start_date = end_date - timedelta(days=args.years * 365)
            date_range_provided = True
            logger.info(f"Retrieving data for the last {args.years} years: {start_date.date()} to {end_date.date()}")
            return start_date, end_date
        else:
            logger.warning(f"Invalid years value: {args.years}. Please provide a positive integer.")
            print_usage()
            sys.exit(1)
    
    # No date range provided, show usage and exit
    logger.error("No date range provided. Please provide a date range using --start-date and --end-date, or --years.")
    print_usage()
    sys.exit(1)

def retrieve_day_ahead_prices(start_date: datetime, end_date: datetime, api_key: str, country_code: str) -> pd.DataFrame:
    """
    Retrieve day-ahead prices from ENTSO-E API for the specified time period and country.
    
    This function queries the ENTSO-E API for day-ahead electricity prices
    for the specified country within the specified time period. It handles the
    conversion of the API response to a pandas DataFrame.
    
    Args:
        start_date (datetime): Start date for data retrieval
        end_date (datetime): End date for data retrieval
        api_key (str): ENTSO-E API key
        country_code (str): Country code (e.g., 'NL' for Netherlands)
        
    Returns:
        pd.DataFrame: DataFrame with day-ahead price data containing columns:
            - datetime: Timestamp of the price data
            - price: Electricity price in EUR/MWh
            - country: Country code
    """
    logger.info(f"Retrieving day-ahead prices for {country_code} from {start_date.date()} to {end_date.date()}")
    
    try:
        # Initialize client
        client = EntsoePandasClient(api_key=api_key)
        
        # Get the domain code for the country
        domain_code = COUNTRY_CODES.get(country_code)
        if not domain_code:
            logger.error(f"Invalid country code: {country_code}")
            return pd.DataFrame()
        
        # Retrieve day-ahead prices
        prices = client.query_day_ahead_prices(
            country_code=country_code,
            start=pd.Timestamp(start_date).tz_localize('UTC'),
            end=pd.Timestamp(end_date).tz_localize('UTC')
        )
        
        # Convert to DataFrame
        if isinstance(prices, pd.Series):
            df = prices.to_frame(name='price')
            df.reset_index(inplace=True)
            df.rename(columns={'index': 'datetime'}, inplace=True)
            
            # Add country column
            df['country'] = country_code
            
            return df
        else:
            logger.error(f"Unexpected result format from entsoe-py client for {country_code}")
            return pd.DataFrame()
    
    except Exception as e:
        logger.error(f"Error retrieving day-ahead prices for {country_code}: {str(e)}")
        return pd.DataFrame()

def retrieve_data_in_chunks(start_date: datetime, end_date: datetime, api_key: str, country_code: str, chunk_days: int = 30) -> pd.DataFrame:
    """
    Retrieve data from ENTSO-E API in chunks to handle API limitations.
    
    This function breaks down the data retrieval into smaller time chunks
    to avoid hitting API rate limits and to handle large date ranges more
    efficiently.
    
    Args:
        start_date (datetime): Start date for data retrieval
        end_date (datetime): End date for data retrieval
        api_key (str): ENTSO-E API key
        country_code (str): Country code (e.g., 'NL' for Netherlands)
        chunk_days (int, optional): Number of days per chunk. Defaults to 30.
        
    Returns:
        pd.DataFrame: Combined DataFrame with price data from all chunks
    """
    dfs = []
    
    current_start = start_date
    while current_start < end_date:
        current_end = min(current_start + timedelta(days=chunk_days), end_date)
        
        # Get day-ahead prices for this chunk
        df = retrieve_day_ahead_prices(current_start, current_end, api_key, country_code)
        if not df.empty:
            dfs.append(df)
        
        # Move to next chunk
        current_start = current_end
        
        # Sleep to avoid hitting API rate limits
        time.sleep(1)
    
    # Combine all chunks
    if dfs:
        return pd.concat(dfs).reset_index(drop=True)
    else:
        return pd.DataFrame()

def convert_to_local_timezone(df: pd.DataFrame, country_code: str) -> pd.DataFrame:
    """
    Convert timestamps in DataFrame to local timezone for the specified country.
    
    Args:
        df (pd.DataFrame): DataFrame with UTC timestamps
        country_code (str): Country code to determine the timezone
        
    Returns:
        pd.DataFrame: DataFrame with timestamps converted to local timezone
    """
    if df.empty:
        return df
    
    # Get the timezone for the country
    timezone = COUNTRY_TIMEZONES.get(country_code, 'UTC')
    logger.info(f"Converting timestamps for {country_code} to {timezone}")
    
    # Make a copy to avoid modifying the original DataFrame
    df_local = df.copy()
    
    # Ensure datetime column is timezone-aware (UTC)
    if df_local['datetime'].dt.tz is None:
        df_local['datetime'] = df_local['datetime'].dt.tz_localize('UTC')
    
    # Convert to local timezone
    df_local['datetime'] = df_local['datetime'].dt.tz_convert(timezone)
    
    # Add timezone info column
    df_local['timezone'] = timezone
    
    return df_local

def calculate_daily_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate daily minimum, maximum, and weighted average prices.
    
    This function groups the hourly price data by date and calculates
    the minimum, maximum, and weighted average prices for each day.
    
    The weighted average is calculated as the arithmetic mean of all hourly prices
    for each day. Since the ENTSO-E API provides hourly price data with equal time
    intervals, a simple arithmetic mean is used:
    
    weighted_avg = sum(hourly_prices) / len(hourly_prices)
    
    This calculation is performed for each day and each country separately.
    The result represents the average electricity price for the day, giving
    equal weight to each hour.
    
    Args:
        df (pd.DataFrame): DataFrame with hourly price data
        
    Returns:
        pd.DataFrame: DataFrame with daily metrics containing columns:
            - date: Date of the metrics
            - country: Country code
            - min_price: Minimum price for the day
            - max_price: Maximum price for the day
            - weighted_avg: Weighted average price for the day
    """
    if df.empty:
        logger.error("No data available to calculate metrics")
        return pd.DataFrame()
    
    # Convert datetime to date for grouping
    df['date'] = df['datetime'].dt.date
    
    # Group by date and country
    grouped = df.groupby(['date', 'country'])
    
    # Calculate metrics
    min_prices = grouped['price'].min().reset_index()
    max_prices = grouped['price'].max().reset_index()
    avg_prices = grouped['price'].mean().reset_index()  # This calculates the arithmetic mean (weighted average)
    
    # Merge the metrics
    metrics = min_prices.rename(columns={'price': 'min_price'})
    metrics = metrics.merge(
        max_prices.rename(columns={'price': 'max_price'}),
        on=['date', 'country'],
        how='left'
    )
    metrics = metrics.merge(
        avg_prices.rename(columns={'price': 'weighted_avg'}),
        on=['date', 'country'],
        how='left'
    )
    
    # Add timezone info if available in the original DataFrame
    if 'timezone' in df.columns:
        # Get the timezone for each country
        timezone_info = df.groupby('country')['timezone'].first().reset_index()
        metrics = metrics.merge(timezone_info, on='country', how='left')
    
    return metrics

def export_to_csv(df: pd.DataFrame, filename: str) -> None:
    """
    Export DataFrame to CSV file.
    
    Args:
        df (pd.DataFrame): DataFrame to export
        filename (str): Output filename
    """
    df.to_csv(filename, index=False)
    logger.info(f"Data exported to {filename}")

def get_timezone_suffix(country_code: str, use_local_time: bool) -> str:
    """
    Get the timezone suffix for filenames based on the country and whether local time is used.
    
    Args:
        country_code (str): Country code to determine the timezone
        use_local_time (bool): Whether to use local timezone
        
    Returns:
        str: Timezone suffix for filenames
    """
    if use_local_time:
        # Get the timezone abbreviation (e.g., CET, EET)
        timezone_name = COUNTRY_TIMEZONES.get(country_code, 'UTC')
        tz = pytz.timezone(timezone_name)
        now = datetime.now(tz)
        timezone_abbr = now.strftime('%Z')  # Get timezone abbreviation
        return f"local_{timezone_abbr}"
    else:
        return "utc"

def process_country_data(country_code: str, api_key: str, start_date: datetime, end_date: datetime, use_local_time: bool) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Process data for a specific country.
    
    This function retrieves data for a specific country, calculates metrics,
    and exports the results to CSV files.
    
    Args:
        country_code (str): Country code (e.g., 'NL' for Netherlands)
        api_key (str): ENTSO-E API key
        start_date (datetime): Start date for data retrieval
        end_date (datetime): End date for data retrieval
        use_local_time (bool): Whether to convert timestamps to local timezone
        
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: Tuple containing (metrics_df, raw_df)
    """
    logger.info(f"Processing data for {country_code}")
    
    # Retrieve data from API
    logger.info(f"Retrieving data for {country_code} from {start_date.date()} to {end_date.date()}")
    df = retrieve_data_in_chunks(start_date, end_date, api_key, country_code)
    
    if df.empty:
        logger.error(f"No data retrieved for {country_code}. Skipping.")
        return pd.DataFrame(), pd.DataFrame()
    
    # Get timezone suffix for filenames
    timezone_suffix = get_timezone_suffix(country_code, use_local_time)
    
    # Convert to local timezone if requested
    if use_local_time:
        df = convert_to_local_timezone(df, country_code)
        timezone_info = f" (using {COUNTRY_TIMEZONES.get(country_code, 'UTC')} timezone)"
    else:
        timezone_info = " (using UTC timezone)"
    
    # Calculate metrics
    daily_metrics = calculate_daily_metrics(df)
    
    # Export to CSV with timezone in filename
    metrics_filename = f"{country_code.lower()}_price_metrics_{timezone_suffix}.csv"
    raw_filename = f"{country_code.lower()}_raw_prices_{timezone_suffix}.csv"
    
    export_to_csv(daily_metrics, metrics_filename)
    export_to_csv(df, raw_filename)
    
    logger.info(f"Processed data for {country_code}{timezone_info}")
    
    return daily_metrics, df

def main():
    """
    Main function to orchestrate the data retrieval and processing.
    
    This function:
    1. Gets the API key from environment variables or command line arguments
    2. Gets the list of countries to retrieve data for
    3. Gets the date range for data retrieval
    4. Retrieves day-ahead price data from the ENTSO-E API for each country
    5. Calculates daily metrics (min, max, weighted average)
    6. Exports the data to CSV files
    """
    # Check if help is requested
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print_usage()
        sys.exit(0)
    
    logger.info("Starting ENTSO-E data retrieval using entsoe-py")
    
    # Get API key
    api_key = get_api_key()
    
    # Get countries
    countries = get_countries()
    logger.info(f"Retrieving data for countries: {', '.join(countries)}")
    
    # Get date range
    start_date, end_date = get_date_range()
    
    # Check if combined files should be created
    create_combined = should_create_combined_files()
    if create_combined:
        logger.info("Combined files will be created")
    else:
        logger.info("Only individual country files will be created")
    
    # Check if local timezone should be used
    use_local_time = should_use_local_time()
    if use_local_time:
        logger.info("Using local timezone for each country")
    else:
        logger.info("Using UTC timezone for all data")
    
    try:
        all_metrics = []
        all_raw_data = []
        
        # Process each country
        for country_code in countries:
            metrics_df, raw_df = process_country_data(country_code, api_key, start_date, end_date, use_local_time)
            
            if not metrics_df.empty:
                all_metrics.append(metrics_df)
            
            if not raw_df.empty:
                all_raw_data.append(raw_df)
        
        # Combine all metrics and raw data if requested
        if create_combined and len(countries) > 1:
            # Get timezone suffix for combined files
            timezone_suffix = "utc"
            if use_local_time:
                timezone_suffix = "local_mixed"  # Since we have multiple countries with different timezones
            
            if all_metrics:
                combined_metrics = pd.concat(all_metrics).reset_index(drop=True)
                export_to_csv(combined_metrics, f"combined_price_metrics_{timezone_suffix}.csv")
            
            if all_raw_data:
                combined_raw = pd.concat(all_raw_data).reset_index(drop=True)
                export_to_csv(combined_raw, f"combined_raw_prices_{timezone_suffix}.csv")
        
        logger.info("ENTSO-E data retrieval and processing completed")
        
    except Exception as e:
        logger.error(f"Error during data retrieval: {str(e)}")
        logger.error("Failed to retrieve data. Exiting.")
        return

if __name__ == "__main__":
    main()
