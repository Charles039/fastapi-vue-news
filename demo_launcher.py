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


def find_available_port() -> int:
    configured_port = os.getenv("DEMO_PORT")
    if configured_port:
        port = int(configured_port)
        if not 1 <= port <= 65535:
            raise ValueError("DEMO_PORT 必须位于 1 到 65535 之间")
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
            input("按 Enter 键关闭窗口……")
        except EOFError:
            pass


def main() -> int:
    database_path = demo_database_path()
    frontend_path = frontend_dist_path()
    if not database_path.is_file():
        print(f"启动失败：演示数据库不存在：{database_path}")
        print("请完整解压 Release ZIP，不要只复制 EXE 文件。")
        pause_after_error()
        return 1
    if not (frontend_path / "index.html").is_file():
        print(f"启动失败：前端资源不存在：{frontend_path}")
        print("请完整解压 Release ZIP 后重新运行。")
        pause_after_error()
        return 1

    try:
        port = find_available_port()
        url = f"http://127.0.0.1:{port}"
        from main import app
        import uvicorn

        print("=" * 54)
        print("FastAPI + Vue 新闻系统演示版")
        print(f"访问地址：{url}")
        print("演示管理员：abc / 12345678")
        print(f"便携数据库：{database_path}")
        print("关闭此窗口或按 Ctrl+C 即可停止服务。")
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
        print(f"启动失败：{exc}")
        pause_after_error()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
