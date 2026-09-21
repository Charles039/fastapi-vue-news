from pathlib import Path
from io import StringIO

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from models.base import Base
from models.news import Category
from models.notification import Notification
from models.users import User
from scripts.check_existing_database import DEFAULT_CATEGORIES, inspect_existing_schema


def alembic_config(project_root: Path) -> Config:
    config = Config(str(project_root / "alembic.ini"))
    config.set_main_option("script_location", str(project_root / "alembic"))
    return config


def test_upgrade_empty_database_to_head(tmp_path, monkeypatch):
    project_root = Path(__file__).resolve().parents[1]
    database_path = tmp_path / "migration-test.db"
    async_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("ALEMBIC_DATABASE_URL", async_url)

    config = alembic_config(project_root)
    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    inspector = inspect(engine)
    assert {
        "alembic_version", "user", "user_token", "news_category",
        "news", "favorite", "history", "notification",
    }.issubset(inspector.get_table_names())
    assert "is_admin" in {
        column["name"] for column in inspector.get_columns("user")
    }

    with engine.connect() as connection:
        categories = set(
            connection.execute(text("SELECT name FROM news_category")).scalars()
        )
        result = inspect_existing_schema(connection)
    assert categories == DEFAULT_CATEGORIES
    assert result.errors == []
    assert result.warnings == []
    command.check(config)

    # 分类降级不删业务数据，再次升级也不能产生重复分类。
    command.downgrade(config, "0002_add_user_is_admin")
    command.upgrade(config, "head")
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT COUNT(*) FROM news_category")) == 8

    command.downgrade(config, "base")
    assert not {
        "user", "user_token", "news_category", "news", "favorite", "history"
    }.intersection(inspect(engine).get_table_names())
    engine.dispose()


def test_generate_mssql_offline_upgrade_sql(monkeypatch):
    project_root = Path(__file__).resolve().parents[1]
    monkeypatch.setenv(
        "ALEMBIC_DATABASE_URL",
        "mssql+aioodbc://localhost/news?driver=ODBC+Driver+17+for+SQL+Server",
    )
    output = StringIO()
    config = Config(str(project_root / "alembic.ini"), output_buffer=output)
    config.set_main_option("script_location", str(project_root / "alembic"))

    command.upgrade(config, "head", sql=True)

    sql = output.getvalue()
    assert "CREATE TABLE [user]" in sql
    assert "ALTER TABLE [user] ADD is_admin" in sql
    assert "CREATE TABLE notification" in sql
    assert "IF NOT EXISTS" in sql
    assert "财经" in sql


def test_stamp_existing_database_preserves_business_data(tmp_path, monkeypatch):
    project_root = Path(__file__).resolve().parents[1]
    database_path = tmp_path / "existing.db"
    sync_url = f"sqlite:///{database_path.as_posix()}"
    async_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"
    engine = create_engine(sync_url)
    Base.metadata.create_all(engine)
    Notification.__table__.drop(engine)
    with Session(engine) as session:
        session.add(User(username="kept-user", password="existing-hash", is_admin=True))
        session.add_all(
            Category(name=name, sort_order=sort_order)
            for sort_order, name in enumerate(sorted(DEFAULT_CATEGORIES), start=1)
        )
        session.commit()
    engine.dispose()

    monkeypatch.setenv("ALEMBIC_DATABASE_URL", async_url)
    config = alembic_config(project_root)
    command.stamp(config, "0003_seed_news_categories")
    command.upgrade(config, "head")

    engine = create_engine(sync_url)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT COUNT(*) FROM [user]")) == 1
        assert connection.scalar(text("SELECT COUNT(*) FROM news_category")) == 8
        assert "notification" in inspect(connection).get_table_names()
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
            "0004_create_notification"
        )
    engine.dispose()
