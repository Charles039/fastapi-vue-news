import asyncio
from dataclasses import dataclass, field

from sqlalchemy import inspect, text

from config.db_conf import async_engine


EXPECTED_COLUMNS = {
    "user": {
        "id", "username", "password", "nickname", "avatar", "gender",
        "bio", "phone", "is_admin", "created_at", "updated_at",
    },
    "user_token": {"id", "user_id", "token", "expires_at", "created_at"},
    "news_category": {"id", "name", "sort_order", "created_at", "updated_at"},
    "news": {
        "id", "title", "description", "content", "image", "author",
        "category_id", "views", "publish_time", "created_at", "updated_at",
    },
    "favorite": {"id", "user_id", "news_id", "created_at"},
    "history": {"id", "user_id", "news_id", "view_time"},
}

EXPECTED_INDEXES = {
    "user": {"username_UNIQUE", "phone_UNIQUE"},
    "user_token": {"token_UNIQUE", "fk_user_token_user_idx"},
    "news": {"fk_news_category_idx", "idx_publish_time"},
    "favorite": {"fk_favorite_user_idx", "fk_favorite_news_idx"},
    "history": {"fk_history_user_idx", "fk_history_news_idx", "idx_view_time"},
}

EXPECTED_UNIQUES = {
    "user": {("username",)},
    "user_token": {("token",)},
    "news_category": {("name",)},
    "favorite": {("news_id", "user_id")},
}

DEFAULT_CATEGORIES = {"头条", "社会", "国内", "国际", "娱乐", "体育", "科技", "财经"}


@dataclass
class CheckResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def inspect_existing_schema(connection) -> CheckResult:
    inspector = inspect(connection)
    result = CheckResult()
    existing_tables = set(inspector.get_table_names())

    for table_name, required_columns in EXPECTED_COLUMNS.items():
        if table_name not in existing_tables:
            result.errors.append(f"缺少数据表: {table_name}")
            continue

        actual_columns = {item["name"] for item in inspector.get_columns(table_name)}
        for column_name in sorted(required_columns - actual_columns):
            result.errors.append(f"表 {table_name} 缺少字段: {column_name}")

    for table_name, expected_indexes in EXPECTED_INDEXES.items():
        if table_name not in existing_tables:
            continue
        actual_indexes = {item["name"] for item in inspector.get_indexes(table_name)}
        for index_name in sorted(expected_indexes - actual_indexes):
            result.warnings.append(f"表 {table_name} 缺少索引: {index_name}")

    for table_name, expected_groups in EXPECTED_UNIQUES.items():
        if table_name not in existing_tables:
            continue
        unique_groups = {
            tuple(sorted(item.get("column_names") or ()))
            for item in inspector.get_unique_constraints(table_name)
        }
        unique_groups.update(
            tuple(sorted(item.get("column_names") or ()))
            for item in inspector.get_indexes(table_name)
            if item.get("unique")
        )
        for expected_group in expected_groups:
            normalized = tuple(sorted(expected_group))
            if normalized not in unique_groups:
                columns = ", ".join(expected_group)
                result.warnings.append(
                    f"表 {table_name} 缺少唯一约束或唯一索引: ({columns})"
                )

    if "news_category" in existing_tables:
        existing_categories = set(
            connection.execute(text("SELECT name FROM news_category")).scalars()
        )
        for name in sorted(DEFAULT_CATEGORIES - existing_categories):
            result.warnings.append(f"缺少默认新闻分类: {name}")

    return result


async def check_database() -> CheckResult:
    async with async_engine.connect() as connection:
        return await connection.run_sync(inspect_existing_schema)


async def async_main() -> int:
    try:
        result = await check_database()
    except Exception as exc:
        print(f"无法连接或检查数据库: {exc}")
        return 2

    if result.errors:
        print("结构检查未通过，不能接管现有数据库：")
        for message in result.errors:
            print(f"  [错误] {message}")
    else:
        print("关键表和字段检查通过。")

    if result.warnings:
        print("需要人工确认的警告：")
        for message in result.warnings:
            print(f"  [警告] {message}")

    if not result.errors:
        print(
            "确认警告可接受后，可手动执行: "
            "alembic stamp 0003_seed_news_categories，随后执行 alembic upgrade head"
        )
    return 1 if result.errors else 0


def main() -> None:
    raise SystemExit(asyncio.run(async_main()))


if __name__ == "__main__":
    main()
