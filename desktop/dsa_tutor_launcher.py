"""
DSA AI Tutor — Desktop Launcher

A small cross-platform GUI (Windows / macOS / Linux) for running the
project without memorizing Docker commands. It checks that Docker and
Python are installed and that Docker is actually running, then lets
you build the images, start/stop the stack, and seed the roadmap +
Codeforces + LeetCode problem pools — all from one window.

Run directly:
    python desktop/dsa_tutor_launcher.py

This file only uses the Python standard library (tkinter, subprocess,
threading, webbrowser, ...) so it doesn't need `pip install` to run.
On some minimal Linux installs tkinter isn't bundled with Python; if
you see "No module named tkinter" install it with:
    Debian/Ubuntu:  sudo apt install python3-tk
    Fedora:         sudo dnf install python3-tkinter
    Arch:           sudo pacman -S tk
"""

import os
import queue
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except ImportError:
    print(
        "tkinter isn't installed for this Python. See the comment at "
        "the top of this file for how to install it, then try again."
    )
    sys.exit(1)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
ENV_TEMPLATE = PROJECT_ROOT / "dot.env"
FRONTEND_URL = "http://localhost:5500"
BACKEND_URL = "http://localhost:8000"

APP_TITLE = "DSA AI Tutor — Launcher"


def compose_base_cmd() -> list[str]:
    """
    Prefer the modern `docker compose` (Compose V2, bundled with
    current Docker Desktop / docker-ce) and fall back to the legacy
    standalone `docker-compose` binary if that's what's installed.
    """
    if shutil.which("docker") and _docker_compose_v2_available():
        return ["docker", "compose"]
    if shutil.which("docker-compose"):
        return ["docker-compose"]
    return ["docker", "compose"]


def _docker_compose_v2_available() -> bool:
    try:
        result = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def which_python() -> str | None:
    for candidate in ("python3", "python"):
        if shutil.which(candidate):
            return candidate
    return None


