"""restore project column defaults

Revision ID: f1a2b3c4d5e6
Revises: ccf53727dcae
Create Date: 2026-10-01 21:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: str | Sequence[str] | None = "ccf53727dcae"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Restore server defaults declared on the Project model."""
    op.alter_column(
        "projects",
        "color",
        existing_type=sa.String(length=20),
        server_default="blue",
        existing_nullable=False,
    )
    op.alter_column(
        "projects",
        "status",
        existing_type=sa.String(length=20),
        server_default="active",
        existing_nullable=False,
    )


def downgrade() -> None:
    """Drop the restored server defaults."""
    op.alter_column(
        "projects",
        "color",
        existing_type=sa.String(length=20),
        server_default=None,
        existing_nullable=False,
    )
    op.alter_column(
        "projects",
        "status",
        existing_type=sa.String(length=20),
        server_default=None,
        existing_nullable=False,
    )
