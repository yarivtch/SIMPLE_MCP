#!/bin/bash

echo "Installing SIMPLE MCP dependencies..."
echo

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo
echo "✅ Installation complete!"
echo
echo "To run the project:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Start MCP server: python api_server.py"
echo "3. Start gateway: python mcp_gateway.py"
echo