#!/usr/bin/env python3
"""
ENTSO-E Historic Price Data Retriever - Runner Script for entsoe-py version

This script provides a simple interface to run the ENTSO-E data retriever using the entsoe-py library.

Features:
- User-friendly interface for retrieving ENTSO-E price data
- Supports multiple countries (specify with --countries flag)
- Supports loading API key from .env file or command line argument
- Supports custom date ranges (--start-date, --end-date, --years)
- Supports local timezone conversion with --local-time flag
- Displays information about output files

Usage:
    python run_entsoe_py.py [--api-key YOUR_API_KEY] --countries NL,DE,FR [--combined] [--local-time] --years 3
    python run_entsoe_py.py [--api-key YOUR_API_KEY] --countries NL,DE,FR [--combined] [--local-time] --years 5
    python run_entsoe_py.py [--api-key YOUR_API_KEY] --countries NL,DE,FR [--combined] [--local-time] --start-date 2020-01-01 --end-date 2022-12-31

Environment Variables:
    ENTSOE_API_KEY: Your ENTSO-E API key (can be set in .env file)
"""

import os
import sys
import logging
import argparse
import glob
from datetime import datetime, timedelta
from entso_py_retriever import (
    main as run_data_retriever,
    COUNTRY_CODES,
    get_countries,
    should_create_combined_files,
    should_use_local_time,
    get_date_range,
    print_usage,
    get_timezone_suffix
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_header(countries, combined, local_time, start_date, end_date, years):
    """
    Print a header for the script.
    
    Displays information about the script's purpose and functionality.
    
    Args:
        countries (list): List of country codes to display
        combined (bool): Whether combined files will be created
        local_time (bool): Whether local timezone will be used
        start_date (str): Start date for data retrieval (YYYY-MM-DD)
        end_date (str): End date for data retrieval (YYYY-MM-DD)
        years (int): Number of years to retrieve
    """
    print("\n" + "=" * 80)
    print(" ENTSO-E Historic Price Data Retriever (entsoe-py version) ".center(80, "="))
    print("=" * 80)
    print("\nThis script will retrieve historic electricity price data from ENTSO-E")
    
    if len(countries) == 1:
        print(f"for {countries[0]}", end="")
    else:
        country_list = ", ".join(countries[:-1]) + " and " + countries[-1]
        print(f"for {country_list}", end="")
    
    # Display date range information
    if start_date and end_date:
        print(f" from {start_date} to {end_date},", end="")
    elif years:
        print(f" for the last {years} years,", end="")
    else:
        print(" for the specified date range,", end="")
    
    print(" calculate daily metrics,")
    print("and export the results to CSV files.\n")
    print("This version uses the entsoe-py library for more reliable data retrieval.")
    print("It will only retrieve real data, with no fallback to sample data.\n")
    print("API Key can be provided via:")
    print("  1. Command line argument: --api-key YOUR_API_KEY")
    print("  2. Environment variable: ENTSOE_API_KEY")
    print("  3. .env file with ENTSOE_API_KEY=YOUR_API_KEY\n")
    print("Countries must be specified via:")
    print("  1. Command line argument: --countries NL,DE,FR\n")
    print("Date range can be specified via:")
    print("  1. Start and end dates: --start-date 2020-01-01 --end-date 2022-12-31")
    print("  2. Number of years: --years 5")
    print("  Note: You must specify either --years or both --start-date and --end-date\n")
    
    if local_time:
        print("Timestamps will be converted to local timezone for each country.")
        print("Output filenames will include the timezone information.\n")
    else:
        print("All timestamps will be in UTC timezone.")
        print("Output filenames will include 'utc' to indicate this.\n")
    
    if len(countries) > 1:
        if combined:
            print("Combined files will be created for all countries.\n")
        else:
            print("Only individual country files will be created.")
            print("Use --combined flag to create combined files for all countries.\n")
    
    print("Available country codes:")
    
    # Display available country codes in a formatted way
    country_list = list(COUNTRY_CODES.keys())
    country_list.sort()
    
    # Display in columns
    col_width = 4  # Width of each column (3 chars for code + 1 space)
    cols = 10      # Number of columns
    
    for i in range(0, len(country_list), cols):
        row = country_list[i:i+cols]
        print("  " + "".join(f"{code:<{col_width}}" for code in row))
    
    print("")

def print_footer(countries, combined, use_local_time):
    """
    Print a footer with information about the output files.
    
    Args:
        countries (list): List of country codes to check for output files
        combined (bool): Whether combined files were created
        use_local_time (bool): Whether local timezone was used
    """
    print("\n" + "=" * 80)
    print(" Results ".center(80, "="))
    print("=" * 80)
    print("\nThe following output files have been created:")
    
    files_found = False
    
    # Check for country-specific files
    for country in countries:
        country_lower = country.lower()
        timezone_suffix = get_timezone_suffix(country, use_local_time)
        metrics_file = f"data/{country_lower}_price_metrics_{timezone_suffix}.csv"
        raw_file = f"data/{country_lower}_raw_prices_{timezone_suffix}.csv"
        
        for file in [metrics_file, raw_file]:
            if os.path.exists(file):
                size = os.path.getsize(file) / 1024  # Size in KB
                print(f" - {file} ({size:.2f} KB)")
                files_found = True
    
    # Check for combined files
    if combined and len(countries) > 1:
        timezone_suffix = "utc"
        if use_local_time:
            timezone_suffix = "local_mixed"  # Since we have multiple countries with different timezones
            
        for file in [f"data/combined_price_metrics_{timezone_suffix}.csv", f"data/combined_raw_prices_{timezone_suffix}.csv"]:
            if os.path.exists(file):
                size = os.path.getsize(file) / 1024  # Size in KB
                print(f" - {file} ({size:.2f} KB)")
                files_found = True
    
    if not files_found:
        print(" No output files were created. Check the logs for errors.")
    
    print("\nYou can now analyze this data in your preferred spreadsheet application.")
    print("=" * 80 + "\n")

def main():
    """
    Main function to run the data retriever.
    
    This function:
    1. Displays information about the script
    2. Asks for user confirmation before proceeding
    3. Runs the data retriever
    4. Displays information about the output files
    """
    # Check if help is requested
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print_usage()
        sys.exit(0)
    
    # Parse command line arguments (these will be passed to entso_py_retriever.py)
    parser = argparse.ArgumentParser(description='Run ENTSO-E data retriever')
    parser.add_argument('--api-key', type=str, help='ENTSO-E API key')
    parser.add_argument('--countries', type=str, help='Comma-separated list of country codes (e.g., NL,DE,FR)')
    parser.add_argument('--combined', action='store_true', help='Create combined files for all countries')
    parser.add_argument('--local-time', action='store_true', help='Convert timestamps to local timezone for each country')
    parser.add_argument('--start-date', type=str, help='Start date for data retrieval (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date for data retrieval (YYYY-MM-DD)')
    parser.add_argument('--years', type=int, help='Number of years to retrieve (from today)')
    args = parser.parse_args()
    
    # Check if countries are provided
    if not args.countries:
        logger.error("No countries provided. Please provide at least one country code via --countries argument.")
        print_usage()
        sys.exit(1)
    
    # Check if date range is provided
    if not args.years and not args.start_date:
        logger.error("No date range provided. Please provide a date range using --start-date and --end-date, or --years.")
        print_usage()
        sys.exit(1)
    
    # Get the list of countries
    countries = get_countries()
    
    # Check if combined files should be created
    combined = should_create_combined_files()
    
    # Check if local timezone should be used
    use_local_time = should_use_local_time()
    
    # Format dates for display
    start_date_str = args.start_date if args.start_date else None
    end_date_str = args.end_date if args.end_date else None
    
    print_header(countries, combined, use_local_time, start_date_str, end_date_str, args.years)
    
    # Ask user if they want to proceed
    response = input("Do you want to proceed with data retrieval? (y/n): ")
    if response.lower() != 'y':
        print("Operation cancelled.")
        return
    
    print("\nStarting data retrieval. This may take some time...\n")
    
    # Run the data retriever
    run_data_retriever()
    
    # Print footer with information about the output files
    print_footer(countries, combined, use_local_time)

if __name__ == "__main__":
    main()
