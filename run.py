"""
Application Runner: Internship Discovery & Skill-Gap Recommendation Engine

Starts the local Flask development web server.
Usage:
    python run.py
"""

import os
import sys
from pathlib import Path

# Ensure the project root is in the Python search path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import create_app
from app.config import DB_PATH

app = create_app()

if __name__ == "__main__":
    # Verify database file exists before launching
    if not DB_PATH.exists():
        print(f"[WARNING] Database not found at '{DB_PATH}'.")
        print("Initializing database with demo seed data...")
        from scripts.setup_db import main as setup_db_main
        setup_db_main()

    host = os.environ.get("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_RUN_PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "t")

    print("\n" + "=" * 70)
    print(" INTERNSHIP DISCOVERY & SKILL-GAP RECOMMENDATION ENGINE")
    print(" Milestone 5: Web Application & Student Discovery Portal")
    print("=" * 70)
    print(f" Local Web Server: http://{host}:{port}/")
    print(f" Student Portal:   http://{host}:{port}/profile")
    print(f" Health Check:     http://{host}:{port}/health")
    print(f" REST API:         http://{host}:{port}/api/internships")
    print(" Press Ctrl+C to stop the development server.")
    print("=" * 70 + "\n")

    app.run(host=host, port=port, debug=debug)
