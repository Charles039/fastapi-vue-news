import os
import socket
import sys
import threading
import time
import urllib.request
import webbrowser


os.environ["APP_MODE"] = "demo"
os.environ["CACHE_BACKEND"] = "memory"
os.environ.setdefault("SQL_ECHO", "false")

from config.runtime import demo_database_path, frontend_dist_path  # noqa: E402


def configure_console_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="backslashreplace")


def find_available_port() -> int:
    configured_port = os.getenv("DEMO_PORT")
    if configured_port:
        port = int(configured_port)
        if not 1 <= port <= 65535:
            raise ValueError("DEMO_PORT must be between 1 and 65535")
        return port

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(("127.0.0.1", 0))
        return server_socket.getsockname()[1]


def open_browser_when_ready(url: str) -> None:
    if os.getenv("DEMO_OPEN_BROWSER", "true").lower() == "false":
        return

    def wait_and_open():
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for _ in range(100):
            try:
                with opener.open(url, timeout=0.25):
                    webbrowser.open(url)
                    return
            except Exception:
                time.sleep(0.1)

    threading.Thread(target=wait_and_open, daemon=True).start()


def pause_after_error() -> None:
    if sys.stdin and sys.stdin.isatty():
        try:
            input("Press Enter to close this window...")
        except EOFError:
            pass


def main() -> int:
    configure_console_output()
    database_path = demo_database_path()
    frontend_path = frontend_dist_path()
    if not database_path.is_file():
        print(f"Startup failed: demo database not found: {database_path}")
        print("Extract the complete Release ZIP; do not copy only the EXE file.")
        pause_after_error()
        return 1
    if not (frontend_path / "index.html").is_file():
        print(f"Startup failed: frontend assets not found: {frontend_path}")
        print("Extract the complete Release ZIP and try again.")
        pause_after_error()
        return 1

    try:
        port = find_available_port()
        url = f"http://127.0.0.1:{port}"
        from main import app
        import uvicorn

        print("=" * 54)
        print("FastAPI + Vue News Demo")
        print(f"URL: {url}")
        print("Demo administrator: abc / 12345678")
        print(f"Portable database: {database_path}")
        print("Close this window or press Ctrl+C to stop the server.")
        print("=" * 54)
        open_browser_when_ready(url)
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=port,
            loop="asyncio",
            http="h11",
            access_log=False,
        )
        return 0
    except Exception as exc:
        print(f"Startup failed: {exc}")
        pause_after_error()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
