import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_MODE = os.getenv("APP_MODE", "development").strip().lower()
IS_DEMO = APP_MODE == "demo"


def application_dir() -> Path:
    """Return the writable directory placed next to the packaged executable."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return PROJECT_ROOT


def bundled_resource(relative_path: str) -> Path:
    """Resolve source files and PyInstaller bundled resources consistently."""
    bundle_root = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT))
    return (bundle_root / relative_path).resolve()


def demo_database_path() -> Path:
    configured_path = os.getenv("DEMO_DATABASE_PATH")
    if configured_path:
        return Path(configured_path).expanduser().resolve()
    return application_dir() / "news.db"


def frontend_dist_path() -> Path:
    configured_path = os.getenv("FRONTEND_DIST_PATH")
    if configured_path:
        return Path(configured_path).expanduser().resolve()
    if getattr(sys, "frozen", False):
        return bundled_resource("web")
    return PROJECT_ROOT / "xwzx-news" / "dist"
