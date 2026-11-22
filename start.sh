#!/bin/bash
# FootPredict AI Launcher Script
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
PORT=5055

echo "⚽ Starting FootPredict AI Server on port $PORT..."
# Check if already running
PID=$(lsof -ti :$PORT 2>/dev/null || fuser $PORT/tcp 2>/dev/null)
if [ ! -z "$PID" ]; then
    echo "⚠️ Port $PORT is already in use by PID $PID. Killing old instance..."
    kill -9 $PID 2>/dev/null
    sleep 1
fi

python3 "$DIR/server.py"
