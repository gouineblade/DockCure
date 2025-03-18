#!/bin/bash

echo "🔍 Checking the virtual environment..."

# Check if the virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Error: The virtual environment does not exist. Run ./create_venv.sh first 🛠️"
    exit 1
fi

# Activate the virtual environment
source venv/bin/activate
echo "✅ Virtual environment activated 🐍"

# Check if pip is installed
if ! command -v pip &> /dev/null
then
    echo "❌ Error: pip is not installed. Try installing it with: python -m ensurepip"
    exit 1
fi

# Get the latest version of pip from PyPI
LATEST_PIP_VERSION=$(curl -s https://pypi.org/pypi/pip/json | jq -r '.info.version')
CURRENT_PIP_VERSION=$(pip --version | awk '{print $2}')

echo "🔄 Checking pip version..."

if [ "$LATEST_PIP_VERSION" != "$CURRENT_PIP_VERSION" ]; then
    echo "🚀 Updating pip (current version: $CURRENT_PIP_VERSION, latest version: $LATEST_PIP_VERSION)..."
    pip install --upgrade pip
    echo "✅ pip has been updated to version $(pip --version | awk '{print $2}') 🎉"
else
    echo "👌 pip is already up to date (version: $CURRENT_PIP_VERSION)."
fi

# Check and install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    pip freeze > installed_packages.txt
    if ! cmp -s <(sort installed_packages.txt) <(sort requirements.txt); then
        echo "📦 Installing dependencies from requirements.txt..."
        pip install -r requirements.txt
        echo "✅ Installation complete 🚀"
    else
        echo "👌 All dependencies are already installed."
    fi
    rm installed_packages.txt
else
    echo "⚠️ No requirements.txt file found. No installation performed."
fi
