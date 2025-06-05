@echo off
REM ENTSO-E Historic Price Data Retriever - Runner Script for Windows

:menu
cls
echo ==============================================================
echo       ENTSO-E Historic Price Data Retriever - Main Menu       
echo ==============================================================
echo.
echo This script will help you retrieve historic electricity price
echo data from the ENTSO-E Transparency Platform.
echo.
echo Please select an option:
echo.
echo 1. Retrieve data for Netherlands (last 3 years)
echo 2. Retrieve data for Netherlands (last 5 years)
echo 3. Retrieve data for multiple countries (last 3 years)
echo 4. Retrieve data for multiple countries (last 5 years)
echo 5. Retrieve data for custom date range
echo 6. Retrieve data with local timezone conversion
echo 7. Export data to Excel format
echo 8. Exit
echo.
echo Note: You need an ENTSO-E API key to use this script.
echo You can set it in the .env file or provide it when prompted.
echo.
set /p choice=Enter your choice (1-8):

if "%choice%"=="1" goto option1
if "%choice%"=="2" goto option2
if "%choice%"=="3" goto option3
if "%choice%"=="4" goto option4
if "%choice%"=="5" goto option5
if "%choice%"=="6" goto option6
if "%choice%"=="7" goto export_excel
if "%choice%"=="8" goto exit
echo.
echo Invalid choice. Please try again.
timeout /t 2 >nul
goto menu

:get_api_key
REM Check if API key is in .env file
if exist .env (
    findstr /C:"ENTSOE_API_KEY" .env >nul
    if not errorlevel 1 (
        echo API key found in .env file.
        goto :eof
    )
)

REM Prompt for API key
echo.
echo Please enter your ENTSO-E API key:
set /p api_key=^> 

REM Save API key to .env file
echo ENTSOE_API_KEY=%api_key%> .env
echo API key saved to .env file.
goto :eof

:get_countries
echo.
echo Please enter the country codes separated by commas (e.g., NL,DE,FR):
set /p countries=^> 
echo.
goto :eof

:get_date_range
echo.
echo Please enter the start date (YYYY-MM-DD):
set /p start_date=^> 

echo.
echo Please enter the end date (YYYY-MM-DD):
set /p end_date=^> 
echo.
goto :eof

:ask_local_timezone
echo.
echo Do you want to convert timestamps to local timezone for each country? (y/n)
set /p use_local_time=^> 
echo.

if /i "%use_local_time%"=="y" (
    set local_time_flag=--local-time
) else (
    set local_time_flag=
)
goto :eof

:ask_combined_files
echo.
echo Do you want to create combined files for all countries? (y/n)
set /p create_combined=^> 
echo.

if /i "%create_combined%"=="y" (
    set combined_flag=--combined
) else (
    set combined_flag=
)
goto :eof

:option1
call :get_api_key
call :ask_local_timezone
python entso_py_retriever.py --countries NL --years 3 %local_time_flag%
goto continue

:option2
call :get_api_key
call :ask_local_timezone
python entso_py_retriever.py --countries NL --years 5 %local_time_flag%
goto continue

:option3
call :get_api_key
call :get_countries
call :ask_combined_files
call :ask_local_timezone
python entso_py_retriever.py --countries %countries% --years 3 %combined_flag% %local_time_flag%
goto continue

:option4
call :get_api_key
call :get_countries
call :ask_combined_files
call :ask_local_timezone
python entso_py_retriever.py --countries %countries% --years 5 %combined_flag% %local_time_flag%
goto continue

:option5
call :get_api_key
call :get_countries
call :get_date_range
call :ask_combined_files
call :ask_local_timezone
python entso_py_retriever.py --countries %countries% --start-date %start_date% --end-date %end_date% %combined_flag% %local_time_flag%
goto continue

:option6
call :get_api_key
call :get_countries
echo.
echo How many years of data do you want to retrieve?
set /p years=^> 
echo.
call :ask_combined_files
python entso_py_retriever.py --countries %countries% --years %years% %combined_flag% --local-time
goto continue

:continue
echo.
pause
goto menu

:export_excel
echo.
echo Exporting data to Excel format...
python export_to_excel.py
goto continue

:exit
echo.
echo Exiting...
exit /b 0
