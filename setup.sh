#!/bin/bash

echo "🚀 Starting setup process..."

# Check if grype is installed
echo "🔍 Checking if grype is installed..."
if ! command -v grype &> /dev/null
then
    echo "💿 Grype not found. Downloading and installing..."
    curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
    echo "✅ Grype has been installed successfully!"
else
    echo "✅ Grype is already installed. Skipping installation."
fi

# Run create_venv.sh
echo "🔧 Creating virtual environment..."
bash create_venv.sh

# Run activate_venv.sh
echo "🔥 Activating virtual environment and installing dependencies..."
bash activate_venv.sh

echo "✅ Setup completed successfully! 🎉"
