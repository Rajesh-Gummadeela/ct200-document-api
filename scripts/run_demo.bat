@echo off
REM Script to run the complete demo with automatic server startup

cd /d "%~dp0\.."

REM Clean up database
echo Cleaning up database files...
del /F ct200.db 2>nul
del /F generation_store.json 2>nul

REM Start server in background
echo Starting API server...
start /B python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

REM Wait for server to be ready
echo Waiting for server to start...
timeout /t 3 /nobreak >nul

REM Run demo
echo Running demo...
python scripts/demo.py

REM Cleanup
echo Demo complete!
REM Note: Server will need to be stopped manually
