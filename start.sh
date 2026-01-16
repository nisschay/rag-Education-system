#!/bin/bash

# RAG Education System - Start Script
# This script starts both backend and frontend servers

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
LOG_DIR="$SCRIPT_DIR/logs"
PID_DIR="$SCRIPT_DIR/.pids"

# Create directories
mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  RAG Education System - Starting...   ${NC}"
echo -e "${GREEN}========================================${NC}"

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Start Backend
start_backend() {
    echo -e "\n${YELLOW}Starting Backend Server...${NC}"
    
    if check_port 8000; then
        echo -e "${RED}Port 8000 is already in use. Backend may already be running.${NC}"
        return 1
    fi
    
    cd "$BACKEND_DIR"
    
    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo -e "${RED}Virtual environment not found. Creating one...${NC}"
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    fi
    
    # Start backend server
    nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 \
        >> "$LOG_DIR/backend.log" 2>&1 &
    
    echo $! > "$PID_DIR/backend.pid"
    echo -e "${GREEN}Backend started with PID: $!${NC}"
    echo -e "${GREEN}Backend logs: $LOG_DIR/backend.log${NC}"
    echo -e "${GREEN}Backend URL: http://localhost:8000${NC}"
}

# Start Frontend
start_frontend() {
    echo -e "\n${YELLOW}Starting Frontend Server...${NC}"
    
    if check_port 5173; then
        echo -e "${RED}Port 5173 is already in use. Frontend may already be running.${NC}"
        return 1
    fi
    
    cd "$FRONTEND_DIR"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing frontend dependencies...${NC}"
        npm install
    fi
    
    # Start frontend server
    nohup npm run dev >> "$LOG_DIR/frontend.log" 2>&1 &
    
    echo $! > "$PID_DIR/frontend.pid"
    echo -e "${GREEN}Frontend started with PID: $!${NC}"
    echo -e "${GREEN}Frontend logs: $LOG_DIR/frontend.log${NC}"
    echo -e "${GREEN}Frontend URL: http://localhost:5173${NC}"
}

# Main
start_backend
sleep 2
start_frontend

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  All services started successfully!   ${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n${YELLOW}To view logs:${NC}"
echo -e "  Backend:  tail -f $LOG_DIR/backend.log"
echo -e "  Frontend: tail -f $LOG_DIR/frontend.log"
echo -e "\n${YELLOW}To stop servers:${NC}"
echo -e "  ./stop.sh"
