@echo off

echo ====================================
echo Starting Data Harvester Scraper
echo ====================================

cd /d %~dp0

echo.
echo Activating virtual environment...
call .venv\Scripts\activate

echo.
echo Installing missing dependencies (if any)...
pip install -r requirements.txt

echo.
echo Starting scraper engine...
python main.py

echo.
echo ====================================
echo Scraping finished
echo ====================================

pause
