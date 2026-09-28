@echo off
REM One-click starter for TalentMatch AI (Windows).
REM Double-click this file to set up and launch the app. Safe to run again any
REM time - it reuses what's already set up.

cd /d "%~dp0backend"

if not exist ".venv" (
  echo Setting up TalentMatch AI for the first time - this can take a minute...
  python -m venv .venv
)

call .venv\Scripts\activate.bat
python -m ensurepip --upgrade
python -m pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

if not exist ".env" (
  copy .env.example .env >nul
  echo.
  echo ======================================================================
  echo  First-time setup: open backend\.env in Notepad and paste your Gemini
  echo  API key after GEMINI_API_KEY=
  echo  (See GEMINI_SETUP.md in this folder for how to get a free key.)
  echo ======================================================================
  echo.
  pause
)

echo.
echo Starting TalentMatch AI...
echo Once it says "Application startup complete", open this in your browser:
echo.
echo    http://127.0.0.1:8000
echo.
echo (Close this window to stop the app.)
echo.

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

pause
