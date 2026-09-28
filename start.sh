#!/usr/bin/env bash
# One-click starter for TalentMatch AI (macOS / Linux).
# Double-click this file (or run "./start.sh" in a terminal) to set up and
# launch the app. Safe to run again any time - it reuses what's already set up.
set -e
cd "$(dirname "$0")/backend"

if [ ! -d ".venv" ]; then
  echo "Setting up TalentMatch AI for the first time - this can take a minute..."
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo ""
  echo "======================================================================"
  echo " First-time setup: open backend/.env in any text editor and paste"
  echo " your Gemini API key after GEMINI_API_KEY="
  echo " (See GEMINI_SETUP.md in this folder for how to get a free key.)"
  echo "======================================================================"
  echo ""
fi

echo ""
echo "Starting TalentMatch AI..."
echo "Once it says 'Application startup complete', open this in your browser:"
echo ""
echo "   http://127.0.0.1:8000"
echo ""
echo "(Press Ctrl+C in this window to stop the app.)"
echo ""

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
