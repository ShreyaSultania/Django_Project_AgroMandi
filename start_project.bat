@echo off
title Agro-AI System Launcher
echo ====================================================
echo Starting Agro-AI System (Django Backend + Frontend)
echo ====================================================
echo.

echo [1/2] Launching Django REST Backend on http://localhost:5001/ ...
start "Agro-AI Django Backend" cmd /k "cd /d %~dp0django_backend && python manage.py runserver"

timeout /t 3 /nobreak >nul

echo [2/2] Launching React Frontend on http://localhost:5173/ ...
start "Agro-AI React Frontend" cmd /k "cd /d %~dp0Frontend && npm run dev"

echo.
echo ====================================================
echo Both servers are starting up:
echo   - Backend:  http://localhost:5001/
echo   - Frontend: http://localhost:5173/
echo ====================================================
echo.
