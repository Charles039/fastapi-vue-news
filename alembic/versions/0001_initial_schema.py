"""Create the initial application schema without administrator privileges."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password", sa.String(length=255), nullable=False),
        sa.Column("nickname", sa.String(length=50), nullable=True),
        sa.Column("avatar", sa.String(length=255), nullable=True),
        sa.Column(
            "gender",
            sa.Enum("male", "female", "unknown", name="user_gender"),
            nullable=True,
        ),
        sa.Column("bio", sa.String(length=500), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user")),
        sa.UniqueConstraint("username", name=op.f("uq_user_username")),
    )
    op.create_index("phone_UNIQUE", "user", ["phone"], unique=False)
    op.create_index("username_UNIQUE", "user", ["username"], unique=False)

    op.create_table(
        "news_category",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_news_category")),
        sa.UniqueConstraint("name", name=op.f("uq_news_category_name")),
    )

    op.create_table(
        "news",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("image", sa.String(length=255), nullable=True),
        sa.Column("author", sa.String(length=50), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("views", sa.Integer(), nullable=False),
        sa.Column("publish_time", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["news_category.id"],
            name=op.f("fk_news_category_id_news_category"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_news")),
    )
    op.create_index("fk_news_category_idx", "news", ["category_id"], unique=False)
    op.create_index("idx_publish_time", "news", ["publish_time"], unique=False)

    op.create_table(
        "user_token",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_user_token_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_token")),
        sa.UniqueConstraint("token", name=op.f("uq_user_token_token")),
    )
    op.create_index(
        "fk_user_token_user_idx", "user_token", ["user_id"], unique=False
    )
    op.create_index("token_UNIQUE", "user_token", ["token"], unique=False)

    op.create_table(
        "favorite",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("news_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["news_id"], ["news.id"], name=op.f("fk_favorite_news_id_news")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_favorite_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_favorite")),
        sa.UniqueConstraint("user_id", "news_id", name="user_news_unique"),
    )
    op.create_index("fk_favorite_news_idx", "favorite", ["news_id"], unique=False)
    op.create_index("fk_favorite_user_idx", "favorite", ["user_id"], unique=False)

    op.create_table(
        "history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("news_id", sa.Integer(), nullable=False),
        sa.Column("view_time", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["news_id"], ["news.id"], name=op.f("fk_history_news_id_news")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_history_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_history")),
    )
    op.create_index("fk_history_news_idx", "history", ["news_id"], unique=False)
    op.create_index("fk_history_user_idx", "history", ["user_id"], unique=False)
    op.create_index("idx_view_time", "history", ["view_time"], unique=False)


def downgrade() -> None:
    op.drop_table("history")
    op.drop_table("favorite")
    op.drop_table("user_token")
    op.drop_table("news")
    op.drop_table("news_category")
    op.drop_table("user")

