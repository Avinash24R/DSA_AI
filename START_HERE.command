#!/usr/bin/env bash
# ===============================================================
# DSA AI Tutor — one-click entry point (macOS)
#
# Double-click this file in Finder after extracting/cloning the
# project (first time: right-click -> Open, to get past Gatekeeper).
# It runs desktop/install_macos.sh (checks Python/Docker, creates
# .env, adds a Desktop launcher) and then opens the GUI immediately.
# ===============================================================
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCHER="$HERE/desktop/dsa_tutor_launcher.py"

bash "$HERE/desktop/install_macos.sh"
status=$?
if [ $status -ne 0 ]; then
    echo
    echo "Setup did not finish - see the messages above."
    read -n 1 -s -r -p "Press any key to close..."
    exit 1
fi

echo
echo "Opening the DSA AI Tutor launcher..."
python3 "$LAUNCHER"
