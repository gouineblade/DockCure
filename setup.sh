#!/bin/bash

echo "🚀 Starting setup process..."

# Check if grype is installed
if ! command -v grype &> /dev/null; then
    echo "💿 Grype not found. Installing..."

    # Check if brew is installed
    if command -v brew &> /dev/null; then
        echo "📦 Homebrew detected. Installing Grype via Homebrew..."
        brew install anchore/grype/grype
    else
        echo "🔽 Homebrew not found. Installing Grype manually..."
        URL="https://github.com/anchore/grype/releases/latest/download/grype-darwin-amd64"
        curl -sSfL "$URL" -o grype
        chmod +x grype
        sudo mv grype /usr/local/bin/
    fi

    echo "✅ Grype has been installed successfully!"
else
    echo "✅ Grype is already installed. Skipping installation."
fi

# Check and install Tkinter based on the package manager
echo "🔍 Checking if Tkinter is installed..."

# Function to install Tkinter with apt (Ubuntu/Debian)
install_with_apt() {
    echo "Using apt package manager to install tkinter..."
    sudo apt-get update
    sudo apt-get install -y python3-venv
}

# Check the package manager and install Tkinter
if command -v apt &> /dev/null; then
    install_with_apt
    echo "✅ Tkinter installation complete!"
fi

# Run create_venv.sh
echo "🔧 Creating virtual environment..."
bash create_venv.sh

# Run activate_venv.sh
echo "🔥 Activating virtual environment and installing dependencies..."
bash activate_venv.sh

echo "✅ Setup completed successfully! 🎉"
