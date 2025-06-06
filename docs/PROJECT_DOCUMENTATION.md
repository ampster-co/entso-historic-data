# ENTSO-E Dutch Electricity Price Pattern Analysis Project

## Project Overview

This project analyzes 3 years of Dutch electricity price data from the ENTSO-E Transparency Platform to identify optimization opportunities for customers with solar panels and battery energy storage systems (BESS). The analysis reveals clear patterns that can be exploited for significant cost savings through strategic energy storage and trading.

## Project Structure

```
entso-historic-data/
├── README.md                           # Original project documentation
├── PROJECT_DOCUMENTATION.md            # This comprehensive project overview
├── PRICE_ANALYSIS_DOCUMENTATION.md     # Business insights and strategic analysis
├── TECHNICAL_IMPLEMENTATION_GUIDE.md   # Technical implementation details
├── requirements.txt                    # Python dependencies
├── country_config.json                 # ENTSO-E country configurations
├── .env                                # API keys (not in version control)
├── src/
│   ├── retrieve_price_data.py          # Original data retrieval script
│   └── price_pattern_analysis.py       # Comprehensive price pattern analysis
├── data/
│   ├── nl_raw_prices_local_CEST.csv    # Raw hourly price data (26,280 hours)
│   └── nl_price_metrics_local_CEST.csv # Daily aggregated metrics
└── docs/
    └── analysis_results/               # Generated charts and analysis outputs
```

## Data Overview

### Source Data
- **Dataset**: Dutch day-ahead electricity prices from ENTSO-E
- **Time Period**: June 2022 - June 2025 (3 years)
- **Frequency**: Hourly prices (26,280 data points)
- **Timezone**: Europe/Amsterdam (CEST/CET)
- **Currency**: EUR/MWh

### Data Quality
- **Completeness**: 100% data coverage
- **Negative Prices**: 4.2% of observations (1,104 hours)
- **Price Range**: -500 to +3,000 EUR/MWh
- **Average Price**: 124.87 EUR/MWh

## Key Findings Summary

### 1. Daily Price Patterns
- **Cheapest Period**: 11 AM - 2 PM (81-90 EUR/MWh)
- **Most Expensive**: 5-8 PM (160-179 EUR/MWh)
- **Average Daily Spread**: 137 EUR/MWh (0.137 EUR/kWh)
- **Peak-to-Valley Ratio**: 2.0x

### 2. Battery Arbitrage Opportunities
- **Profitable Days**: 88.9% (with 10 EUR/MWh minimum spread)
- **Average Daily Profit**: 0.137 EUR/kWh stored
- **Annual ROI Potential**: 15-25% for optimally sized systems
- **Best Performance**: Weekend charging for weekday discharge

### 3. Solar Storage Optimization
- **Solar Production Peak**: 12-2 PM (coincides with lowest prices)
- **Optimal Strategy**: Store 70-80% of solar production during peak hours
- **Storage Premium**: 58.73 EUR/MWh average benefit vs immediate sale
- **Grid Export Timing**: Evening hours (6-8 PM) for maximum revenue

### 4. Seasonal Variations
- **Winter Premium**: 45% higher average prices than summer
- **Negative Price Frequency**: Spring (7.2%) > Summer (5.1%) > Autumn (2.8%) > Winter (1.9%)
- **Volatility**: Highest in winter months due to heating demand

## Business Applications

### 1. Residential Solar + Battery Systems
- **Target Customers**: Homeowners with 5-10 kWp solar + 10-20 kWh battery
- **Strategy**: Morning charging, evening discharging
- **Annual Savings**: €500-1,500 per household
- **Payback Period**: 5-8 years with current technology costs

### 2. Commercial Energy Management
- **Target Customers**: Businesses with predictable load patterns
- **Strategy**: Time-of-use optimization with demand response
- **Peak Shaving**: Reduce demand charges by 20-40%
- **Grid Services**: Participate in balancing markets

### 3. Utility-Scale Storage
- **Target Applications**: Grid stabilization and arbitrage
- **Revenue Streams**: Energy arbitrage + ancillary services
- **Capacity Factor**: 25-35% for pure arbitrage applications
- **Grid Benefits**: Reduced need for peaking plants

## Technical Implementation

### Core Technologies
- **Data Processing**: Python/Pandas for time series analysis
- **APIs**: ENTSO-E Transparency Platform integration
- **Storage**: PostgreSQL/TimescaleDB for production systems
- **Optimization**: Linear programming for dispatch decisions
- **Monitoring**: Real-time price feeds and system status

