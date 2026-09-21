"""Create per-user notifications."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_create_notification"
down_revision: Union[str, None] = "0003_seed_news_categories"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notification",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=30), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("news_id", sa.Integer(), nullable=True),
        sa.Column("news_title", sa.String(length=255), nullable=True),
        sa.Column("dedupe_key", sa.String(length=100), nullable=False),
        sa.Column("is_read", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], name=op.f("fk_notification_user_id_user")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notification")),
        sa.UniqueConstraint(
            "user_id", "dedupe_key", name="uq_notification_user_dedupe"
        ),
    )
    op.create_index(
        "idx_notification_news", "notification", ["news_id"], unique=False
    )
    op.create_index(
        "idx_notification_user_time",
        "notification",
        ["user_id", "updated_at"],
        unique=False,
    )
    op.create_index(
        "idx_notification_user_unread",
        "notification",
        ["user_id", "is_read"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("notification")

