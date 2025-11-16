@echo off
echo ========================================
echo Personal Research Concierge Agent - CLI
echo ========================================
echo.

call venv\Scripts\activate.bat

echo Ready! Use like this:
echo.
echo   python main.py "Your research question here"
echo.
echo Example:
echo   python main.py "What is quantum computing?"
echo.
echo For interactive mode:
echo   python main.py
echo.

cmd /k
