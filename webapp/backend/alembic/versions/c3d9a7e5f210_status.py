"""Add FAILED to the document upload status; merge the payments and annotations heads

Revision ID: c3d9a7e5f210
Revises: b123456789ab, b7c2e4f91d3a
Create Date: 2026-10-06 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c3d9a7e5f210'
down_revision: Union[str, Sequence[str], None] = ('b123456789ab', 'b7c2e4f91d3a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # The enum stores member names, matching the initial migration.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE uploadstatus ADD VALUE IF NOT EXISTS 'FAILED'")


def downgrade() -> None:
    """Downgrade schema."""
    # Postgres cannot drop an enum value; move failed rows back to DELETED.
    op.execute("UPDATE documents SET upload_status = 'DELETED' WHERE upload_status = 'FAILED'")
