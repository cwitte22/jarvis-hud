#!/usr/bin/env python3
"""
J.A.R.V.I.S. HUD, Mac launcher.

Runs the HUD from ./docs on your Mac, speaks with the real macOS British voice,
and can start itself every time you log in.

  python3 jarvis.py              start it now
  python3 jarvis.py --install    start it automatically at login
  python3 jarvis.py --uninstall  stop starting at login
  python3 jarvis.py --say "Hello, sir."   just talk

No pip installs needed. Standard library only.
"""
import argparse
import json
import os
import plistlib
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
WEB = HERE / "docs"
PORT = 7777
LABEL = "com.jarvis.hud"
PLIST = Path.home() / "Library/LaunchAgents" / f"{LABEL}.plist"
PREFERRED_VOICES = ["Daniel", "Arthur", "Oliver", "Jamie (Premium)", "Jamie"]

_say_proc = None
_say_lock = threading.Lock()
_flight_cache = {}  # query -> (time, bytes)


# ---------------------------------------------------------------- voice
def pick_voice():
    try:
        out = subprocess.run(["say", "-v", "?"], capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return None
    names = [line.split("  ")[0].strip() for line in out.splitlines()]
    for want in PREFERRED_VOICES:
        if want in names:
            return want
    for line in out.splitlines():
        if "en_GB" in line:
            return line.split("  ")[0].strip()
    return None


VOICE = pick_voice() if sys.platform == "darwin" else None


def say(text):
    """Speak with macOS `say`. Cuts off whatever Jarvis was saying before."""
    global _say_proc
    text = text[:1200]
    if sys.platform != "darwin":
        print(f"[jarvis] {text}")
        return
    with _say_lock:
        if _say_proc and _say_proc.poll() is None:
            _say_proc.terminate()
        cmd = ["say", "-r", "185"] + (["-v", VOICE] if VOICE else []) + [text]
        _say_proc = subprocess.Popen(cmd)


# ---------------------------------------------------------------- server
class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass  # keep the terminal quiet

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path == "/api/say":
            n = min(int(self.headers.get("Content-Length", 0)), 4000)
            text = self.rfile.read(n).decode("utf-8", "ignore").strip()
            if text:
                say(text)
            # rough guess at how long it takes to say, so the reactor glows the right amount
            return self._json({"ok": True, "seconds": len(text.split()) / 3.0})
        self._json({"error": "not found"}, 404)

    def do_GET(self):
        if self.path.startswith("/api/flights"):
            return self.flights()
        return super().do_GET()

    def flights(self):
        # OpenSky doesn't always allow browsers to call it directly, so the Mac fetches it.
        # Cached 20s so we stay well under their free rate limit.
        q = self.path.split("?", 1)[1] if "?" in self.path else ""
        hit = _flight_cache.get(q)
        if hit and time.time() - hit[0] < 20:
            data = hit[1]
        else:
            try:
                req = urllib.request.Request(
                    f"https://opensky-network.org/api/states/all?{q}",
                    headers={"User-Agent": "jarvis-hud/1.0"},
                )
                with urllib.request.urlopen(req, timeout=12) as r:
                    data = r.read()
                _flight_cache[q] = (time.time(), data)
            except Exception as e:
                if hit:
                    data = hit[1]
                else:
                    return self._json({"error": str(e), "states": []}, 502)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def open_window(url):
    """Open as a clean app window in Chrome if you have it, otherwise your default browser."""
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if sys.platform == "darwin" and os.path.exists(chrome):
        subprocess.Popen([chrome, f"--app={url}", "--start-fullscreen",
                          f"--user-data-dir={Path.home() / '.jarvis-hud-chrome'}",
                          "--autoplay-policy=no-user-gesture-required"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        webbrowser.open(url)


def run(open_browser=True):
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), partial(Handler, directory=str(WEB)))
    except OSError:
        print(f"Jarvis is already running at http://localhost:{PORT}")
        if open_browser:
            open_window(f"http://localhost:{PORT}")
        return
    url = f"http://localhost:{PORT}"
    print(f"J.A.R.V.I.S. online at {url}  (voice: {VOICE or 'default'})  Ctrl+C to shut down.")
    if open_browser:
        threading.Timer(0.6, open_window, args=[url]).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        say("Powering down. Goodbye.")
        print("\nJarvis offline.")


# ---------------------------------------------------------------- login item
def install():
    if sys.platform != "darwin":
        sys.exit("--install only works on a Mac.")
    PLIST.parent.mkdir(parents=True, exist_ok=True)
    python = shutil.which("python3") or sys.executable
    plist = {
        "Label": LABEL,
        "ProgramArguments": [python, str(HERE / "jarvis.py")],
        "RunAtLoad": True,
        "WorkingDirectory": str(HERE),
        "StandardOutPath": str(Path.home() / "Library/Logs/jarvis-hud.log"),
        "StandardErrorPath": str(Path.home() / "Library/Logs/jarvis-hud.log"),
    }
    with open(PLIST, "wb") as f:
        plistlib.dump(plist, f)
    subprocess.run(["launchctl", "unload", str(PLIST)], capture_output=True)
    subprocess.run(["launchctl", "load", str(PLIST)])
    print(f"Done. Jarvis will greet you every time you log in.\n(Login item: {PLIST})")
    say("Installation complete. I'll see you when you log in.")


def uninstall():
    if PLIST.exists():
        subprocess.run(["launchctl", "unload", str(PLIST)], capture_output=True)
        PLIST.unlink()
        print("Removed. Jarvis won't start at login anymore.")
    else:
        print("Jarvis wasn't set to start at login.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="J.A.R.V.I.S. HUD launcher")
    p.add_argument("--install", action="store_true", help="start Jarvis automatically at login")
    p.add_argument("--uninstall", action="store_true", help="stop starting at login")
    p.add_argument("--no-window", action="store_true", help="run the server without opening a window")
    p.add_argument("--say", metavar="TEXT", help="just say something and exit")
    a = p.parse_args()
    if a.install:
        install()
    elif a.uninstall:
        uninstall()
    elif a.say:
        say(a.say)
        if _say_proc:
            _say_proc.wait()
    else:
        run(open_browser=not a.no_window)
