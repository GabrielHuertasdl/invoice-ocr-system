#!/usr/bin/env bash
# Starts both the backend (FastAPI) and frontend (Vite) in the background.
# Run from the project root: ./start.sh
# Stop everything: ./start.sh stop

set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/invoice_system/backend"
FRONTEND="$ROOT/invoice_system/frontend"
VENV="$ROOT/invoice_system/venv"
PID_FILE="$ROOT/.pids"

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "No running processes found (no .pids file)."
        exit 0
    fi
    echo "Stopping backend and frontend..."
    while IFS= read -r pid; do
        kill "$pid" 2>/dev/null && echo "  killed PID $pid" || echo "  PID $pid already gone"
    done < "$PID_FILE"
    rm -f "$PID_FILE"
    echo "Done."
    exit 0
}

[ "${1}" = "stop" ] && stop

# ── Environment checks ──────────────────────────────────────────────────────
if ! command -v tesseract &>/dev/null; then
    echo "WARNING: tesseract not found. Install with: sudo apt install tesseract-ocr"
fi
if ! command -v pdfinfo &>/dev/null; then
    echo "WARNING: poppler not found. Install with: sudo apt install poppler-utils"
fi

# ── .env setup ───────────────────────────────────────────────────────────────
if [ ! -f "$BACKEND/.env" ]; then
    echo "No .env found — copying .env.example. Edit $BACKEND/.env if needed."
    cp "$BACKEND/.env.example" "$BACKEND/.env"
fi

# ── Backend ──────────────────────────────────────────────────────────────────
echo "Starting backend on http://localhost:8000 ..."
source "$VENV/bin/activate"
cd "$BACKEND"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "$BACKEND_PID" > "$PID_FILE"

# ── Frontend ─────────────────────────────────────────────────────────────────
echo "Starting frontend on http://localhost:5173 ..."
cd "$FRONTEND"
npm run dev &
FRONTEND_PID=$!
echo "$FRONTEND_PID" >> "$PID_FILE"

echo ""
echo "Both services running."
echo "  Backend:  http://localhost:8000  (Swagger: http://localhost:8000/docs)"
echo "  Frontend: http://localhost:5173"
echo ""
echo "To stop everything, run:  ./start.sh stop"
echo "(or press Ctrl+C here and then run ./start.sh stop)"

wait
