#!/usr/bin/env bash
# ============================================================
#  UniFind - Campus Lost & Found Management System
#  One-click launcher for macOS / Linux
# ============================================================
set -e
cd "$(dirname "$0")"

PY=python3
command -v $PY >/dev/null 2>&1 || PY=python

# --- 1. Create virtual environment if missing ---
if [ ! -d ".venv" ]; then
    echo "[1/3] Creating virtual environment ..."
    $PY -m venv .venv
fi

# --- 2. Activate venv ---
source .venv/bin/activate

# --- 3. Install dependencies ---
echo "[2/3] Installing dependencies ..."
pip install -r requirements.txt -q

# --- Apply migrations ---
echo "      Applying database migrations ..."
python manage.py migrate --noinput

# --- Seed categories & demo accounts (safe to re-run) ---
echo "      Seeding categories and demo accounts ..."
python manage.py seed_data

# --- Run the server ---
echo
echo "[3/3] Starting UniFind at http://127.0.0.1:8000"
echo "      Press Ctrl+C to stop the server."
echo
python manage.py runserver