class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        self.geometry("760x560")
        self.minsize(640, 480)

        self.log_queue: "queue.Queue[str]" = queue.Queue()
        self.busy = False

        self._build_ui()
        self._poll_log_queue()

        self.after(200, self.check_requirements)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        header = ttk.Frame(self, padding=(16, 16, 16, 8))
        header.pack(fill="x")

        ttk.Label(
            header, text="DSA AI Tutor", font=("Segoe UI", 18, "bold")
        ).pack(anchor="w")
        ttk.Label(
            header,
            text=f"Project folder: {PROJECT_ROOT}",
            foreground="#666666",
        ).pack(anchor="w")

        status = ttk.LabelFrame(self, text="Requirements", padding=12)
        status.pack(fill="x", padx=16, pady=8)

        self.status_labels = {}
        for key, label in [
            ("docker", "Docker"),
            ("docker_running", "Docker daemon running"),
            ("compose", "Docker Compose"),
            ("python", "Python"),
            ("env", ".env file"),
        ]:
            row = ttk.Frame(status)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=label, width=24).pack(side="left")
            value = ttk.Label(row, text="Checking…", foreground="#888888")
            value.pack(side="left")
            self.status_labels[key] = value

        ttk.Button(
            status, text="Re-check", command=self.check_requirements
        ).pack(anchor="e", pady=(6, 0))

        actions = ttk.LabelFrame(self, text="Actions", padding=12)
        actions.pack(fill="x", padx=16, pady=8)

        row1 = ttk.Frame(actions)
        row1.pack(fill="x", pady=2)
        self.build_btn = ttk.Button(
            row1, text="1. Build images", command=self.action_build
        )
        self.build_btn.pack(side="left", padx=(0, 6))

        self.start_btn = ttk.Button(
            row1, text="2. Start", command=self.action_start
        )
        self.start_btn.pack(side="left", padx=6)

        self.stop_btn = ttk.Button(
            row1, text="Stop", command=self.action_stop
        )
        self.stop_btn.pack(side="left", padx=6)

        self.seed_btn = ttk.Button(
            row1, text="3. Seed problems (roadmap + Codeforces + LeetCode)",
            command=self.action_seed,
        )
        self.seed_btn.pack(side="left", padx=6)

        row2 = ttk.Frame(actions)
        row2.pack(fill="x", pady=(8, 2))

        self.open_btn = ttk.Button(
            row2, text="Open app in browser", command=self.action_open
        )
        self.open_btn.pack(side="left", padx=(0, 6))

        ttk.Button(
            row2, text="View container status", command=self.action_ps
        ).pack(side="left", padx=6)

        self.action_buttons = [
            self.build_btn, self.start_btn, self.stop_btn,
            self.seed_btn, self.open_btn,
        ]

        log_frame = ttk.LabelFrame(self, text="Log", padding=8)
        log_frame.pack(fill="both", expand=True, padx=16, pady=(8, 16))

        self.log_text = tk.Text(
            log_frame, wrap="word", state="disabled",
            background="#0d1117", foreground="#d8dee9",
            insertbackground="#d8dee9", font=("Consolas", 10),
        )
        self.log_text.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(
            log_frame, command=self.log_text.yview
        )
        scrollbar.pack(fill="y", side="right")
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.status_bar = ttk.Label(
            self, text="Ready", relief="sunken", anchor="w", padding=(8, 2)
        )
        self.status_bar.pack(fill="x", side="bottom")

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------

    def log(self, message: str):
        self.log_queue.put(message)

    def _poll_log_queue(self):
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.configure(state="normal")
                self.log_text.insert("end", message + "\n")
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(100, self._poll_log_queue)

    def _set_status(self, key: str, text: str, ok: bool | None):
        color = "#888888" if ok is None else ("#2e8b57" if ok else "#c0392b")
        self.status_labels[key].configure(text=text, foreground=color)

    def _set_busy(self, busy: bool, status_text: str = "Ready"):
        self.busy = busy
        state = "disabled" if busy else "normal"
        for btn in self.action_buttons:
            btn.configure(state=state)
        self.status_bar.configure(text=status_text)

    # ------------------------------------------------------------------
    # Requirement checks
    # ------------------------------------------------------------------

    def check_requirements(self):
        docker_path = shutil.which("docker")
        self._set_status(
            "docker",
            "Found" if docker_path else "Not found — install Docker Desktop",
            bool(docker_path),
        )

        compose_ok = False
        if docker_path:
            compose_ok = _docker_compose_v2_available() or bool(
                shutil.which("docker-compose")
            )
        self._set_status(
            "compose",
            "Found" if compose_ok else "Not found",
            compose_ok,
        )

        docker_running = False
        if docker_path:
            try:
                result = subprocess.run(
                    ["docker", "info"], capture_output=True, timeout=10
                )
                docker_running = result.returncode == 0
            except Exception:
                docker_running = False
        self._set_status(
            "docker_running",
            "Running" if docker_running else "Not running — start Docker Desktop",
            docker_running,
        )

        python_path = which_python()
        self._set_status(
            "python",
            f"Found ({python_path})" if python_path else "Not found",
            bool(python_path),
        )

        env_ok = ENV_FILE.exists()
        self._set_status(
            "env",
            "Found" if env_ok else "Missing — click to create from template",
            env_ok,
        )
        if not env_ok:
            self.after(50, self._offer_env_creation)

    def _offer_env_creation(self):
        if not ENV_TEMPLATE.exists():
            return
        if messagebox.askyesno(
            "Create .env file?",
            (
                "No .env file was found. Create one from dot.env now?\n\n"
                "You'll still need to edit it and add your GROQ_API key "
                "before starting the app."
            ),
        ):
            shutil.copy(ENV_TEMPLATE, ENV_FILE)
            self.log(f"Created {ENV_FILE} from template — edit it and add your GROQ_API key.")
            self.check_requirements()

    # ------------------------------------------------------------------
    # Actions (each runs a subprocess on a background thread so the
    # GUI never freezes while Docker does its thing)
    # ------------------------------------------------------------------

    def _run_command(self, cmd: list[str], on_done=None, label: str = ""):
        if self.busy:
            messagebox.showinfo(APP_TITLE, "Another action is already running — please wait.")
            return

        def worker():
            self._set_busy(True, f"Running: {label or ' '.join(cmd)}")
            self.log(f"\n$ {' '.join(cmd)}")
            try:
                process = subprocess.Popen(
                    cmd,
                    cwd=PROJECT_ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                assert process.stdout is not None
                for line in process.stdout:
                    self.log(line.rstrip())
                process.wait()
                if process.returncode == 0:
                    self.log(f"[OK] {label or 'Command'} finished successfully.")
                else:
                    self.log(
                        f"[ERROR] {label or 'Command'} exited with code {process.returncode}."
                    )
            except FileNotFoundError:
                self.log(f"[ERROR] Command not found: {cmd[0]}. Is it installed and on PATH?")
            except Exception as e:
                self.log(f"[ERROR] {e}")
            finally:
                self._set_busy(False)
                if on_done:
                    self.after(0, on_done)

        threading.Thread(target=worker, daemon=True).start()

    def action_build(self):
        self._run_command(
            compose_base_cmd() + ["build"], label="Build images"
        )

    def action_start(self):
        self._run_command(
            compose_base_cmd() + ["up", "-d"], label="Start containers"
        )

    def action_stop(self):
        self._run_command(
            compose_base_cmd() + ["down"], label="Stop containers"
        )

    def action_seed(self):
        # Chains roadmap + Codeforces + LeetCode seeding — see the
        # `roadmap-seeder` service's `command:` in docker-compose.yaml.
        self._run_command(
            compose_base_cmd() + ["run", "--rm", "roadmap-seeder"],
            label="Seed roadmap + Codeforces + LeetCode problems",
        )

    def action_ps(self):
        self._run_command(compose_base_cmd() + ["ps"], label="Container status")

    def action_open(self):
        webbrowser.open(FRONTEND_URL)
        self.log(f"Opened {FRONTEND_URL} in your browser (backend API at {BACKEND_URL}).")


def main():
    app = Launcher()
    app.mainloop()


if __name__ == "__main__":
    main()
