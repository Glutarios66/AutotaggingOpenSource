# manage.py
import argparse
import subprocess
import sys
import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def run_command(command: list):
    """Runs a shell command and streams output."""
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        sys.exit(1)


# --- Commands ---

def start_server(reload: bool = False):
    """Start FastAPI server using uvicorn."""
    print("🚀 Starting AutotaggingOpenSource API server...")

    cmd = [
        "uvicorn",
        "main:app",
        "--host", "0.0.0.0",
        "--port", "8000"
    ]

    if reload:
        cmd.append("--reload")

    run_command(cmd)


def stop_server():
    """Stops uvicorn (simple kill for dev)."""
    print("🛑 Stopping server...")
    run_command(["pkill", "-f", "uvicorn"])


def health_check():
    """Checks if API is running."""
    print("🔍 Checking API health...")
    run_command(["curl", "http://localhost:8000/health"])


def docker_start():
    """Start Docker services."""
    print("🐳 Starting Docker services...")
    run_command(["docker", "compose", "up", "-d"])


def docker_stop():
    """Stop Docker services."""
    print("🛑 Stopping Docker services...")
    run_command(["docker", "compose", "down"])


def run_tests():
    """Run basic API test."""
    print("🧪 Running test request...")

    run_command([
        "curl",
        "-X", "POST",
        "http://localhost:8000/process",
        "-F", "file=@test.pdf"
    ])


# --- CLI Setup ---

def main():
    parser = argparse.ArgumentParser(description="AutotaggingOpenSource Management CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # start
    start_parser = subparsers.add_parser("start", help="Start API server")
    start_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    # stop
    subparsers.add_parser("stop", help="Stop API server")

    # dev (shortcut)
    subparsers.add_parser("dev", help="Start server in dev mode (--reload)")

    # health
    subparsers.add_parser("health", help="Check API health")

    # docker
    subparsers.add_parser("docker-start", help="Start Docker")
    subparsers.add_parser("docker-stop", help="Stop Docker")

    # test
    subparsers.add_parser("test", help="Run API test")

    args = parser.parse_args()

    if args.command == "start":
        start_server(reload=args.reload)

    elif args.command == "dev":
        start_server(reload=True)

    elif args.command == "stop":
        stop_server()

    elif args.command == "health":
        health_check()

    elif args.command == "docker-start":
        docker_start()

    elif args.command == "docker-stop":
        docker_stop()

    elif args.command == "test":
        run_tests()


if __name__ == "__main__":
    main()