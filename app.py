#!/usr/bin/env python3
"""EnvTools - Development Environment Manager (Web Edition)"""

import os
import traceback
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from backend.core.database import init_db
from backend.api import register_blueprints

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "frontend", "dist")

app = Flask(__name__, static_folder=DIST_DIR, static_url_path="")
CORS(app)

init_db()
register_blueprints(app)


@app.errorhandler(Exception)
def handle_exception(e):
    traceback.print_exc()
    return jsonify({"error": str(e)}), 500


@app.route("/")
def serve_index():
    return send_from_directory(DIST_DIR, "index.html")


@app.errorhandler(404)
def fallback(e):
    index = os.path.join(DIST_DIR, "index.html")
    if os.path.exists(index):
        return send_from_directory(DIST_DIR, "index.html")
    return jsonify({"error": "Not found"}), 404


if __name__ == "__main__":
    print("=" * 50)
    print("  EnvTools - Development Environment Manager ")
    print("  http://localhost:18090")
    print("=" * 50)
    app.run(host="0.0.0.0", port=18090, debug=True)
