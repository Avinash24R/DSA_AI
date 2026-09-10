#!/usr/bin/env bash
# DSA AI Tutor - macOS Installer
#
# Checks Python and Docker, creates a .env from the template if
# missing, and adds a double-clickable launcher icon to the Desktop.

set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "==============================================="
echo "  DSA AI Tutor - macOS Installer"
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
    echo "Install it from https://www.python.org/downloads/ or with:"
    echo "    brew install python"
    status=1
fi

# ---------------------------------------------------------------
# 2. Check tkinter
# ---------------------------------------------------------------
if [ "${PYTHON_CMD:-}" != "" ] && $PYTHON_CMD -c "import tkinter" >/dev/null 2>&1; then
    echo "[OK] tkinter available"
elif [ "${PYTHON_CMD:-}" != "" ]; then
    echo "[MISSING] tkinter is not available for this Python."
    echo "If you installed Python via Homebrew, try:"
    echo "    brew install python-tk"
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
        echo "[WARNING] Docker is installed but doesn't seem to be running."
        echo "Start Docker Desktop, then use the launcher's 'Re-check' button."
    fi
else
    echo "[MISSING] Docker was not found."
    echo "Install Docker Desktop from https://www.docker.com/products/docker-desktop/"
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
# 5. Create a double-clickable launcher on the Desktop
# ---------------------------------------------------------------
DESKTOP="$HOME/Desktop"
LAUNCHER_CMD="$DESKTOP/DSA AI Tutor.command"

mkdir -p "$DESKTOP"
cat > "$LAUNCHER_CMD" <<EOF
#!/usr/bin/env bash
cd "$PROJECT_ROOT"
$PYTHON_CMD "$PROJECT_ROOT/desktop/dsa_tutor_launcher.py"
EOF
chmod +x "$LAUNCHER_CMD"

echo "[OK] Created launcher: $LAUNCHER_CMD"
echo
echo "Note: macOS may warn the first time you open an app downloaded"
echo "from the internet. If so, right-click the icon on your Desktop"
echo "and choose Open, then confirm."
echo
echo "(Optional) To give it a custom icon: select DSA AI Tutor.command"
echo "in Finder, press Cmd+I, drag desktop/assets/icon.png onto the"
echo "icon shown in the top-left of the Info window."
echo
echo "==============================================="
echo "  Setup complete! Double-click 'DSA AI Tutor'"
echo "  on your Desktop to open the launcher."
echo "==============================================="
