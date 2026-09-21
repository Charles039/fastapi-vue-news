import argparse
import asyncio
import os
import sys
from pathlib import Path


DEMO_ADMIN_USERNAME = "abc"
DEMO_ADMIN_PASSWORD = "12345678"


def configure_console_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="backslashreplace")


def configure_demo_environment(database_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"
    os.environ["APP_MODE"] = "demo"
    os.environ["CACHE_BACKEND"] = "memory"
    os.environ["DEMO_DATABASE_PATH"] = str(database_path)
    os.environ["ALEMBIC_DATABASE_URL"] = database_url
    os.environ["SQL_ECHO"] = "false"


def run_migrations(project_root: Path) -> None:
    from alembic import command
    from alembic.config import Config

    config = Config(str(project_root / "alembic.ini"))
    config.set_main_option("script_location", str(project_root / "alembic"))
    command.upgrade(config, "head")


async def seed_database() -> tuple[int, int]:
    from sqlalchemy import select

    from config.db_conf import AsyncSessionLocal, async_engine
    from models.users import User
    from scripts.seed_demo_news import seed_demo_news
    from utils.security import get_hash_password

    seed_result = await seed_demo_news()
    async with AsyncSessionLocal() as session:
        existing = await session.execute(
            select(User).where(User.username == DEMO_ADMIN_USERNAME)
        )
        admin = existing.scalar_one_or_none()
        if admin is None:
            session.add(
                User(
                    username=DEMO_ADMIN_USERNAME,
                    password=get_hash_password(DEMO_ADMIN_PASSWORD),
                    nickname="演示管理员",
                    is_admin=True,
                )
            )
        else:
            admin.password = get_hash_password(DEMO_ADMIN_PASSWORD)
            admin.is_admin = True
        await session.commit()
    await async_engine.dispose()
    return seed_result.inserted, seed_result.skipped


def build_database(output_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    output_path = output_path.expanduser().resolve()
    if output_path.exists():
        raise FileExistsError(f"输出文件已存在，请先删除后重试：{output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    configure_demo_environment(output_path)
    run_migrations(project_root)
    inserted, skipped = asyncio.run(seed_database())
    print(f"Demo database created: {output_path}")
    print(f"Demo news: inserted {inserted}, skipped {skipped} duplicates")
    print(f"Demo administrator: {DEMO_ADMIN_USERNAME} / {DEMO_ADMIN_PASSWORD}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成零依赖 Release 的 SQLite 数据库")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("demo-build/news.db"),
        help="SQLite 输出路径（默认：demo-build/news.db）",
    )
    return parser.parse_args()


def main() -> None:
    configure_console_output()
    args = parse_args()
    try:
        build_database(args.output)
    except Exception as exc:
        print(f"Failed to build demo database: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
