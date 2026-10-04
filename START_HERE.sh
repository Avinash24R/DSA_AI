#!/usr/bin/env bash
# ===============================================================
# DSA AI Tutor — one-click entry point (Linux)
#
# Run this after extracting/cloning the project:
#     ./START_HERE.sh
# It runs desktop/install_linux.sh (checks Python/Docker, creates
# .env, adds an application-menu entry) and then opens the GUI
# immediately, so you don't have to go hunting for it on first run.
# ===============================================================
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCHER="$HERE/desktop/dsa_tutor_launcher.py"

bash "$HERE/desktop/install_linux.sh"
status=$?
if [ $status -ne 0 ]; then
    echo
    echo "Setup did not finish - see the messages above."
    exit 1
fi

echo
echo "Opening the DSA AI Tutor launcher..."
python3 "$LAUNCHER"
