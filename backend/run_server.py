"""
Server runner script for Edge AI Smart EV Charging Station Optimizer.
"""

import sys
import os

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import uvicorn
from app.config import settings

if __name__ == "__main__":
    print(f"[*] Starting Edge AI Smart EV Charging Station Backend on http://{settings.HOST}:{settings.PORT}")
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=False)
