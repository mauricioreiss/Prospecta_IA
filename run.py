"""
Prospecta IA v2.0 - Development Runner
Starts Backend (FastAPI) and Frontend (Next.js) simultaneously
"""
import subprocess
import sys
import time
import os
import signal

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_DIR)

processes = []


def run_backend():
    """Start FastAPI backend"""
    print("Starting Backend FastAPI on port 8000...")
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=PROJECT_DIR,
        env={**os.environ, "PYTHONPATH": PROJECT_DIR}
    )


def run_frontend():
    """Start Next.js frontend"""
    print("Starting Frontend Next.js on port 3000...")
    frontend_dir = os.path.join(PROJECT_DIR, "frontend")

    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"

    return subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=frontend_dir,
        shell=sys.platform == "win32"
    )


def cleanup(signum=None, frame=None):
    """Clean up processes on exit"""
    print("\nShutting down...")
    for p in processes:
        try:
            p.terminate()
            p.wait(timeout=5)
        except Exception:
            p.kill()
    print("Done.")
    sys.exit(0)


def main():
    print("=" * 50)
    print("  PROSPECTA IA v2.0")
    print("  Clean Architecture Backend + Next.js Frontend")
    print("=" * 50)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # Start backend
    backend = run_backend()
    processes.append(backend)
    time.sleep(3)

    # Start frontend
    frontend = run_frontend()
    processes.append(frontend)
    time.sleep(3)

    print("\n" + "=" * 50)
    print("  System started!")
    print("=" * 50)
    print("\nFrontend: http://localhost:3000")
    print("Backend API: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop...\n")

    try:
        while True:
            if backend.poll() is not None:
                print("Backend stopped unexpectedly!")
                break
            if frontend.poll() is not None:
                print("Frontend stopped unexpectedly!")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()


if __name__ == "__main__":
    main()
