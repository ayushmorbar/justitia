# JUSTITIA Setup Script for Windows PowerShell

Write-Host "🏛️ Setting up JUSTITIA environment..." -ForegroundColor Green

# Check Python version
$python_version = python --version 2>&1
if ($python_version -match "Python (\d+\.\d+)") {
    $version = [version]$matches[1]
    if ($version -lt [version]"3.10") {
        Write-Host "❌ Python 3.10 or higher required. Found: $($matches[1])" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Python $($matches[1]) detected" -ForegroundColor Green
}

# Create virtual environment
Write-Host "🐍 Creating Python virtual environment..." -ForegroundColor Yellow
python -m venv venv
& "venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "📦 Upgrading pip..." -ForegroundColor Yellow
pip install --upgrade pip

# Install dependencies
Write-Host "📚 Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Install project
Write-Host "🔧 Installing JUSTITIA..." -ForegroundColor Yellow
pip install -e .

# Check for Ollama
$ollama_installed = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollama_installed) {
    Write-Host "🤖 Please install Ollama manually from: https://ollama.ai/download" -ForegroundColor Yellow
} else {
    Write-Host "✅ Ollama already installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "🎉 Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To get started:" -ForegroundColor Cyan
Write-Host "  1. Activate virtual environment: venv\Scripts\Activate.ps1"
Write-Host "  2. Install Ollama if needed: https://ollama.ai/download"
Write-Host "  3. Pull model: ollama pull gpt-oss:20b"
Write-Host "  4. Run CLI: justitia --help"
Write-Host "  5. Run TUI: python run_tui.py"
Write-Host ""
Write-Host "🏆 Ready to build your winning hackathon project!" -ForegroundColor Green
