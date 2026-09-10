# DSA AI Tutor — Desktop Launcher

A one-window GUI for running the project without memorizing Docker
commands: build the images, start/stop the stack, seed the Codeforces
+ LeetCode problem pools, and open the app — all from one place.

## Install

Pick the script for your OS. Each one checks for Python and Docker,
creates a `.env` from the template if you don't have one yet, and
adds a desktop icon that opens the launcher.

**Windows** — double-click `install_windows.bat` (or run it from a
terminal). Creates `DSA AI Tutor.lnk` on your Desktop.

**macOS** — in Terminal:
```bash
./desktop/install_macos.sh
```
Creates `DSA AI Tutor.command` on your Desktop (double-click to run;
the first time, right-click → Open to get past Gatekeeper).

**Linux** — in a terminal:
```bash
./desktop/install_linux.sh
```
Creates an application-menu entry and, if `~/Desktop` exists, a copy
there too (right-click it → "Allow Launching" on GNOME the first time).

## Running it manually

No installer needed — this only needs the Python standard library:

```bash
python3 desktop/dsa_tutor_launcher.py
```

If you get `No module named tkinter`, install it separately (it isn't
bundled with Python on some minimal Linux installs):

```bash
sudo apt install python3-tk      # Debian/Ubuntu
sudo dnf install python3-tkinter # Fedora
sudo pacman -S tk                # Arch
brew install python-tk           # macOS + Homebrew Python
```

## What the launcher does

| Button | Runs |
|---|---|
| Re-check | Verifies Docker is installed, the daemon is running, Docker Compose is available, Python is found, and `.env` exists |
| Build images | `docker compose build` |
| Start | `docker compose up -d` |
| Stop | `docker compose down` |
| Seed problems | `docker compose run --rm roadmap-seeder` — seeds the roadmap, then Codeforces, then LeetCode ([see docker-compose.yaml](../docker-compose.yaml)) |
| View container status | `docker compose ps` |
| Open app in browser | Opens `http://localhost:5500` |

It always runs these against the project root (one level up from
`desktop/`), and logs full command output in the window so you can
see exactly what's happening.

## Notes

- You still need a Groq API key in `.env` (`GROQ_API=...`) before
  starting the backend — the installer creates the file but can't
  fill that in for you.
- Only the standard library is used, so no `pip install` is required
  to run the launcher itself.
