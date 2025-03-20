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

# Check and install Tkinter based on the package manager
echo "🔍 Checking if Tkinter is installed..."

# Function to install Tkinter with apt (Ubuntu/Debian)
install_with_apt() {
    echo "Using apt package manager to install tkinter..."
    sudo apt-get update
    sudo apt-get install -y python3-tk python3-venv
}

# Function to install Tkinter with pacman (Arch Linux)
install_with_pacman() {
    echo "Using pacman package manager to install tkinter..."
    sudo pacman -Syu --noconfirm tk
}

# Function to install Tkinter with dnf (Fedora)
install_with_dnf() {
    echo "Using dnf package manager to install tkinter..."
    sudo dnf install -y python3-tkinter
}

# Check the package manager and install Tkinter
if command -v apt &> /dev/null; then
    install_with_apt
elif command -v pacman &> /dev/null; then
    install_with_pacman
elif command -v dnf &> /dev/null; then
    install_with_dnf
else
    echo "⚠️ Unsupported package manager. Please install tkinter manually."
    exit 1
fi

echo "✅ Tkinter installation complete!"


# Run create_venv.sh
echo "🔧 Creating virtual environment..."
bash create_venv.sh

# Run activate_venv.sh
echo "🔥 Activating virtual environment and installing dependencies..."
bash activate_venv.sh

echo "✅ Setup completed successfully! 🎉"
