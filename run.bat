@echo off
echo === Starting Vocalis ===

:: Start backend in a new window
start cmd /k "call .\env\Scripts\activate && python -m backend.main"

:: Wait a moment for backend to initialize
timeout /t 2 /nobreak > nul

:: Start frontend in a new window

echo === Vocalis servers started ===
echo Backend: http://localhost:8000 (or your FastAPI port)
