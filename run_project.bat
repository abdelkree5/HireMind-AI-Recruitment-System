@echo off
title HireMind Startup
echo ====================================================
echo         HireMind AI Platform - Startup Script
echo ====================================================
echo.

:: Start Backend in a new window
echo [1/2] Launching Backend (FastAPI)...
start "HireMind Backend API" cmd /k "echo Activating Virtual Environment (if exists)... && IF NOT EXIST .venv (echo Creating virtual environment... && py -m venv .venv) && call .venv\Scripts\activate && echo Installing Backend Dependencies... && py -m pip install -r backend\requirements.txt && echo. && echo Starting Backend Server... && py -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000"

:: Start Frontend in a new window
echo [2/2] Launching Frontend (React/Vite)...
start "HireMind Frontend UI" cmd /k "cd frontend && echo Installing Frontend Dependencies... && npm install && echo. && echo Starting Frontend Server... && npm run dev"

echo.
echo ====================================================
echo Both servers are launching in separate windows!
echo Please wait a few seconds for them to fully start.
echo ====================================================
echo.
echo - Backend API Docs: http://127.0.0.1:8000/docs
echo - Frontend Web App: http://localhost:5173
echo.
echo You can keep this window open or close it. The servers will keep running in their own windows.
echo To stop the project, simply close the two new windows that opened.
echo.
pause
