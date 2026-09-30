#!/bin/bash
# Start the intelligence worker in the background
python -m apps.intelligence.live_worker --interval 120 &

# Start the dashboard server on the port provided by Render
PORT="${PORT:-8080}"
echo "Starting web server on port $PORT..."
python -m http.server $PORT --directory apps/intelligence/dashboard
