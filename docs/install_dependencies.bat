@echo off
echo Installing SIMPLE MCP dependencies...
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt

echo.
echo Installation complete!
echo.

REM Test dependencies
echo Testing dependencies...
python test_dependencies.py
echo.

echo To run the project:
echo 1. Activate virtual environment: venv\Scripts\activate.bat
echo 2. Start MCP server: python api_server.py  
echo 3. Start gateway: python mcp_gateway.py
echo 4. Open browser: http://localhost:3000
echo.
pause