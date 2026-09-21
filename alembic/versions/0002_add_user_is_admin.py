"""Add the administrator flag to users."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_add_user_is_admin"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user",
        sa.Column(
            "is_admin",
            sa.Boolean(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    with op.batch_alter_table("user") as batch_op:
        batch_op.drop_column("is_admin", mssql_drop_default=True)

