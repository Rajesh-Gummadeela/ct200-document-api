#!/bin/bash
# Script to run the complete demo with automatic server startup

set -e

cd "$(dirname "$0")/.."

# Clean up database
rm -f ct200.db generation_store.json

# Start server in background
echo "Starting API server..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

# Wait for server to be ready
echo "Waiting for server to start..."
sleep 3

# Run demo
echo "Running demo..."
python scripts/demo.py

# Cleanup
echo "Stopping server..."
kill $SERVER_PID 2>/dev/null || true

echo "Demo complete!"
