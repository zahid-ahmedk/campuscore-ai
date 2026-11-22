@echo off
start "CampusCore Backend (FastAPI)" cmd /k "cd /d D:\campuscore-ai\backend && uvicorn main:app --reload"
start "CampusCore Frontend (Next.js)" cmd /k "cd /d D:\campuscore-ai\frontend && npm run dev"
timeout /t 4 >nul
start http://localhost:3000
