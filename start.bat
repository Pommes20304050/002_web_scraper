@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo   Web Scraper - Setup / Start
echo   ============================
echo.

pip install -r requirements.txt -q
if errorlevel 1 (
    echo [!] pip install fehlgeschlagen.
    pause
    exit /b 1
)

echo.
python -m src.main --no-banner --help
echo.
echo   Beispiele:
echo     python -m src.main scrape   https://example.com
echo     python -m src.main crawl    https://example.com --max-pages 20 --export all
echo     python -m src.main sitemap  https://example.com
echo     python -m src.main info     https://example.com
echo.
echo   Tippe Befehle direkt ein. STRG+C zum Beenden.
echo.

cmd /k "cd /d %~dp0"
