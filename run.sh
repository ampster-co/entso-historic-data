#!/bin/bash
# ENTSO-E Historic Price Data Retriever - Runner Script for Unix/Linux/macOS

# Function to display the menu
display_menu() {
    clear
    echo "=============================================================="
    echo "      ENTSO-E Historic Price Data Retriever - Main Menu       "
    echo "=============================================================="
    echo ""
    echo "This script will help you retrieve historic electricity price"
    echo "data from the ENTSO-E Transparency Platform."
    echo ""
    echo "Please select an option:"
    echo ""
    echo "1. Retrieve data for Netherlands (last 3 years)"
    echo "2. Retrieve data for Netherlands (last 5 years)"
    echo "3. Retrieve data for multiple countries (last 3 years)"
    echo "4. Retrieve data for multiple countries (last 5 years)"
    echo "5. Retrieve data for custom date range"
    echo "6. Retrieve data with local timezone conversion"
    echo "7. Exit"
    echo ""
    echo "Note: You need an ENTSO-E API key to use this script."
    echo "You can set it in the .env file or provide it when prompted."
    echo ""
    read -p "Enter your choice (1-7): " choice
}

# Function to get API key
get_api_key() {
    # Check if API key is in .env file
    if [ -f .env ] && grep -q "ENTSOE_API_KEY" .env; then
        echo "API key found in .env file."
        return
    fi
    
    # Prompt for API key
    echo ""
    echo "Please enter your ENTSO-E API key:"
    read -p "> " api_key
    
    # Save API key to .env file
    echo "ENTSOE_API_KEY=$api_key" > .env
    echo "API key saved to .env file."
}

# Function to get countries
get_countries() {
    echo ""
    echo "Please enter the country codes separated by commas (e.g., NL,DE,FR):"
    read -p "> " countries
    echo ""
}

# Function to get date range
get_date_range() {
    echo ""
    echo "Please enter the start date (YYYY-MM-DD):"
    read -p "> " start_date
    
    echo ""
    echo "Please enter the end date (YYYY-MM-DD):"
    read -p "> " end_date
    echo ""
}

# Function to ask about local timezone
ask_local_timezone() {
    echo ""
    echo "Do you want to convert timestamps to local timezone for each country? (y/n)"
    read -p "> " use_local_time
    echo ""
    
    if [[ $use_local_time == "y" || $use_local_time == "Y" ]]; then
        local_time_flag="--local-time"
    else
        local_time_flag=""
    fi
}

# Function to ask about combined files
ask_combined_files() {
    echo ""
    echo "Do you want to create combined files for all countries? (y/n)"
    read -p "> " create_combined
    echo ""
    
    if [[ $create_combined == "y" || $create_combined == "Y" ]]; then
        combined_flag="--combined"
    else
        combined_flag=""
    fi
}

# Main loop
while true; do
    display_menu
    
    case $choice in
        1)
            get_api_key
            ask_local_timezone
            python entso_py_retriever.py --countries NL --years 3 $local_time_flag
            ;;
        2)
            get_api_key
            ask_local_timezone
            python entso_py_retriever.py --countries NL --years 5 $local_time_flag
            ;;
        3)
            get_api_key
            get_countries
            ask_combined_files
            ask_local_timezone
            python entso_py_retriever.py --countries $countries --years 3 $combined_flag $local_time_flag
            ;;
        4)
            get_api_key
            get_countries
            ask_combined_files
            ask_local_timezone
            python entso_py_retriever.py --countries $countries --years 5 $combined_flag $local_time_flag
            ;;
        5)
            get_api_key
            get_countries
            get_date_range
            ask_combined_files
            ask_local_timezone
            python entso_py_retriever.py --countries $countries --start-date $start_date --end-date $end_date $combined_flag $local_time_flag
            ;;
        6)
            get_api_key
            get_countries
            echo ""
            echo "How many years of data do you want to retrieve?"
            read -p "> " years
            echo ""
            ask_combined_files
            python entso_py_retriever.py --countries $countries --years $years $combined_flag --local-time
            ;;
        7)
            echo ""
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo ""
            echo "Invalid choice. Please try again."
            sleep 2
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
done
