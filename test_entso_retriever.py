#!/usr/bin/env python3
"""
Test script for ENTSO-E Historic Price Data Retriever

This script tests the functionality of the ENTSO-E data retriever.
It verifies that the API connection works, data can be retrieved,
and metrics can be calculated correctly.

Usage:
    python test_entso_retriever.py
"""

import unittest
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import dotenv
from entso_py_retriever import (
    COUNTRY_CODES,
    get_api_key,
    get_countries,
    get_date_range,
    retrieve_day_ahead_prices,
    calculate_daily_metrics,
    export_to_csv
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestEntsoeRetriever(unittest.TestCase):
    """
    Test cases for ENTSO-E data retriever.
    """
    
    def setUp(self):
        """
        Set up test environment.
        """
        # Try to load API key from .env file
        dotenv.load_dotenv()
        self.api_key = os.environ.get('ENTSOE_API_KEY')
        
        # Set up test parameters
        self.country_code = 'NL'  # Netherlands
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=7)  # Last 7 days
        
        # Create test arguments
        sys.argv = ['test_entso_retriever.py', '--countries', 'NL', '--years', '1']
    
    def test_country_codes(self):
        """
        Test that country codes are valid.
        """
        logger.info("Testing country codes...")
        
        # Check that COUNTRY_CODES is not empty
        self.assertGreater(len(COUNTRY_CODES), 0, "COUNTRY_CODES should not be empty")
        
        # Check that NL is in COUNTRY_CODES
        self.assertIn('NL', COUNTRY_CODES, "NL should be in COUNTRY_CODES")
        
        # Check that the domain code for NL is correct
        self.assertEqual(COUNTRY_CODES['NL'], '10YNL----------L', "Domain code for NL is incorrect")
        
        logger.info("Country codes test passed")
    
    def test_get_countries(self):
        """
        Test that get_countries returns the correct countries.
        """
        logger.info("Testing get_countries...")
        
        # Test with required countries argument
        sys.argv = ['test_entso_retriever.py', '--countries', 'NL', '--years', '1']
        countries = get_countries()
        self.assertEqual(countries, ['NL'], "Country should be NL")
        
        # Test with multiple countries
        sys.argv = ['test_entso_retriever.py', '--countries', 'NL,DE,FR', '--years', '1']
        countries = get_countries()
        self.assertEqual(countries, ['NL', 'DE', 'FR'], "Countries should be NL, DE, FR")
        
        # Test with invalid country code
        sys.argv = ['test_entso_retriever.py', '--countries', 'XX', '--years', '1']
        with self.assertRaises(SystemExit):
            countries = get_countries()
        
        # Test with no countries provided
        sys.argv = ['test_entso_retriever.py', '--years', '1']
        with self.assertRaises(SystemExit):
            countries = get_countries()
        
        # Reset arguments
        sys.argv = ['test_entso_retriever.py', '--countries', 'NL', '--years', '1']
        
        logger.info("get_countries test passed")
    
    def test_get_date_range(self):
        """
        Test that get_date_range returns the correct date range.
        """
        logger.info("Testing get_date_range...")
        
        # Test with years argument
        sys.argv = ['test_entso_retriever.py', '--countries', 'NL', '--years', '1']
        start_date, end_date = get_date_range()
        expected_start_date = datetime.now() - timedelta(days=365)
        
        # Check that the dates are within 1 day of each other (to account for test execution time)
        self.assertLess(
            abs((start_date - expected_start_date).total_seconds()),
            86400,  # 1 day in seconds
            "Start date should be 1 year ago"
        )
        
        # Test with start_date and end_date arguments
        test_start_date = '2022-01-01'
        test_end_date = '2022-12-31'
        sys.argv = ['test_entso_retriever.py', '--countries', 'NL', '--start-date', test_start_date, '--end-date', test_end_date]
        start_date, end_date = get_date_range()
        
        self.assertEqual(
            start_date.strftime('%Y-%m-%d'),
            test_start_date,
            "Start date should be 2022-01-01"
        )
        self.assertEqual(
            end_date.strftime('%Y-%m-%d'),
            test_end_date,
            "End date should be 2022-12-31"
        )
        
        # Test with no date range provided
        sys.argv = ['test_entso_retriever.py', '--countries', 'NL']
        with self.assertRaises(SystemExit):
            start_date, end_date = get_date_range()
        
        # Reset arguments
        sys.argv = ['test_entso_retriever.py', '--countries', 'NL', '--years', '1']
        
        logger.info("get_date_range test passed")
    
    def test_api_connection(self):
        """
        Test that the API connection works.
        """
        logger.info("Testing API connection...")
        
        # Skip test if no API key is provided
        if not self.api_key:
            logger.warning("Skipping API connection test: No API key provided")
            self.skipTest("No API key provided")
        
        # Test retrieving data for a short period
        df = retrieve_day_ahead_prices(
            self.start_date,
            self.end_date,
            self.api_key,
            self.country_code
        )
        
        # Check that the DataFrame is not empty
        self.assertFalse(df.empty, "DataFrame should not be empty")
        
        # Check that the DataFrame has the expected columns
        expected_columns = ['datetime', 'price', 'country']
        for column in expected_columns:
            self.assertIn(column, df.columns, f"DataFrame should have column: {column}")
        
        # Check that the country column has the correct value
        self.assertEqual(df['country'].iloc[0], self.country_code, f"Country should be {self.country_code}")
        
        logger.info("API connection test passed")
    
    def test_calculate_metrics(self):
        """
        Test that metrics are calculated correctly.
        """
        logger.info("Testing metric calculation...")
        
        # Create a test DataFrame
        dates = pd.date_range(start='2022-01-01', periods=24, freq='H')
        prices = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240]
        
        df = pd.DataFrame({
            'datetime': dates,
            'price': prices,
            'country': 'NL'
        })
        
        # Calculate metrics
        metrics = calculate_daily_metrics(df)
        
        # Check that the metrics DataFrame is not empty
        self.assertFalse(metrics.empty, "Metrics DataFrame should not be empty")
        
        # Check that the metrics DataFrame has the expected columns
        expected_columns = [
            'date', 'country',
            'min_price_mwh', 'max_price_mwh', 'weighted_avg_mwh',
            'min_price_kwh', 'max_price_kwh', 'weighted_avg_kwh'
        ]
        for column in expected_columns:
            self.assertIn(column, metrics.columns, f"Metrics DataFrame should have column: {column}")
        
        # Check that the metrics are calculated correctly
        self.assertEqual(metrics['min_price_mwh'].iloc[0], 10, "Minimum price (MWh) should be 10")
        self.assertEqual(metrics['max_price_mwh'].iloc[0], 240, "Maximum price (MWh) should be 240")
        self.assertEqual(metrics['weighted_avg_mwh'].iloc[0], 125, "Weighted average (MWh) should be 125")
        self.assertAlmostEqual(metrics['min_price_kwh'].iloc[0], 0.01, places=5, msg="Minimum price (kWh) should be 0.01")
        self.assertAlmostEqual(metrics['max_price_kwh'].iloc[0], 0.24, places=5, msg="Maximum price (kWh) should be 0.24")
        self.assertAlmostEqual(metrics['weighted_avg_kwh'].iloc[0], 0.125, places=5, msg="Weighted average (kWh) should be 0.125")
        
        logger.info("Metric calculation test passed")
    
    def test_export_to_csv(self):
        """
        Test that data can be exported to CSV.
        """
        logger.info("Testing CSV export...")
        
        # Create a test DataFrame
        df = pd.DataFrame({
            'date': ['2022-01-01', '2022-01-02', '2022-01-03'],
            'country': ['NL', 'NL', 'NL'],
            'min_price_mwh': [10, 20, 30],
            'max_price_mwh': [100, 200, 300],
            'weighted_avg_mwh': [50, 100, 150],
            'min_price_kwh': [0.01, 0.02, 0.03],
            'max_price_kwh': [0.1, 0.2, 0.3],
            'weighted_avg_kwh': [0.05, 0.1, 0.15]
        })
        
        # Export to CSV
        test_filename = 'test_export.csv'
        export_to_csv(df, test_filename)
        
        # Check that the file exists
        self.assertTrue(os.path.exists(test_filename), f"File {test_filename} should exist")
        
        # Check that the file has the correct content
        df_read = pd.read_csv(test_filename)
        
        # Check that the DataFrame has the expected columns
        expected_columns = [
            'date', 'country',
            'min_price_mwh', 'max_price_mwh', 'weighted_avg_mwh',
            'min_price_kwh', 'max_price_kwh', 'weighted_avg_kwh'
        ]
        for column in expected_columns:
            self.assertIn(column, df_read.columns, f"DataFrame should have column: {column}")
        
        # Check that the DataFrame has the expected values
        self.assertEqual(df_read['min_price_mwh'].iloc[0], 10, "Minimum price (MWh) should be 10")
        self.assertEqual(df_read['max_price_mwh'].iloc[0], 100, "Maximum price (MWh) should be 100")
        self.assertEqual(df_read['weighted_avg_mwh'].iloc[0], 50, "Weighted average (MWh) should be 50")
        self.assertAlmostEqual(df_read['min_price_kwh'].iloc[0], 0.01, places=5, msg="Minimum price (kWh) should be 0.01")
        self.assertAlmostEqual(df_read['max_price_kwh'].iloc[0], 0.1, places=5, msg="Maximum price (kWh) should be 0.1")
        self.assertAlmostEqual(df_read['weighted_avg_kwh'].iloc[0], 0.05, places=5, msg="Weighted average (kWh) should be 0.05")
        
        # Clean up
        os.remove(test_filename)
        
        logger.info("CSV export test passed")

def run_tests():
    """
    Run the test suite.
    """
    logger.info("Running ENTSO-E data retriever tests...")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    logger.info("All tests completed")

if __name__ == "__main__":
    run_tests()
