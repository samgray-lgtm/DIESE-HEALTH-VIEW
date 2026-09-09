"""
DIESE Health View
=================
Wall display for the Health team's practitioner schedule.

  /            serves board.html, the display itself
  /schedule    fetches the DIESE report server-side and returns it
  /health      returns "ok", handy for checking the service is awake

The page and its data come from the same origin, so the browser never
applies CORS rules to the fetch.

Requirements:
    pip install flask flask-cors requests gunicorn

Render settings:
    Build command:  pip install -r requirements.txt
    Start command:  gunicorn diese_proxy:app

Repository layout - all three files sit together in the repository root,
and diese_proxy.py looks for board.html next to itself:
    diese_proxy.py
    board.html
    requirements.txt
"""

import os
from urllib.parse import urlparse

import requests
from flask import Flask, Response, abort, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Configuration -----------------------------------------------------------

# Only these hosts may be fetched, so the service cannot be used as an
# open proxy for arbitrary websites.
ALLOWED_HOSTS = {"audocuments.diesesoftware.com"}

REPORTS = {
    # Health team: columns are practitioners, not venues. Empty time comes
    # through as "Not Available" entries, often spanning 00:00-23:59; the
    # board draws those as background bands rather than appointments.
    "health": (
        "https://tab.diesesoftware.com/sp-UyVSZARq-AjVSNQw5-VhxWVQNCXEw=-BTYFalVg"
        "?modePartage=1"
        "&idSM=509"
        "&mode=html"
        "&idUtilisateur=1"
        "&idProds="
        "&ta=233,234,240,241,237,239,238,275,274,259,262,263,264,265,277,278,279,258,243,244,245,246"
        "&tp=12"
        "&lieux=360,347,350,351,366,352,368,381,367"
        "&statuts=3,1,4"
        "&date_from=2026-01-01"
        "&date_to=2030-12-31"
        "&idCustom=n59b6pj9pc248166780fghgk0qb69ici70gpo3fo05ljpipk031788925690"
        "&externe=1"
    ),
}

DEFAULT_REPORT = "health"
TIMEOUT_SECONDS = 20
PORT = int(os.environ.get("PORT", 5050))

# -----------------------------------------------------------------------------


def _host_allowed(url: str) -> bool:
    try:
        return urlparse(url).netloc.lower() in ALLOWED_HOSTS
    except ValueError:
        return False


def _no_cache(response: Response) -> Response:
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


@app.route("/")
def board():
    """Serve the health team board."""
    return _no_cache(send_from_directory(BASE_DIR, "board.html"))


@app.route("/health")
def health():
    return Response("ok", mimetype="text/plain")


@app.route("/schedule")
def schedule():
    """Fetch the DIESE report and hand it back to the board."""
    url = request.args.get("url")

    if url:
        if not _host_allowed(url):
            abort(403, description="That host is not on the allow list.")
    else:
        name = request.args.get("report", DEFAULT_REPORT)
        url = REPORTS.get(name)
        if not url:
            abort(404, description=f"No report registered under '{name}'.")

    try:
        upstream = requests.get(url, timeout=TIMEOUT_SECONDS)
        upstream.raise_for_status()
    except requests.RequestException as exc:
        abort(502, description=f"Could not reach DIESE: {exc}")

    return _no_cache(
        Response(upstream.text, mimetype="text/html; charset=utf-8")
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
