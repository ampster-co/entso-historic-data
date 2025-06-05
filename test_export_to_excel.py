#!/usr/bin/env python3
"""
Test script for ENTSO-E Excel Export

This script tests the functionality of the Excel export script.
It verifies that CSV files can be exported to Excel format correctly.

Usage:
    python test_export_to_excel.py
"""

import unittest
import os
import pandas as pd
import logging
import tempfile
import shutil
from datetime import datetime
from export_to_excel import main as run_excel_export

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestExcelExport(unittest.TestCase):
    """
    Test cases for Excel export functionality.
    """

    def setUp(self):
        """
        Set up test environment.
        Create temporary directory and test CSV files.
        """
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        
        # Change to the temporary directory
        os.chdir(self.test_dir)
        
        # Create test CSV files
        self.create_test_csv_files()

    def tearDown(self):
        """
        Clean up test environment.
        Remove temporary directory and test files.
        """
        # Change back to the original directory
        os.chdir(self.original_dir)
        
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_dir)

    def create_test_csv_files(self):
        """
        Create test CSV files for testing the Excel export.
        """
        # Create a test metrics CSV file
        metrics_df = pd.DataFrame({
            'date': ['2022-01-01', '2022-01-02', '2022-01-03'],
            'country': ['NL', 'NL', 'NL'],
            'min_price': [10, 20, 30],
            'max_price': [100, 200, 300],
            'weighted_avg': [50, 100, 150],
            'timezone': ['Europe/Amsterdam', 'Europe/Amsterdam', 'Europe/Amsterdam']
        })
        metrics_df.to_csv('nl_price_metrics_local_CEST.csv', index=False)
        
        # Create a test raw prices CSV file
        dates = pd.date_range(start='2022-01-01', periods=24, freq='h')
        prices = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240]
        
        raw_df = pd.DataFrame({
            'datetime': dates,
            'price': prices,
            'country': ['NL'] * 24,
            'timezone': ['Europe/Amsterdam'] * 24,
            'date': ['2022-01-01'] * 24
        })
        raw_df.to_csv('nl_raw_prices_local_CEST.csv', index=False)

    def test_excel_export(self):
        """
        Test that CSV files can be exported to Excel format.
        """
        logger.info("Testing Excel export...")
        
        # Run the Excel export
        run_excel_export()
        
        # Find the Excel file (it has a timestamp in the filename)
        excel_files = [f for f in os.listdir('.') if f.endswith('.xlsx')]
        self.assertTrue(excel_files, "Excel file should be created")
        
        excel_file = excel_files[0]
        
        # Check that the Excel file exists
        self.assertTrue(os.path.exists(excel_file), f"File {excel_file} should exist")
        
        # Read the Excel file
        xls = pd.ExcelFile(excel_file)
        
        # Check that the Excel file has the expected sheets
        expected_sheets = ['Summary', 'Daily Metrics (Local Time)', 'Raw Prices (Local Time)']
        for sheet in expected_sheets:
            self.assertIn(sheet, xls.sheet_names, f"Excel file should have sheet: {sheet}")
        
        # Check the content of the metrics sheet
        metrics_df = pd.read_excel(excel_file, sheet_name='Daily Metrics (Local Time)')
        
        # Check that the DataFrame has the expected columns
        expected_columns = ['date', 'country', 'min_price', 'max_price', 'weighted_avg', 'timezone']
        for column in expected_columns:
            self.assertIn(column, metrics_df.columns, f"DataFrame should have column: {column}")
        
        # Check that the DataFrame has the expected values
        self.assertEqual(metrics_df['min_price'].iloc[0], 10, "Minimum price should be 10")
        self.assertEqual(metrics_df['max_price'].iloc[0], 100, "Maximum price should be 100")
        self.assertEqual(metrics_df['weighted_avg'].iloc[0], 50, "Weighted average should be 50")
        
        logger.info("Excel export test passed")

def run_tests():
    """
    Run the test suite.
    """
    logger.info("Running Excel export tests...")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    logger.info("All tests completed")

if __name__ == "__main__":
    run_tests()
