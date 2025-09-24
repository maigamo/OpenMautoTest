# OpenMautoTest Windows PowerShell Script
# Alternative to Makefile for Windows environment

param(
    [Parameter(Mandatory=$false)]
    [string]$Target = "help"
)

function Show-Help {
    Write-Host "OpenMautoTest Available Commands:" -ForegroundColor Green
    Write-Host "  .\make.ps1 install      - Install project dependencies"
    Write-Host "  .\make.ps1 test         - Run all tests"
    Write-Host "  .\make.ps1 check-config - Check configuration files"
    Write-Host "  .\make.ps1 meta-up      - Start Metabase services"
    Write-Host "  .\make.ps1 migrate      - Execute database migrations"
    Write-Host "  .\make.ps1 lint         - Run code quality checks"
    Write-Host "  .\make.ps1 format       - Format code"
    Write-Host "  .\make.ps1 setup-dev    - Setup development environment"
    Write-Host "  .\make.ps1 clean        - Clean temporary files"
    Write-Host "  .\make.ps1 check-env    - Check environment dependencies"
}

function Install-Dependencies {
    Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Installing Playwright browsers..." -ForegroundColor Yellow
        playwright install
        Write-Host "Checking Node.js version..." -ForegroundColor Yellow
        try {
            node --version
        } catch {
            Write-Host "Warning: Node.js not found, mini-program automation will be unavailable" -ForegroundColor Red
        }
    }
}

function Run-Tests {
    Write-Host "Running test suite..." -ForegroundColor Yellow
    python -m pytest -v --tb=short --alluredir=output/allure-results
}

function Check-Config {
    Write-Host "Checking project configuration..." -ForegroundColor Yellow
    try {
        python -c "from configs.settings import SETTINGS; print('Config check passed:', SETTINGS)"
    } catch {
        Write-Host "Config check failed" -ForegroundColor Red
    }
}

function Start-Metabase {
    Write-Host "Starting Metabase and PostgreSQL services..." -ForegroundColor Yellow
    docker-compose -f docker-compose.meta.yml up -d
    Write-Host "Metabase will start at http://localhost:3000" -ForegroundColor Green
}

function Run-Migration {
    Write-Host "Executing database migrations..." -ForegroundColor Yellow
    alembic upgrade head
}

function Run-Lint {
    Write-Host "Running code quality checks..." -ForegroundColor Yellow
    flake8 common configs db drivers orchestrator llm --max-line-length=88 --exclude=__pycache__,migrations
    mypy common configs db drivers orchestrator llm --ignore-missing-imports
}

function Format-Code {
    Write-Host "Formatting code..." -ForegroundColor Yellow
    black common configs db drivers orchestrator llm
    isort common configs db drivers orchestrator llm
}

function Setup-Dev {
    Write-Host "Setting up development environment..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        if (-not (Test-Path ".env")) {
            Copy-Item ".env.example" ".env"
            Write-Host "Created .env file, please modify configuration as needed" -ForegroundColor Green
        } else {
            Write-Host ".env file already exists" -ForegroundColor Yellow
        }
    }
}

function Clean-Temp {
    Write-Host "Cleaning temporary files..." -ForegroundColor Yellow
    Get-ChildItem -Path . -Recurse -Name "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -Name "__pycache__" -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Cleanup completed" -ForegroundColor Green
}

function Check-Environment {
    Write-Host "Checking environment dependencies..." -ForegroundColor Yellow
    Write-Host "Python version:" -ForegroundColor Cyan
    python --version
    Write-Host "Node.js version:" -ForegroundColor Cyan
    try { node --version } catch { Write-Host "Node.js not installed" -ForegroundColor Red }
    Write-Host "Docker version:" -ForegroundColor Cyan
    try { docker --version } catch { Write-Host "Docker not installed" -ForegroundColor Red }
}

# Main logic
switch ($Target.ToLower()) {
    "help" { Show-Help }
    "install" { Install-Dependencies }
    "test" { Run-Tests }
    "check-config" { Check-Config }
    "meta-up" { Start-Metabase }
    "migrate" { Run-Migration }
    "lint" { Run-Lint }
    "format" { Format-Code }
    "setup-dev" { Setup-Dev }
    "clean" { Clean-Temp }
    "check-env" { Check-Environment }
    default { 
        Write-Host "Unknown command: $Target" -ForegroundColor Red
        Show-Help 
    }
}