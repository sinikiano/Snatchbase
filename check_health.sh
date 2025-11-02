#!/bin/bash

echo "🔍 Snatchbase Health Check"
echo "=========================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check Backend
echo -n "Backend (Port 8000): "
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Running${NC}"
    BACKEND_RUNNING=1
else
    echo -e "${RED}✗ Not Running${NC}"
    BACKEND_RUNNING=0
fi

# Check Frontend
echo -n "Frontend (Port 3000): "
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Running${NC}"
    FRONTEND_RUNNING=1
else
    echo -e "${RED}✗ Not Running${NC}"
    FRONTEND_RUNNING=0
fi

# Check Telegram Bot
echo -n "Telegram Bot: "
if ps aux | grep "run_telegram_bot.py" | grep -v grep > /dev/null; then
    echo -e "${GREEN}✓ Running${NC}"
    BOT_RUNNING=1
else
    echo -e "${YELLOW}⚠ Not Running${NC}"
    BOT_RUNNING=0
fi

# Check Database Connection
echo -n "Database Connection: "
if [ $BACKEND_RUNNING -eq 1 ]; then
    if curl -s http://localhost:8000/stats > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Connected${NC}"
        DB_CONNECTED=1
    else
        echo -e "${RED}✗ Not Connected${NC}"
        DB_CONNECTED=0
    fi
else
    echo -e "${YELLOW}⚠ Cannot Check (Backend not running)${NC}"
    DB_CONNECTED=0
fi

echo ""
echo "📊 Statistics:"
if [ $BACKEND_RUNNING -eq 1 ] && [ $DB_CONNECTED -eq 1 ]; then
    STATS=$(curl -s http://localhost:8000/stats)
    echo "$STATS" | jq '.' 2>/dev/null || echo "$STATS"
fi

echo ""
echo "🔧 Process Information:"
echo "Backend PIDs: $(pgrep -f 'uvicorn app.main:app' | tr '\n' ' ')"
echo "Frontend PIDs: $(pgrep -f 'vite' | tr '\n' ' ')"
echo "Telegram Bot PIDs: $(pgrep -f 'run_telegram_bot.py' | tr '\n' ' ')"

echo ""
echo "📝 Recent Logs:"
echo "--- Backend (last 5 lines) ---"
tail -5 /tmp/snatchbase-backend.log 2>/dev/null || echo "No log file found"

echo ""
echo "--- Frontend (last 5 lines) ---"
tail -5 /tmp/snatchbase-frontend.log 2>/dev/null || echo "No log file found"

echo ""
if [ $BACKEND_RUNNING -eq 1 ] && [ $FRONTEND_RUNNING -eq 1 ]; then
    echo -e "${GREEN}✓ All services are healthy!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some services are not running. Run ./start_snatchbase.sh to start all services.${NC}"
    exit 1
fi
