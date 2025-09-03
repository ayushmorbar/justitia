#!/bin/bash
# JUSTITIA Setup Script for Unix systems

set -e

echo "🏛️ Setting up JUSTITIA environment..."

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $required_version or higher required. Found: $python_version"
    exit 1
fi

echo "✅ Python $python_version detected"

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Install project in development mode
echo "🔧 Installing JUSTITIA in development mode..."
pip install -e .

# Check for Ollama
if ! command -v ollama &> /dev/null; then
    echo "🤖 Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
else
    echo "✅ Ollama already installed"
fi

# Pull gpt-oss model
echo "📥 Pulling gpt-oss model (this may take a few minutes)..."
ollama pull gpt-oss:20b

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To get started:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run CLI: justitia --help"
echo "  3. Run TUI: python run_tui.py"
echo "  4. Create samples: justitia create-samples content-moderation"
echo ""
echo "🏆 Ready to build your winning hackathon project!"