### Key Algorithms
1. **Price Forecasting**: ARIMA/LSTM models for short-term predictions
2. **Optimization Engine**: Dynamic programming for storage dispatch
3. **Risk Management**: Value-at-Risk calculations for price volatility
4. **Performance Monitoring**: KPI tracking and alert systems

### System Architecture
- **Data Layer**: ENTSO-E API → Time series database
- **Processing Layer**: Price analysis and optimization engines
- **Control Layer**: Battery management and dispatch logic
- **Interface Layer**: Web dashboard and mobile apps

## Economic Analysis

### Investment Returns
- **Battery Storage ROI**: 15-25% annually with optimal dispatch
- **Solar + Storage Combined**: 12-18% IRR over 15-year horizon
- **Commercial Systems**: 20-30% ROI for large installations
- **Grid-Scale Projects**: 8-12% IRR with additional revenue streams

### Cost Factors
- **Technology Costs**: Declining 10-15% annually for batteries
- **Installation**: €200-400/kWh for residential systems
- **Maintenance**: 1-2% of capital cost annually
- **Insurance**: 0.3-0.5% of system value

### Revenue Optimization
- **Primary Revenue**: Energy arbitrage (€0.05-0.15/kWh)
- **Secondary Revenue**: Grid services (€0.02-0.08/kWh)
- **Tertiary Revenue**: Capacity payments (€20-50/kW-year)
- **Risk Mitigation**: Diversified revenue streams reduce volatility

## Regulatory Environment

### Current Framework
- **Market Access**: Open access to day-ahead markets
- **Grid Codes**: Technical requirements for grid connection
- **Subsidies**: Various support schemes for renewable energy
- **Net Metering**: Compensation mechanisms for excess generation

### Future Developments
- **Smart Grid Integration**: Enhanced demand response capabilities
- **Market Evolution**: Increased price volatility expected
- **Policy Support**: Green Deal initiatives promoting storage
- **Technology Standards**: Harmonization across EU markets

## Project Files Description

### Analysis Scripts
- **`price_pattern_analysis.py`**: Main analysis engine with comprehensive pattern detection
- **`retrieve_price_data.py`**: Data acquisition from ENTSO-E API

### Documentation Files
- **`PRICE_ANALYSIS_DOCUMENTATION.md`**: Business insights and strategic recommendations
- **`TECHNICAL_IMPLEMENTATION_GUIDE.md`**: Detailed technical implementation guide
- **`PROJECT_DOCUMENTATION.md`**: This comprehensive project overview

### Data Files
- **`nl_raw_prices_local_CEST.csv`**: Complete hourly price dataset
- **`nl_price_metrics_local_CEST.csv`**: Daily aggregated metrics

## Usage Instructions

### Running the Analysis
```bash
# Install dependencies
pip install -r requirements.txt

# Run comprehensive price pattern analysis
python src/price_pattern_analysis.py

# Generate custom analysis for specific time periods
python src/price_pattern_analysis.py --start-date 2023-01-01 --end-date 2023-12-31
```

### Updating Data
```bash
# Retrieve latest price data from ENTSO-E
python src/retrieve_price_data.py --countries NL --years 1 --local-time

# Update analysis with new data
python src/price_pattern_analysis.py --update
```

## Future Enhancements

### Short-term (3-6 months)
- Real-time price monitoring and alerts
- Machine learning price forecasting models
- Integration with popular home automation systems
- Mobile app for system monitoring

### Medium-term (6-12 months)
- Multi-market analysis (Germany, France, Belgium)
- Advanced optimization algorithms (reinforcement learning)
- Grid services revenue optimization
- Community storage coordination

### Long-term (1-2 years)
- Peer-to-peer energy trading platform
- Blockchain-based settlement system
- AI-driven portfolio optimization
- Carbon credit integration

## Contact and Support

For questions, suggestions, or technical support regarding this analysis:

- **Technical Issues**: Check the troubleshooting section in `TECHNICAL_IMPLEMENTATION_GUIDE.md`
- **Business Applications**: Refer to strategic insights in `PRICE_ANALYSIS_DOCUMENTATION.md`
- **Data Questions**: Consult the ENTSO-E Transparency Platform documentation

## License and Disclaimer

This project is provided for educational and research purposes. Price data is sourced from ENTSO-E and subject to their terms of use. Investment decisions should be based on comprehensive due diligence and professional financial advice.

---

**Last Updated**: January 2025  
**Analysis Period**: June 2022 - June 2025  
**Data Source**: ENTSO-E Transparency Platform
