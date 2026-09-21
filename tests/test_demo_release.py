import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from utils.security import verify_password


def test_build_demo_database(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    database_path = tmp_path / "news.db"
    environment = os.environ.copy()
    environment.pop("DATABASE_URL", None)
    environment["APP_MODE"] = "demo"
    environment["CACHE_BACKEND"] = "memory"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.build_demo_database",
            "--output",
            str(database_path),
        ],
        cwd=project_root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    with sqlite3.connect(database_path) as connection:
        categories = connection.execute(
            "SELECT COUNT(*) FROM news_category"
        ).fetchone()[0]
        news_count = connection.execute("SELECT COUNT(*) FROM news").fetchone()[0]
        admin = connection.execute(
            "SELECT password, is_admin FROM user WHERE username = ?", ("abc",)
        ).fetchone()
        version = connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchone()[0]

    assert categories == 8
    assert news_count > 0
    assert admin is not None
    assert admin[1] == 1
    assert admin[0] != "12345678"
    assert verify_password("12345678", admin[0])
    assert version == "0004_create_notification"
