@echo off
rem Starts the API (port 8000) and the web app (port 3000) from this folder.
set ROOT=%~dp0
start "QUEST Portal API" cmd /k "cd /d %ROOT%backend && uvicorn main:app --reload"
start "QUEST Portal Web" cmd /k "cd /d %ROOT%frontend && npm run dev"
timeout /t 5 >nul
start http://localhost:3000
