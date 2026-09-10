#!/usr/bin/env bash
# DSA AI Tutor - Linux Installer
#
# Checks Python and Docker, creates a .env from the template if
# missing, and adds a desktop launcher icon (.desktop entry).

set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "==============================================="
echo "  DSA AI Tutor - Linux Installer"
echo "==============================================="
echo
echo "Project folder: $PROJECT_ROOT"
echo

status=0

# ---------------------------------------------------------------
# 1. Check Python 3
# ---------------------------------------------------------------
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
    echo "[OK] Python found: $(python3 --version)"
else
    echo "[MISSING] python3 was not found."
    echo "Install it with your package manager, e.g.:"
    echo "    sudo apt install python3"
    status=1
fi

# ---------------------------------------------------------------
# 2. Check tkinter
# ---------------------------------------------------------------
if [ "${PYTHON_CMD:-}" != "" ] && $PYTHON_CMD -c "import tkinter" >/dev/null 2>&1; then
    echo "[OK] tkinter available"
elif [ "${PYTHON_CMD:-}" != "" ]; then
    echo "[MISSING] tkinter is not available for this Python."
    echo "Install it with:"
    echo "    Debian/Ubuntu:  sudo apt install python3-tk"
    echo "    Fedora:         sudo dnf install python3-tkinter"
    echo "    Arch:           sudo pacman -S tk"
    status=1
fi

# ---------------------------------------------------------------
# 3. Check Docker
# ---------------------------------------------------------------
if command -v docker >/dev/null 2>&1; then
    echo "[OK] Docker found"
    if docker info >/dev/null 2>&1; then
        echo "[OK] Docker daemon is running"
    else
        echo "[WARNING] Docker is installed but doesn't seem to be running,"
        echo "or your user isn't in the 'docker' group. Try:"
        echo "    sudo systemctl start docker"
        echo "    sudo usermod -aG docker \$USER   (then log out and back in)"
    fi
else
    echo "[MISSING] Docker was not found."
    echo "Install it via https://docs.docker.com/engine/install/"
    status=1
fi

if [ $status -ne 0 ]; then
    echo
    echo "Install the missing tools above, then run this script again."
    exit 1
fi

# ---------------------------------------------------------------
# 4. Create .env if missing
# ---------------------------------------------------------------
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    if [ -f "$PROJECT_ROOT/dot.env" ]; then
        cp "$PROJECT_ROOT/dot.env" "$PROJECT_ROOT/.env"
        echo "[OK] Created .env from template - edit it and add your GROQ_API key."
    fi
else
    echo "[OK] .env already exists"
fi

# ---------------------------------------------------------------
# 5. Create a desktop launcher (.desktop file)
# ---------------------------------------------------------------
APPS_DIR="$HOME/.local/share/applications"
mkdir -p "$APPS_DIR"
DESKTOP_FILE="$APPS_DIR/dsa-ai-tutor.desktop"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=DSA AI Tutor
Comment=Launch the DSA AI Tutor stack
Exec=$PYTHON_CMD "$PROJECT_ROOT/desktop/dsa_tutor_launcher.py"
Icon=$PROJECT_ROOT/desktop/assets/icon.png
Path=$PROJECT_ROOT
Terminal=false
Categories=Education;Development;
EOF
chmod +x "$DESKTOP_FILE"
echo "[OK] Created application entry: $DESKTOP_FILE"

# Also drop a copy on the Desktop folder if one exists.
if [ -d "$HOME/Desktop" ]; then
    cp "$DESKTOP_FILE" "$HOME/Desktop/dsa-ai-tutor.desktop"
    chmod +x "$HOME/Desktop/dsa-ai-tutor.desktop"
    echo "[OK] Copied shortcut to $HOME/Desktop"
    echo "Note: GNOME/Nautilus may keep it marked 'untrusted' at first —"
    echo "right-click it and choose 'Allow Launching' (or 'Trust and Launch')."
fi

echo
echo "==============================================="
echo "  Setup complete! Find 'DSA AI Tutor' in your"
echo "  applications menu or on your Desktop."
echo "==============================================="
