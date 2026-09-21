"""Insert the default news categories without overwriting existing rows."""

from typing import Sequence, Union
from datetime import datetime

from alembic import context, op
import sqlalchemy as sa


revision: str = "0003_seed_news_categories"
down_revision: Union[str, None] = "0002_add_user_is_admin"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_CATEGORIES = (
    (1, "头条"),
    (2, "社会"),
    (3, "国内"),
    (4, "国际"),
    (5, "娱乐"),
    (6, "体育"),
    (7, "科技"),
    (8, "财经"),
)


def upgrade() -> None:
    category = sa.table(
        "news_category",
        sa.column("name", sa.String(length=50)),
        sa.column("sort_order", sa.Integer()),
        sa.column("created_at", sa.DateTime()),
        sa.column("updated_at", sa.DateTime()),
    )
    connection = op.get_bind()
    if context.is_offline_mode():
        dialect_name = op.get_context().dialect.name
        for sort_order, name in DEFAULT_CATEGORIES:
            if dialect_name == "mssql":
                op.execute(
                    "IF NOT EXISTS (SELECT 1 FROM news_category "
                    f"WHERE name = N'{name}') BEGIN "
                    "INSERT INTO news_category "
                    "(name, sort_order, created_at, updated_at) "
                    f"VALUES (N'{name}', {sort_order}, GETDATE(), GETDATE()) END"
                )
            else:
                op.execute(
                    "INSERT INTO news_category "
                    "(name, sort_order, created_at, updated_at) "
                    f"SELECT '{name}', {sort_order}, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP "
                    "WHERE NOT EXISTS (SELECT 1 FROM news_category "
                    f"WHERE name = '{name}')"
                )
        return

    existing_names = set(connection.execute(sa.select(category.c.name)).scalars())
    seeded_at = datetime.now()

    for sort_order, name in DEFAULT_CATEGORIES:
        if name not in existing_names:
            connection.execute(
                category.insert().values(
                    name=name,
                    sort_order=sort_order,
                    created_at=seeded_at,
                    updated_at=seeded_at,
                )
            )


def downgrade() -> None:
    # 分类属于业务数据，可能已经被新闻引用；降级版本号时保留这些数据。
    pass
