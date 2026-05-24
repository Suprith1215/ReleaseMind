"""
ReleaseMind — root entry point.
Adds the backend package to sys.path then launches the Flask app.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "ReleaseMind-Core", "backend"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "ReleaseMind-Core", "backend", "services"))

from api import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7000))
    app.run(host="0.0.0.0", port=port)
