@echo off
REM Activate the virtual environment
cd /d "%~dp0"
call venv\Scripts\activate.bat

REM Start mock exchanges
start cmd /k "python mock_exchanges.py"

REM Wait a moment for the exchanges to start
timeout /t 3 /nobreak > nul

REM Start the GUI application
python gui.py
