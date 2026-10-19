#!/data/data/com.termux/files/usr/bin/bash
set -e
cd "$(dirname "$0")"
command -v python >/dev/null || { echo "Python missing. Run: pkg install python"; exit 1; }
command -v ffmpeg >/dev/null || { echo "FFmpeg missing. Run: pkg install ffmpeg"; exit 1; }
export GODRENDER_HOST="${GODRENDER_HOST:-127.0.0.1}"
export GODRENDER_PORT="${GODRENDER_PORT:-8080}"
export GODRENDER_WORKERS="${GODRENDER_WORKERS:-2}"
echo "Starting GodRender Studio on port $GODRENDER_PORT with $GODRENDER_WORKERS workers..."
exec python stack.py
