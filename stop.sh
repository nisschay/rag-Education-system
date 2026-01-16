#!/bin/bash

# RAG Education System - Stop Script
# This script stops both backend and frontend servers

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$SCRIPT_DIR/.pids"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${RED}========================================${NC}"
echo -e "${RED}  RAG Education System - Stopping...   ${NC}"
echo -e "${RED}========================================${NC}"

# Function to stop a service
stop_service() {
    local service_name=$1
    local pid_file="$PID_DIR/$service_name.pid"
    
    echo -e "\n${YELLOW}Stopping $service_name...${NC}"
    
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            sleep 1
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                kill -9 "$pid" 2>/dev/null
            fi
            echo -e "${GREEN}$service_name (PID: $pid) stopped${NC}"
        else
            echo -e "${YELLOW}$service_name was not running${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}No PID file found for $service_name${NC}"
    fi
}

# Kill any remaining processes on the ports
kill_port() {
    local port=$1
    local pids=$(lsof -ti:$port 2>/dev/null)
    if [ -n "$pids" ]; then
        echo -e "${YELLOW}Killing processes on port $port: $pids${NC}"
        echo "$pids" | xargs kill -9 2>/dev/null
    fi
}

# Stop services
stop_service "backend"
stop_service "frontend"

# Also kill any orphaned processes on the ports
echo -e "\n${YELLOW}Cleaning up any orphaned processes...${NC}"
kill_port 8000
kill_port 5173

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  All services stopped successfully!   ${NC}"
echo -e "${GREEN}========================================${NC}"
