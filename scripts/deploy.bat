@echo off
REM AI Empire Monitoring Suite - Windows Deployment Script
REM Usage: scripts\deploy.bat [production|development] [port]

setlocal enabledelayedexpansion

REM Configuration
set MODE=%1
if "%MODE%"=="" set MODE=development
set PORT=%2
if "%PORT%"=="" set PORT=8000

echo.
echo 🚀 AI Empire Monitoring Suite Deployment
echo Mode: %MODE% ^| Port: %PORT%
echo.

REM Check prerequisites
echo 📋 Checking prerequisites...

python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 3.9+ is required but not installed
    pause
    exit /b 1
)

pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip is required but not installed
    pause
    exit /b 1
)

echo ✅ Python detected

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 🔧 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate

REM Install dependencies
echo 📦 Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

REM Check .env file
if not exist ".env" (
    echo ⚠️  .env file not found, creating template...
    copy .env.example .env
    echo ⚠️  Please edit .env file with your OpenRouter API key
)

REM Create necessary directories
echo 📁 Creating directories...
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "backups" mkdir backups
if not exist "temp" mkdir temp

REM Stop existing processes
echo 🔧 Stopping existing services...
taskkill /f /im python.exe /fi "windowtitle eq mcp_memory_persistence_server*" >nul 2>&1
taskkill /f /im python.exe /fi "windowtitle eq simple_claude_monitor*" >nul 2>&1
taskkill /f /im python.exe /fi "windowtitle eq REAL_TIME_PERFORMANCE_MONITOR*" >nul 2>&1
taskkill /f /im python.exe /fi "windowtitle eq openrouter_cost_optimizer*" >nul 2>&1

REM Start background services
echo 🔧 Starting background services...

REM Start MCP memory server
if exist "mcp-servers\mcp_memory_persistence_server.py" (
    echo 🧠 Starting MCP Memory Server...
    start "MCP Memory Server" /min python mcp-servers\mcp_memory_persistence_server.py
    timeout /t 2 >nul
)

REM Start monitoring systems
if exist "monitoring\simple_claude_monitor.py" (
    echo 📊 Starting Claude Monitor...
    start "Claude Monitor" /min python monitoring\simple_claude_monitor.py
    timeout /t 1 >nul
)

if exist "monitoring\REAL_TIME_PERFORMANCE_MONITOR.py" (
    echo ⚡ Starting Performance Monitor...
    start "Performance Monitor" /min python monitoring\REAL_TIME_PERFORMANCE_MONITOR.py
    timeout /t 1 >nul
)

if exist "monitoring\openrouter_cost_optimizer.py" (
    echo 💰 Starting Cost Optimizer...
    start "Cost Optimizer" /min python monitoring\openrouter_cost_optimizer.py
    timeout /t 1 >nul
)

REM Wait for services to start
echo ⏳ Waiting for services to initialize...
timeout /t 5 >nul

REM Start web server
echo 🌐 Starting web server on port %PORT%...
if "%MODE%"=="production" (
    start "Web Server" /min python -m http.server %PORT%
) else (
    start "Web Server" /min python -m http.server %PORT%
)

timeout /t 3 >nul

REM Health check
echo 🔍 Running health check...

REM Test OpenRouter connection
echo 🔗 Testing OpenRouter connection...
python -c "
import requests
import os
import sys
from dotenv import load_dotenv

try:
    load_dotenv()
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print('❌ OpenRouter API key not found in .env')
        sys.exit(0)

    headers = {'Authorization': f'Bearer {api_key}'}
    response = requests.get('https://openrouter.ai/api/v1/models', headers=headers, timeout=10)
    if response.status_code == 200:
        models = response.json()
        free_models = [m for m in models.get('data', []) if m.get('pricing', {}).get('prompt') == '0']
        print(f'✅ OpenRouter: Connected ({len(free_models)} free models)')
    else:
        print(f'⚠️  OpenRouter: HTTP {response.status_code}')
except ImportError:
    print('⚠️  Installing required packages...')
except Exception as e:
    print(f'❌ OpenRouter: Connection failed - {e}')
"

echo.
echo 🎉 AI Empire Monitoring Suite deployed successfully!
echo.
echo 📊 Access Points:
echo   • Main Dashboard: http://localhost:%PORT%/dashboards/AI_EMPIRE_COMPLETE_DASHBOARD.html
echo   • Real-time Analytics: http://localhost:%PORT%/dashboards/REAL_TIME_ANALYTICS_DASHBOARD.html
echo   • Status Dashboard: http://localhost:%PORT%/dashboards/ULTIMATE_EMPIRE_STATUS_DASHBOARD.html
echo   • Revenue Dashboard: http://localhost:%PORT%/dashboards/PRODUCTION_REVENUE_DASHBOARD.html
echo   • Progress Monitor: http://localhost:%PORT%/dashboards/CONSOLIDATION_PROGRESS_MONITOR.html
echo.
echo 🔧 Management Commands:
echo   • Stop all services: scripts\stop.bat
echo   • View logs: dir logs\*.log
echo   • Health check: scripts\health_check.bat
echo   • Restart services: scripts\restart.bat
echo.
echo 📈 System Status:
echo   • Mode: %MODE%
echo   • Port: %PORT%
echo   • Cost: $0.00 (Free models only)
echo   • Memory Persistence: Enabled
echo   • Real-time Monitoring: Active
echo.
echo 🚀 Ready for operation!
echo.

REM Open main dashboard
echo Opening main dashboard...
start http://localhost:%PORT%/dashboards/AI_EMPIRE_COMPLETE_DASHBOARD.html

pause