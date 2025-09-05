#!/bin/bash
# AI Empire Monitoring Suite - Automated Deployment Script
# Usage: ./scripts/deploy.sh [production|development]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MODE=${1:-development}
PORT=${2:-8000}

echo -e "${BLUE}🚀 AI Empire Monitoring Suite Deployment${NC}"
echo -e "${YELLOW}Mode: $MODE | Port: $PORT${NC}"
echo ""

# Check prerequisites
echo -e "${BLUE}📋 Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3.9+ is required but not installed${NC}"
    exit 1
fi

if ! command -v pip &> /dev/null; then
    echo -e "${RED}❌ pip is required but not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [[ $(echo "$PYTHON_VERSION < 3.9" | bc) -eq 1 ]]; then
    echo -e "${RED}❌ Python 3.9+ required, found $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python $PYTHON_VERSION detected${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${BLUE}🔧 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${BLUE}📦 Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Check OpenRouter API key
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found, creating template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env file with your OpenRouter API key${NC}"
fi

# Create necessary directories
echo -e "${BLUE}📁 Creating directories...${NC}"
mkdir -p logs data backups temp

# Set permissions
chmod +x scripts/*.sh
chmod +x scripts/*.py

# Start background services
echo -e "${BLUE}🔧 Starting background services...${NC}"

# Kill existing processes if any
pkill -f "mcp_memory_persistence_server.py" 2>/dev/null || true
pkill -f "simple_claude_monitor.py" 2>/dev/null || true
pkill -f "REAL_TIME_PERFORMANCE_MONITOR.py" 2>/dev/null || true
pkill -f "openrouter_cost_optimizer.py" 2>/dev/null || true

# Start MCP memory server
if [ -f "mcp-servers/mcp_memory_persistence_server.py" ]; then
    echo -e "${BLUE}🧠 Starting MCP Memory Server...${NC}"
    python mcp-servers/mcp_memory_persistence_server.py > logs/mcp_server.log 2>&1 &
    MCP_PID=$!
    echo "MCP Server PID: $MCP_PID"
fi

# Start monitoring systems
if [ -f "monitoring/simple_claude_monitor.py" ]; then
    echo -e "${BLUE}📊 Starting Claude Monitor...${NC}"
    python monitoring/simple_claude_monitor.py > logs/claude_monitor.log 2>&1 &
    CLAUDE_PID=$!
    echo "Claude Monitor PID: $CLAUDE_PID"
fi

if [ -f "monitoring/REAL_TIME_PERFORMANCE_MONITOR.py" ]; then
    echo -e "${BLUE}⚡ Starting Performance Monitor...${NC}"
    python monitoring/REAL_TIME_PERFORMANCE_MONITOR.py > logs/performance_monitor.log 2>&1 &
    PERF_PID=$!
    echo "Performance Monitor PID: $PERF_PID"
fi

if [ -f "monitoring/openrouter_cost_optimizer.py" ]; then
    echo -e "${BLUE}💰 Starting Cost Optimizer...${NC}"
    python monitoring/openrouter_cost_optimizer.py > logs/cost_optimizer.log 2>&1 &
    COST_PID=$!
    echo "Cost Optimizer PID: $COST_PID"
fi

# Wait for services to start
echo -e "${BLUE}⏳ Waiting for services to initialize...${NC}"
sleep 5

# Start web server
echo -e "${BLUE}🌐 Starting web server on port $PORT...${NC}"
if [ "$MODE" = "production" ]; then
    # Production mode with gunicorn
    if command -v gunicorn &> /dev/null; then
        gunicorn --bind 0.0.0.0:$PORT --workers 4 --daemon app:app
        WEB_PID=$!
    else
        python -m http.server $PORT > logs/web_server.log 2>&1 &
        WEB_PID=$!
    fi
else
    # Development mode
    python -m http.server $PORT > logs/web_server.log 2>&1 &
    WEB_PID=$!
fi

# Save PIDs for later management
cat > .pids <<EOF
MCP_PID=$MCP_PID
CLAUDE_PID=$CLAUDE_PID
PERF_PID=$PERF_PID
COST_PID=$COST_PID
WEB_PID=$WEB_PID
EOF

# Health check
echo -e "${BLUE}🔍 Running health check...${NC}"
sleep 3

# Check if services are running
if ps -p $MCP_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✅ MCP Memory Server: Running${NC}"
else
    echo -e "${RED}❌ MCP Memory Server: Failed${NC}"
fi

if ps -p $CLAUDE_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Claude Monitor: Running${NC}"
else
    echo -e "${RED}❌ Claude Monitor: Failed${NC}"
fi

if ps -p $PERF_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Performance Monitor: Running${NC}"
else
    echo -e "${RED}❌ Performance Monitor: Failed${NC}"
fi

if ps -p $WEB_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Web Server: Running on port $PORT${NC}"
else
    echo -e "${RED}❌ Web Server: Failed${NC}"
fi

# Test OpenRouter connection
echo -e "${BLUE}🔗 Testing OpenRouter connection...${NC}"
python -c "
import requests
import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('OPENROUTER_API_KEY')
if not api_key:
    print('❌ OpenRouter API key not found in .env')
    exit(1)

try:
    headers = {'Authorization': f'Bearer {api_key}'}
    response = requests.get('https://openrouter.ai/api/v1/models', headers=headers, timeout=10)
    if response.status_code == 200:
        models = response.json()
        free_models = [m for m in models.get('data', []) if m.get('pricing', {}).get('prompt') == '0']
        print(f'✅ OpenRouter: Connected ({len(free_models)} free models)')
    else:
        print(f'⚠️  OpenRouter: HTTP {response.status_code}')
except Exception as e:
    print(f'❌ OpenRouter: Connection failed - {e}')
"

echo ""
echo -e "${GREEN}🎉 AI Empire Monitoring Suite deployed successfully!${NC}"
echo ""
echo -e "${BLUE}📊 Access Points:${NC}"
echo -e "  • Main Dashboard: ${YELLOW}http://localhost:$PORT/dashboards/AI_EMPIRE_COMPLETE_DASHBOARD.html${NC}"
echo -e "  • Real-time Analytics: ${YELLOW}http://localhost:$PORT/dashboards/REAL_TIME_ANALYTICS_DASHBOARD.html${NC}"
echo -e "  • Status Dashboard: ${YELLOW}http://localhost:$PORT/dashboards/ULTIMATE_EMPIRE_STATUS_DASHBOARD.html${NC}"
echo -e "  • Revenue Dashboard: ${YELLOW}http://localhost:$PORT/dashboards/PRODUCTION_REVENUE_DASHBOARD.html${NC}"
echo -e "  • Progress Monitor: ${YELLOW}http://localhost:$PORT/dashboards/CONSOLIDATION_PROGRESS_MONITOR.html${NC}"
echo ""
echo -e "${BLUE}🔧 Management Commands:${NC}"
echo -e "  • Stop all services: ${YELLOW}./scripts/stop.sh${NC}"
echo -e "  • View logs: ${YELLOW}tail -f logs/*.log${NC}"
echo -e "  • Health check: ${YELLOW}./scripts/health_check.sh${NC}"
echo -e "  • Restart services: ${YELLOW}./scripts/restart.sh${NC}"
echo ""
echo -e "${BLUE}📈 System Status:${NC}"
echo -e "  • Mode: $MODE"
echo -e "  • Port: $PORT"
echo -e "  • Cost: \$0.00 (Free models only)"
echo -e "  • Memory Persistence: Enabled"
echo -e "  • Real-time Monitoring: Active"
echo ""
echo -e "${GREEN}🚀 Ready for operation!${NC}"