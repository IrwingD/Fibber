"""
app.py
Entry point for the portable app.

Run as a script (python app.py) or as the compiled exe -- either way this:
  1. binds a free localhost port (never a fixed port, avoids conflicts)
  2. starts a Flask server bound ONLY to 127.0.0.1 (not reachable on the LAN)
  3. opens the UI in Edge "app mode" (chromeless window), falling back to
     the default browser if Edge isn't found
  4. watches for a heartbeat ping from the page; if the tab is closed and
     pings stop, the process exits on its own -- no lingering background
     server, no tray icon needed.

Settings (last-used schema) are saved as settings.json next to the exe,
so the whole app -- code + your saved schema -- travels together as one
folder (USB stick, zip, network share, wherever).
"""

import csv
import io
import json
import os
import secrets
import socket
import subprocess
import sys
import threading
import time
import webbrowser

from flask import Flask, Response, jsonify, request, send_from_directory

import faker_api

# ---------------------------------------------------------------------------
# Paths: work identically whether run as `python app.py` or as a frozen
# PyInstaller --onedir exe.
# ---------------------------------------------------------------------------
if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)      # folder the exe lives in
    BASE_DIR = getattr(sys, "_MEIPASS", APP_DIR)    # where bundled data was unpacked
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = APP_DIR

STATIC_DIR = os.path.join(BASE_DIR, "static")
SETTINGS_PATH = os.path.join(APP_DIR, "settings.json")

# ---------------------------------------------------------------------------
# Lightweight local-only auth: a random token is baked into the URL the
# browser opens. The page reads it from the URL and sends it back as a
# header on every API call. Anything without the right token gets a 403.
# This just stops some other process on the machine from poking the
# server while it's running -- it's not meant to survive real attackers.
# ---------------------------------------------------------------------------
APP_TOKEN = secrets.token_hex(16)

app = Flask(__name__, static_folder=None)

STARTED = time.time()
last_heartbeat = time.time()
HEARTBEAT_TIMEOUT_SECONDS = 20   # no ping for this long => assume tab closed
GRACE_PERIOD_SECONDS = 30        # don't watch for pings until page has loaded


@app.before_request
def check_token():
    if request.path.startswith("/api/"):
        if request.headers.get("X-App-Token") != APP_TOKEN:
            return ("Forbidden", 403)


# ---------------------------------------------------------------------------
# Static UI
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(STATIC_DIR, path)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
@app.route("/api/heartbeat", methods=["POST"])
def heartbeat():
    global last_heartbeat
    last_heartbeat = time.time()
    return ("", 204)


@app.route("/api/locales")
def locales():
    return jsonify(faker_api.COMMON_LOCALES)


@app.route("/api/providers")
def providers():
    locale = request.args.get("locale", "en_US")
    return jsonify(faker_api.get_providers(locale))


@app.route("/api/preview", methods=["POST"])
def preview():
    data = request.get_json(force=True)
    fields = data.get("fields", [])
    locale = data.get("locale", "en_US")
    seed = data.get("seed")
    rows = faker_api.generate_rows(fields, 10, locale, seed)
    return jsonify(rows)


@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)
    fmt = data.get("format", "csv")
    rows = max(1, min(int(data.get("rows", 1000)), 500_000))
    fields = data.get("fields", [])
    locale = data.get("locale", "en_US")
    seed = data.get("seed")

    if fmt == "json":
        def gen_json():
            yield "["
            fake = faker_api.make_faker(locale, seed)
            for i in range(rows):
                row = faker_api.generate_one(fake, fields)
                yield ("," if i else "") + json.dumps(row, default=str)
            yield "]"

        return Response(
            gen_json(),
            mimetype="application/json",
            headers={"Content-Disposition": "attachment; filename=synthetic_data.json"},
        )

    def gen_csv():
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([f["name"] for f in fields])
        yield buf.getvalue()
        buf.seek(0)
        buf.truncate(0)

        fake = faker_api.make_faker(locale, seed)
        for _ in range(rows):
            row = faker_api.generate_one(fake, fields)
            writer.writerow([row[f["name"]] for f in fields])
            yield buf.getvalue()
            buf.seek(0)
            buf.truncate(0)

    return Response(
        gen_csv(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=synthetic_data.csv"},
    )


@app.route("/api/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        with open(SETTINGS_PATH, "w", encoding="utf-8") as fh:
            json.dump(request.get_json(force=True), fh, indent=2)
        return ("", 204)

    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, encoding="utf-8") as fh:
            return jsonify(json.load(fh))
    return jsonify(None)


# ---------------------------------------------------------------------------
# Lifecycle: self-terminate once the browser stops pinging us
# ---------------------------------------------------------------------------
def watch_heartbeat():
    while True:
        time.sleep(5)
        if time.time() - STARTED < GRACE_PERIOD_SECONDS:
            continue
        if time.time() - last_heartbeat > HEARTBEAT_TIMEOUT_SECONDS:
            os._exit(0)


# ---------------------------------------------------------------------------
# Launch helpers
# ---------------------------------------------------------------------------
def free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def open_browser(url: str):
    edge_candidates = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
    ]
    for path in edge_candidates:
        if os.path.exists(path):
            try:
                subprocess.Popen([path, f"--app={url}"])
                return
            except OSError:
                pass
    # Fallback: whatever the OS considers the default browser
    webbrowser.open(url)


if __name__ == "__main__":
    port = free_port()
    url = f"http://127.0.0.1:{port}/?token={APP_TOKEN}"

    threading.Thread(target=watch_heartbeat, daemon=True).start()
    threading.Timer(1.0, open_browser, args=(url,)).start()

    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
