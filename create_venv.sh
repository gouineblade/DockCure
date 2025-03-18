#!/bin/bash

echo "🔍 Checking if the virtual environment exists..."

# Check if the virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚙️ Creating the virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created successfully 🐍"
else
    echo "⚠️ Virtual environment already exists."
fi
