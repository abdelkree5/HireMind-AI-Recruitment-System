@echo off
title HireMind Startup
echo ====================================================
echo         HireMind AI Platform - Startup Script
echo ====================================================
echo.

:: Start Backend in a new window
echo [1/2] Launching Backend (FastAPI)...
start "HireMind Backend API" cmd /k "cd /d e:\graduate\Ai_resume_graduate && echo Activating Virtual Environment... && call .venv\Scripts\activate && echo. && echo Starting Backend Server... && python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000"

:: Wait a moment before starting frontend
timeout /t 3 /nobreak >nul

:: Start Frontend in a new window
echo [2/2] Launching Frontend (React/Vite)...
start "HireMind Frontend UI" cmd /k "cd /d e:\graduate\Ai_resume_graduate\frontend && npm run dev"

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
