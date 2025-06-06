#!/bin/bash
# ENTSO-E Data Analysis - Quick Start Script

echo "ENTSO-E Dutch Electricity Price Analysis"
echo "========================================"
echo ""

# Check if required packages are installed
if ! python -c "import pandas, numpy, matplotlib, seaborn" 2>/dev/null; then
    echo "⚠️  Installing required packages..."
    pip install pandas numpy matplotlib seaborn
    echo ""
fi

# Check if data file exists
if [ ! -f "data/nl_raw_prices_local_CEST.csv" ]; then
    echo "❌ Data file not found: data/nl_raw_prices_local_CEST.csv"
    echo "   Run data retrieval first:"
    echo "   python src/entso_py_retriever.py --countries NL --local-time --years 3"
    exit 1
fi

echo "📊 Running price pattern analysis..."
echo ""
python analysis/price_pattern_analysis.py

echo ""
echo "✅ Analysis complete!"
echo ""
echo "📚 For more information, see:"
echo "   - docs/QUICK_REFERENCE_GUIDE.md (key findings)"
echo "   - docs/BUSINESS_ANALYSIS_DOCUMENTATION.md (strategic insights)"
echo "   - docs/TECHNICAL_IMPLEMENTATION_GUIDE.md (implementation details)"
