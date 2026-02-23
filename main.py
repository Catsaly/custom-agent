"""
CodeCraft AI — Main Entry Point
Starts both FastAPI backend and Streamlit frontend.
"""
import subprocess
import sys
import os
import threading
import time
import signal
from app.config import settings


def start_fastapi():
    """Start the FastAPI backend server."""
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "app.api.server:app",
        "--host", settings.app_host,
        "--port", str(settings.app_port),
        "--reload" if settings.debug else "--no-reload",
    ])


def start_streamlit():
    """Start the Streamlit frontend."""
    time.sleep(2)  # Wait for FastAPI to start
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "app/streamlit_app.py",
        "--server.port", str(settings.streamlit_port),
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        "--theme.base", "dark",
        "--theme.primaryColor", "#6366f1",
        "--theme.backgroundColor", "#0f172a",
        "--theme.secondaryBackgroundColor", "#1e293b",
        "--theme.textColor", "#f8fafc",
    ])


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode == "api":
        print("🚀 Starting FastAPI backend...")
        start_fastapi()
    elif mode == "ui":
        print("⚡ Starting Streamlit frontend...")
        start_streamlit()
    else:
        print("⚡ CodeCraft AI starting...")
        print(f"   Backend:  http://localhost:{settings.app_port}")
        print(f"   Frontend: http://localhost:{settings.streamlit_port}")
        print(f"   API Docs: http://localhost:{settings.app_port}/docs")

        api_thread = threading.Thread(target=start_fastapi, daemon=True)
        api_thread.start()
        start_streamlit()
