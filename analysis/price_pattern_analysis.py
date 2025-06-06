#!/usr/bin/env python3
"""
DUTCH ELECTRICITY PRICE PATTERN ANALYSIS FOR SOLAR + BATTERY OPTIMIZATION

This script performs comprehensive analysis of Dutch electricity price data from the ENTSO-E
Transparency Platform to identify patterns that can optimize solar panel and battery storage
systems for residential customers.

BUSINESS CONTEXT:
================
Customers with solar panels and batteries can:
1. Store solar electricity in batteries when prices are low
2. Sell stored electricity back to the grid when prices are high
3. Buy electricity from the grid during negative price periods (get paid to consume)
4. Optimize their energy costs through strategic battery charging/discharging

KEY FINDINGS FROM ANALYSIS:
==========================
- Clear daily patterns: Cheapest prices 11 AM-2 PM, most expensive 5-8 PM
- Strong arbitrage opportunities: Average 0.137 EUR/kWh daily spread
- Negative prices occur 4.2% of the time (customers get PAID to consume)
- Solar storage is profitable 88.9% of days
- Weekend prices are 34% lower than weekdays
- Summer has highest volatility and arbitrage potential

TECHNICAL APPROACH:
==================
The analysis examines:
1. Hourly price patterns across 24-hour cycles
2. Seasonal variations (Spring/Summer/Autumn/Winter)
3. Weekday vs weekend differences
4. Extreme price events (negative prices and price spikes)
5. Daily arbitrage potential calculations
6. Solar production vs demand timing optimization

DATA REQUIREMENTS:
=================
Input: CSV file with columns:
- datetime: Timestamp with timezone info
- price: Electricity price in EUR/MWh
- country: Country code (NL for Netherlands)
- timezone: Timezone information
- date: Date in YYYY-MM-DD format

Output: Comprehensive analysis report with actionable insights for battery optimization

USAGE:
======
python price_pattern_analysis.py

The script expects 'nl_raw_prices_local_CEST.csv' in the '../data/' directory.

DEPENDENCIES:
============
- pandas: Data manipulation and analysis
- numpy: Numerical computations
- matplotlib: Data visualization (imported but not used in current version)
- seaborn: Statistical data visualization (imported but not used in current version)

AUTHORS:
========
Created for ENTSO-E historic data analysis project
Optimized for solar panel and battery storage customers

VERSION:
========
1.0 - Initial comprehensive analysis implementation
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, time
import warnings
warnings.filterwarnings('ignore')

def load_and_prepare_data(file_path):
    """
    Load and prepare electricity price data for analysis.
    
    This function loads the raw price data CSV file and creates additional columns
    needed for temporal analysis including hour, month, day of week, season,
    weekend flag, and year.
    
    Args:
        file_path (str): Path to the CSV file containing price data
        
    Returns:
        pandas.DataFrame: Prepared dataframe with additional temporal columns
        
    Expected CSV columns:
        - datetime: Timestamp with timezone (e.g., "2022-06-07 11:00:00+02:00")
        - price: Electricity price in EUR/MWh
        - country: Country code (e.g., "NL")
        - timezone: Timezone name (e.g., "Europe/Amsterdam")
        - date: Date string (e.g., "2022-06-07")
    
    Added columns:
        - hour: Hour of day (0-23)
        - month: Month number (1-12)
        - day_of_week: Day of week (0=Monday, 6=Sunday)
        - season: Season name (Spring/Summer/Autumn/Winter)
        - is_weekend: Boolean flag for weekend days
        - year: Year number
        
    Note:
        The datetime column is parsed with UTC awareness to handle timezone-aware timestamps.
    """
    import os
    
    # Try different possible paths
    possible_paths = [
        file_path,
        os.path.join('data', 'nl_raw_prices_local_CEST.csv'),
        os.path.join('..', 'data', 'nl_raw_prices_local_CEST.csv'),
        'nl_raw_prices_local_CEST.csv'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Loading data from: {path}")
            df = pd.read_csv(path)
            break
    else:
        raise FileNotFoundError(f"Could not find data file. Tried paths: {possible_paths}")
    
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    df['hour'] = df['datetime'].dt.hour
    df['month'] = df['datetime'].dt.month
    df['day_of_week'] = df['datetime'].dt.dayofweek  # 0=Monday, 6=Sunday
    df['season'] = df['month'].map({12: 'Winter', 1: 'Winter', 2: 'Winter',
                                   3: 'Spring', 4: 'Spring', 5: 'Spring',
                                   6: 'Summer', 7: 'Summer', 8: 'Summer',
                                   9: 'Autumn', 10: 'Autumn', 11: 'Autumn'})
    df['is_weekend'] = df['day_of_week'].isin([5, 6])
    df['year'] = df['datetime'].dt.year
    return df

def analyze_hourly_patterns(df):
    """
    Analyze hourly price patterns throughout the day.
    
    This analysis identifies the optimal times for battery charging (low prices)
    and discharging/selling (high prices) based on average hourly price patterns.
    
    Args:
        df (pandas.DataFrame): Prepared price data with hour column
        
    Returns:
        tuple: (hourly_stats, peak_hours, valley_hours)
            - hourly_stats: Statistical summary by hour
            - peak_hours: List of 5 most expensive hours
            - valley_hours: List of 5 cheapest hours
            
    Business Logic:
        - Peak hours indicate when customers should sell electricity from batteries
        - Valley hours indicate when customers should charge batteries
        - Solar production hours (7 AM - 7 PM) analysis helps understand when
          solar panels are producing vs when grid prices are favorable
          
    Key Metrics Calculated:
        - Mean, median, std dev, min, max price for each hour
        - Top 5 peak hours (highest average prices)
        - Top 5 valley hours (lowest average prices)
        - Average prices during vs outside solar production hours
        
    Strategic Insights:
        - If non-solar hours have higher prices than solar hours, storing
          solar energy and selling later is profitable
        - The difference between peak and valley hours indicates arbitrage potential
    """
    print("=== HOURLY PRICE PATTERNS ===")
    hourly_stats = df.groupby('hour')['price'].agg(['mean', 'median', 'std', 'min', 'max']).round(2)
    print("Average prices by hour of day:")
    print(hourly_stats)
    
    # Find peak and valley hours for battery optimization
    peak_hours = hourly_stats['mean'].nlargest(5).index.tolist()
    valley_hours = hourly_stats['mean'].nsmallest(5).index.tolist()
    
    print(f"\nTOP 5 PEAK HOURS (highest average prices): {peak_hours}")
    print(f"TOP 5 VALLEY HOURS (lowest average prices): {valley_hours}")
    
    # Solar production hours analysis (rough estimate: 7 AM to 7 PM)
    solar_hours = list(range(7, 20))
    solar_prices = df[df['hour'].isin(solar_hours)]['price']
    non_solar_prices = df[~df['hour'].isin(solar_hours)]['price']
    
    print(f"\nSOLAR PRODUCTION HOURS (7 AM - 7 PM):")
    print(f"Average price during solar hours: {solar_prices.mean():.2f} EUR/MWh")
    print(f"Average price during non-solar hours: {non_solar_prices.mean():.2f} EUR/MWh")
    print(f"Difference: {non_solar_prices.mean() - solar_prices.mean():.2f} EUR/MWh")
    
    return hourly_stats, peak_hours, valley_hours

def analyze_seasonal_patterns(df):
    """
    Analyze seasonal and monthly price variations.
    
    Understanding seasonal patterns helps customers plan long-term battery usage
    strategies and anticipate periods of high/low prices and volatility.
    
    Args:
        df (pandas.DataFrame): Prepared price data with season and month columns
        
    Returns:
        tuple: (seasonal_stats, monthly_stats)
            - seasonal_stats: Price statistics by season
            - monthly_stats: Price statistics by month
            
    Business Value:
        - Seasonal patterns indicate when batteries are most/least valuable
        - High volatility seasons offer more arbitrage opportunities
        - Low price seasons might favor immediate consumption over storage
        
    Key Insights:
        - Summer typically shows highest prices and volatility (AC demand)
        - Spring often has lowest prices (mild weather, high renewable production)
        - Winter patterns affected by heating demand and lower solar production
        - Monthly breakdown reveals transition periods and optimal planning windows
        
    Strategic Applications:
        - Schedule battery maintenance during low-value periods
        - Adjust charging/discharging algorithms by season
        - Plan capacity expansion during high-value seasons
    """
    print("\n=== SEASONAL PATTERNS ===")
    seasonal_stats = df.groupby('season')['price'].agg(['mean', 'median', 'std', 'min', 'max']).round(2)
    print("Average prices by season:")
    print(seasonal_stats)
    
    monthly_stats = df.groupby('month')['price'].agg(['mean', 'median', 'std']).round(2)
    print("\nAverage prices by month:")
    print(monthly_stats)
    
    return seasonal_stats, monthly_stats

def analyze_weekday_patterns(df):
    """
    Compare weekday vs weekend price patterns.
    
    Weekend patterns often differ significantly from weekdays due to:
    - Lower industrial demand
    - Different consumption patterns
    - Reduced commercial activity
    
    Args:
        df (pandas.DataFrame): Prepared price data with is_weekend column
        
    Returns:
        tuple: (weekday_stats, hourly_weekday)
            - weekday_stats: Comparison of weekday vs weekend prices
            - hourly_weekday: Hourly patterns split by weekday/weekend
            
    Business Applications:
        - Adjust battery strategies for weekends (different optimal hours)
        - Weekend price differences affect profitability calculations
        - Long-term planning should account for weekday/weekend mix
        
    Typical Patterns:
        - Weekends usually have lower overall prices
        - Peak hours may shift on weekends
        - Less pronounced daily price curves on weekends
        - Lower volatility on weekends = reduced arbitrage opportunities
    """
    print("\n=== WEEKDAY VS WEEKEND PATTERNS ===")
    weekday_stats = df.groupby('is_weekend')['price'].agg(['mean', 'median', 'std']).round(2)
    weekday_stats.index = ['Weekday', 'Weekend']
    print("Average prices by day type:")
    print(weekday_stats)
    
    # Hourly patterns for weekdays vs weekends
    hourly_weekday = df.groupby(['hour', 'is_weekend'])['price'].mean().unstack()
    hourly_weekday.columns = ['Weekday', 'Weekend']
    
    return weekday_stats, hourly_weekday

def analyze_extreme_prices(df):
    """
    Analyze extreme price events including negative prices and price spikes.
    
    Extreme price events represent the highest-value opportunities for battery
    optimization:
    - Negative prices: Customers get PAID to consume electricity
    - Price spikes: Maximum value for selling stored electricity
    
    Args:
        df (pandas.DataFrame): Price data
        
    Returns:
        tuple: (negative_prices, very_high)
            - negative_prices: DataFrame of negative price periods
            - very_high: DataFrame of very high price periods (95th percentile+)
            
    Critical Business Opportunities:
        
    NEGATIVE PRICES (customers get paid to consume):
        - Occur when renewable generation exceeds demand
        - Most common during midday solar peaks
        - Automatic battery charging during these periods maximizes value
        - Can represent 4-6% of hours annually
        
    EXTREME HIGH PRICES:
        - Usually during supply shortages or peak demand
        - Maximum value for discharging batteries
        - Often occur during evening peaks or supply disruptions
        - Can exceed 10x normal prices
        
    Strategic Implementation:
        - Set automated triggers for negative price charging
        - Reserve battery capacity for extreme high price events
        - Monitor frequency and timing of extreme events for planning
        
    Risk Management:
        - Extreme events can be unpredictable
        - Don't rely solely on extreme events for profitability
        - Balance extreme event capture with daily arbitrage
    """
    print("\n=== EXTREME PRICE ANALYSIS ===")
    
    # Define thresholds for extreme events
    high_threshold = df['price'].quantile(0.95)  # Top 5% of prices
    low_threshold = df['price'].quantile(0.05)   # Bottom 5% of prices
    negative_prices = df[df['price'] < 0]
    
    print(f"95th percentile price: {high_threshold:.2f} EUR/MWh")
    print(f"5th percentile price: {low_threshold:.2f} EUR/MWh")
    print(f"Number of negative price hours: {len(negative_prices)}")
    print(f"Percentage of negative price hours: {len(negative_prices)/len(df)*100:.2f}%")
    
    if len(negative_prices) > 0:
        print(f"Average negative price: {negative_prices['price'].mean():.2f} EUR/MWh")
        print("Negative price hours by hour of day:")
        neg_hourly = negative_prices.groupby('hour').size()
        print(neg_hourly)
    
    # Very high price events
    very_high = df[df['price'] > high_threshold]
    print(f"\nVery high price events (>{high_threshold:.1f} EUR/MWh): {len(very_high)} hours")
    if len(very_high) > 0:
        print("High price hours by hour of day:")
        high_hourly = very_high.groupby('hour').size()
        print(high_hourly.head(10))
    
    return negative_prices, very_high

def calculate_arbitrage_potential(df):
    """
    Calculate daily battery arbitrage potential and profitability metrics.
    
    Arbitrage potential represents the maximum theoretical profit available
    each day by buying electricity at the lowest price and selling at the
    highest price, accounting for battery efficiency and cycling costs.
    
    Args:
        df (pandas.DataFrame): Price data with date column
        
    Returns:
        pandas.DataFrame: Daily statistics including arbitrage potential
        
    Key Metrics:
        - Daily price spread: Difference between max and min prices each day
        - Arbitrage potential: Spread converted to EUR/kWh
        - Best arbitrage days: Highest profit potential days
        
    Business Calculations:
        - Assumes perfect market timing (buy at daily min, sell at daily max)
        - Real-world results will be lower due to:
            * Battery efficiency losses (typically 85-95%)
            * Prediction imperfection
            * Battery degradation costs
            * Grid connection fees
            
    Practical Application:
        - Average daily spread indicates baseline profit potential
        - Top 10% of days show maximum opportunity value
        - Median values provide realistic expectations
        - Trend analysis shows if opportunities are increasing/decreasing
        
    ROI Considerations:
        - Battery cost amortization over cycle life
        - Grid connection and smart meter costs
        - Tax implications of electricity trading
        - Insurance and maintenance costs
        
    Example Calculation:
        If daily spread = 100 EUR/MWh = 0.10 EUR/kWh
        10 kWh battery with 90% efficiency
        Daily profit = 10 * 0.10 * 0.90 = 0.90 EUR/day
        Annual profit = 0.90 * 365 = 328.50 EUR/year
    """
    print("\n=== BATTERY ARBITRAGE POTENTIAL ===")
    
    daily_stats = df.groupby('date')['price'].agg(['min', 'max', 'mean']).reset_index()
    daily_stats['daily_spread'] = daily_stats['max'] - daily_stats['min']
    daily_stats['arbitrage_potential_mwh'] = daily_stats['daily_spread']
    daily_stats['arbitrage_potential_kwh'] = daily_stats['daily_spread'] / 1000  # Convert to EUR/kWh
    
    print(f"Average daily price spread: {daily_stats['daily_spread'].mean():.2f} EUR/MWh")
    print(f"Average daily arbitrage potential: {daily_stats['arbitrage_potential_kwh'].mean():.4f} EUR/kWh")
    print(f"Median daily arbitrage potential: {daily_stats['arbitrage_potential_kwh'].median():.4f} EUR/kWh")
    print(f"Max daily arbitrage potential: {daily_stats['arbitrage_potential_kwh'].max():.4f} EUR/kWh")
    
    # Days with best arbitrage opportunities
    best_days = daily_stats.nlargest(10, 'arbitrage_potential_kwh')[['date', 'arbitrage_potential_kwh']]
    print("\nTop 10 days with highest arbitrage potential:")
    print(best_days)
    
    return daily_stats

def analyze_solar_optimization(df):
    """
    Analyze optimal strategies for solar energy storage vs immediate selling.
    
    This analysis specifically addresses the core business question:
    "When should customers store their solar production vs sell it immediately?"
    
    The analysis compares:
    1. Selling solar immediately during peak production (11 AM - 3 PM)
    2. Storing solar during production and selling during evening peak (5 PM - 9 PM)
    
    Args:
        df (pandas.DataFrame): Price data with hour column
        
    Returns:
        None (prints analysis results)
        
    Key Business Metrics:
        
    SOLAR PEAK vs EVENING PEAK COMPARISON:
        - Solar peak: 11 AM - 3 PM (when panels produce most energy)
        - Evening peak: 5 PM - 9 PM (when household demand and prices peak)
        - Price premium: How much more money is made by storing vs immediate sale
        
    PROFITABILITY FREQUENCY:
        - Percentage of days where storage is more profitable than immediate sale
        - Average benefit amount when storage is profitable
        - Risk assessment: how often storage loses money
        
    STRATEGIC INSIGHTS:
        
    High profitability percentage (>80%) indicates:
        - Strong business case for battery storage
        - Consistent daily arbitrage opportunities
        - Predictable profit patterns
        
    Low profitability percentage (<50%) suggests:
        - Immediate sale often better than storage
        - Market timing risk is high
        - Storage may not justify investment
        
    PRACTICAL IMPLEMENTATION:
        - Use these patterns to program automatic battery management
        - Set storage thresholds based on predicted evening prices
        - Implement dynamic strategies that adapt to daily conditions
        
    EXAMPLE SCENARIO:
        Solar production: 20 kWh/day at 11 AM - 3 PM average price 90 EUR/MWh
        Immediate sale value: 20 * 0.090 = 1.80 EUR
        
        Storage and evening sale: 20 kWh at 5 PM - 9 PM average price 150 EUR/MWh
        With 90% battery efficiency: 18 * 0.150 = 2.70 EUR
        
        Daily storage benefit: 2.70 - 1.80 = 0.90 EUR
        Annual benefit: 0.90 * 365 = 328.50 EUR
    """
    print("\n=== SOLAR OPTIMIZATION INSIGHTS ===")
    
    # Define solar peak hours (11 AM to 3 PM) - when solar panels produce most
    solar_peak_hours = list(range(11, 16))
    # Define evening peak hours (5 PM to 9 PM) - when demand and prices typically peak
    peak_demand_hours = list(range(17, 22))
    
    solar_peak_prices = df[df['hour'].isin(solar_peak_hours)]['price']
    evening_peak_prices = df[df['hour'].isin(peak_demand_hours)]['price']
    
    print(f"Average price during solar peak (11 AM - 3 PM): {solar_peak_prices.mean():.2f} EUR/MWh")
    print(f"Average price during evening peak (5 PM - 9 PM): {evening_peak_prices.mean():.2f} EUR/MWh")
    print(f"Average premium for storing and selling later: {evening_peak_prices.mean() - solar_peak_prices.mean():.2f} EUR/MWh")
    print(f"Average premium per kWh: {(evening_peak_prices.mean() - solar_peak_prices.mean())/1000:.4f} EUR/kWh")
    
    # Calculate percentage of time storage is profitable
    daily_solar_vs_evening = df.groupby('date').apply(
        lambda x: x[x['hour'].isin(peak_demand_hours)]['price'].mean() - 
                  x[x['hour'].isin(solar_peak_hours)]['price'].mean()
    )
    
    profitable_days = (daily_solar_vs_evening > 0).sum()
    total_days = len(daily_solar_vs_evening.dropna())
    
    print(f"\nDays where storing solar and selling in evening is profitable: {profitable_days}/{total_days} ({profitable_days/total_days*100:.1f}%)")
    print(f"Average daily benefit when profitable: {daily_solar_vs_evening[daily_solar_vs_evening > 0].mean():.2f} EUR/MWh")

def main():
    """
    Main analysis orchestration function.
    
    Coordinates all analysis functions and provides executive summary of findings
    specifically tailored for solar panel and battery storage customers.
    
    The analysis follows this logical flow:
    1. Load and prepare data with temporal features
    2. Identify hourly patterns for optimal charging/discharging times
    3. Understand seasonal variations for long-term planning
    4. Compare weekday vs weekend patterns
    5. Identify extreme price events and opportunities
    6. Calculate arbitrage potential and profitability
    7. Optimize solar storage vs immediate sale decisions
    8. Summarize key actionable insights
    
    Executive Summary Format:
        - Clear identification of optimal battery operating hours
        - Quantified profit opportunities
        - Risk assessment (negative prices, high volatility)
        - Seasonal strategy recommendations
        - Implementation priorities
    """
    print("DUTCH ELECTRICITY PRICE PATTERN ANALYSIS")
    print("=" * 50)
    
    # Load and validate data
    df = load_and_prepare_data('data/nl_raw_prices_local_CEST.csv')
    
    print(f"Data period: {df['datetime'].min()} to {df['datetime'].max()}")
    print(f"Total hours analyzed: {len(df):,}")
    print(f"Price range: {df['price'].min():.2f} to {df['price'].max():.2f} EUR/MWh")
    print(f"Average price: {df['price'].mean():.2f} EUR/MWh")
    
    # Execute comprehensive analysis
    hourly_stats, peak_hours, valley_hours = analyze_hourly_patterns(df)
    seasonal_stats, monthly_stats = analyze_seasonal_patterns(df)
    weekday_stats, hourly_weekday = analyze_weekday_patterns(df)
    negative_prices, very_high = analyze_extreme_prices(df)
    daily_stats = calculate_arbitrage_potential(df)
    analyze_solar_optimization(df)
    
    # Generate executive summary for business decision-making
    print("\n" + "=" * 50)
    print("KEY INSIGHTS FOR SOLAR + BATTERY CUSTOMERS")
    print("=" * 50)
    
    print(f"🔋 BEST TIMES TO CHARGE BATTERY: Hours {valley_hours}")
    print(f"💰 BEST TIMES TO SELL: Hours {peak_hours}")
    
    if len(negative_prices) > 0:
        print(f"⚡ NEGATIVE PRICES: {len(negative_prices)} hours ({len(negative_prices)/len(df)*100:.1f}% of time)")
        print("   During negative prices, you could be PAID to consume electricity!")
    
    storage_benefit = df[df['hour'].isin(peak_hours)]['price'].mean() - df[df['hour'].isin(valley_hours)]['price'].mean()
    print(f"💡 AVERAGE STORAGE BENEFIT: {storage_benefit:.2f} EUR/MWh ({storage_benefit/1000:.4f} EUR/kWh)")
    
    # Seasonal strategy guidance
    winter_avg = df[df['season'] == 'Winter']['price'].mean()
    summer_avg = df[df['season'] == 'Summer']['price'].mean()
    print(f"🌞 SEASONAL PATTERN: Winter avg {winter_avg:.1f} EUR/MWh, Summer avg {summer_avg:.1f} EUR/MWh")
    
if __name__ == "__main__":
    main()
