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
import json
from typing import Dict, List, Tuple, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

def get_countries(country_config=None) -> List[str]:
    """
    Get the list of countries to retrieve data for from command line arguments.
    Uses country_config for validation.
    """
    parser = argparse.ArgumentParser(description='Retrieve ENTSO-E historic price data')
    parser.add_argument('--countries', type=str, help='Comma-separated list of country codes (e.g., NL,DE,FR)')
    args, _ = parser.parse_known_args()
    if not args.countries:
        logger.error("No countries provided. Please provide at least one country code via --countries argument.")
        print_usage()
        sys.exit(1)
    countries = [country.strip().upper() for country in args.countries.split(',')]
    valid_countries = []
    for country in countries:
        if country_config and country in country_config:
            valid_countries.append(country)
        else:
            logger.warning(f"Invalid country code: {country}. Skipping.")
    if not valid_countries:
        logger.error("No valid country codes provided. Please provide at least one valid country code.")
        logger.error("Available country codes: " + ", ".join(sorted(country_config.keys())))
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

def load_country_config():
    config_path = os.path.join(os.path.dirname(__file__), 'country_config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

def retrieve_day_ahead_prices(start_date: datetime, end_date: datetime, api_key: str, country_code: str, country_config: dict) -> pd.DataFrame:
    """
    Retrieve day-ahead prices from ENTSO-E API for the specified time period and country.
    Uses domain_code from country_config.json.
    """
    logger.info(f"Retrieving day-ahead prices for {country_code} from {start_date.date()} to {end_date.date()}")
    try:
        from entsoe import EntsoePandasClient
        client = EntsoePandasClient(api_key=api_key)
        domain_code = country_config[country_code]['domain_code']
        prices = client.query_day_ahead_prices(
            domain_code,
            start=pd.Timestamp(start_date).tz_localize('UTC'),
            end=pd.Timestamp(end_date).tz_localize('UTC')
        )
        if isinstance(prices, pd.Series):
            df = prices.to_frame(name='price')
            df.reset_index(inplace=True)
            df.rename(columns={'index': 'datetime'}, inplace=True)
            df['country'] = country_code
            return df
        else:
            logger.error(f"Unexpected result format from entsoe-py client for {country_code}")
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error retrieving day-ahead prices for {country_code}: {str(e)}")
        return pd.DataFrame()

def retrieve_data_in_chunks(start_date: datetime, end_date: datetime, api_key: str, country_code: str, country_config: dict, chunk_days: int = 30) -> pd.DataFrame:
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
        
        df = retrieve_day_ahead_prices(current_start, current_end, api_key, country_code, country_config)
        if not df.empty:
            dfs.append(df)
        
        current_start = current_end
        
        # Sleep to avoid hitting API rate limits
        time.sleep(1)
    if dfs:
        return pd.concat(dfs).reset_index(drop=True)
    else:
        return pd.DataFrame()

def normalize_to_utc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize timestamps in DataFrame to UTC.
    
    Args:
        df (pd.DataFrame): DataFrame with timezone-aware timestamps
        
    Returns:
        pd.DataFrame: DataFrame with timestamps normalized to UTC
    """
    if df.empty:
        return df
    
    # Make a copy to avoid modifying the original DataFrame
    df_utc = df.copy()
    
    # Ensure datetime column is timezone-aware
    if df_utc['datetime'].dt.tz is None:
        # If timezone info is missing, assume it's in UTC
        df_utc['datetime'] = df_utc['datetime'].dt.tz_localize('UTC')
    else:
        # If timezone info is present, convert to UTC
        df_utc['datetime'] = df_utc['datetime'].dt.tz_convert('UTC')
    
    return df_utc

def convert_to_local_timezone(df: pd.DataFrame, country_code: str, country_config: dict) -> pd.DataFrame:
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
    
    timezone = country_config[country_code]['timezone']
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

def calculate_daily_metrics(df: pd.DataFrame, country_tax_configs: dict = None) -> pd.DataFrame:
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
    # This will use the timezone-aware datetime to extract the date
    df['date'] = df['datetime'].dt.date
    
    # Group by date and country
    grouped = df.groupby(['date', 'country'])
    
    # Calculate metrics
    min_prices = grouped['price'].min().reset_index()
    max_prices = grouped['price'].max().reset_index()
    avg_prices = grouped['price'].mean().reset_index()  # This calculates the arithmetic mean (weighted average)

    # Merge the metrics
    metrics = min_prices.rename(columns={'price': 'min_price_mwh'})
    metrics = metrics.merge(
        max_prices.rename(columns={'price': 'max_price_mwh'}),
        on=['date', 'country'],
        how='left'
    )
    metrics = metrics.merge(
        avg_prices.rename(columns={'price': 'weighted_avg_mwh'}),
        on=['date', 'country'],
        how='left'
    )

    # Add kWh columns by dividing MWh columns by 1000
    metrics['min_price_kwh'] = metrics['min_price_mwh'] / 1000
    metrics['max_price_kwh'] = metrics['max_price_mwh'] / 1000
    metrics['weighted_avg_kwh'] = metrics['weighted_avg_mwh'] / 1000

    # Add kwh_all_in_price column using tax config if provided
    if country_tax_configs is not None:
        def calc_all_in(row):
            country = row['country']
            tax_cfg = country_tax_configs.get(country)
            if not tax_cfg:
                return None
            price_per_kwh = row['weighted_avg_mwh'] / 1000
            energy_tax = tax_cfg.get('energy_tax', 0)
            renewable_energy_tax = tax_cfg.get('renewable_energy_tax', 0)
            vat_rate = tax_cfg.get('vat_rate', 0)
            pre_vat_price = price_per_kwh + energy_tax + renewable_energy_tax
            all_in_price_val = pre_vat_price * (1 + vat_rate)
            return round(all_in_price_val, 5)
        metrics['weighted_avg_kwh_all_in_price'] = metrics.apply(calc_all_in, axis=1)
        if 'kwh_all_in_price' in metrics.columns:
            metrics = metrics.drop(columns=['kwh_all_in_price'])

    # Add timezone info if available in the original DataFrame
    if 'timezone' in df.columns:
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

def get_timezone_suffix(country_code: str, use_local_time: bool, country_config: dict) -> str:
    """
    Get the timezone suffix for filenames based on the country and whether local time is used.
    
    Args:
        country_code (str): Country code to determine the timezone
        use_local_time (bool): Whether to use local timezone
        
    Returns:
        str: Timezone suffix for filenames
    """
    if use_local_time:
        timezone_name = country_config[country_code]['timezone']
        tz = pytz.timezone(timezone_name)
        now = datetime.now(tz)
        timezone_abbr = now.strftime('%Z')
        return f"local_{timezone_abbr}"
    else:
        return "utc"

def process_country_data(country_code: str, api_key: str, start_date: datetime, end_date: datetime, use_local_time: bool, country_tax_configs: dict = None, country_config: dict = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
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
    df = retrieve_data_in_chunks(start_date, end_date, api_key, country_code, country_config)
    
    if df.empty:
        logger.error(f"No data retrieved for {country_code}. Skipping.")
        return pd.DataFrame(), pd.DataFrame()
    
    # First, normalize all timestamps to UTC to ensure consistency
    df = normalize_to_utc(df)
    
    # Get timezone suffix for filenames
    timezone_suffix = get_timezone_suffix(country_code, use_local_time, country_config)
    
    # Convert to local timezone if requested
    if use_local_time:
        df = convert_to_local_timezone(df, country_code, country_config)
        timezone_info = f" (using {country_config[country_code]['timezone']} timezone)"
    else:
        timezone_info = " (using UTC timezone)"
    
    # Calculate metrics
    daily_metrics = calculate_daily_metrics(df, country_tax_configs=country_tax_configs)
    
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
    country_config = load_country_config()
    with open(os.path.join(os.path.dirname(__file__), 'country_config.json'), 'r') as f:
        country_tax_configs = json.load(f)
    countries = get_countries(country_config=country_config)
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
            metrics_df, raw_df = process_country_data(
                country_code, api_key, start_date, end_date, use_local_time,
                country_tax_configs=country_tax_configs, country_config=country_config
            )
            
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
                # Combine metrics
                combined_metrics = pd.concat(all_metrics)
                
                # Export combined metrics
                combined_metrics_filename = f"combined_price_metrics_{timezone_suffix}.csv"
                export_to_csv(combined_metrics, combined_metrics_filename)
            
            if all_raw_data:
                # Combine raw data
                combined_raw = pd.concat(all_raw_data)
                
                # Export combined raw data
                combined_raw_filename = f"combined_raw_prices_{timezone_suffix}.csv"
                export_to_csv(combined_raw, combined_raw_filename)
        
        logger.info("Data retrieval and processing completed successfully")
    
    except Exception as e:
        logger.error(f"Error during data retrieval and processing: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
