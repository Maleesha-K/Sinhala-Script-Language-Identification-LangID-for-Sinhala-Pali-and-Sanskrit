"""Cancellation of classification jobs and document processing

Revision ID: f6c3a9e1b524
Revises: e5b2d8f4a713
Create Date: 2026-10-08 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6c3a9e1b524'
down_revision: Union[str, Sequence[str], None] = 'e5b2d8f4a713'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # The enums store member names, matching the initial migration.
    with op.get_context().autocommit_block():
        for enum in ("jobstatus", "uploadstatus", "pagestatus"):
            op.execute(f"ALTER TYPE {enum} ADD VALUE IF NOT EXISTS 'CANCELLED'")
    # Set by the cancel endpoints; the workers stop at their next checkpoint.
    for table in ("classification_jobs", "documents"):
        op.add_column(
            table,
            sa.Column('cancel_requested', sa.Boolean(), nullable=False, server_default=sa.false()),
        )


def downgrade() -> None:
    """Downgrade schema."""
    for table in ("classification_jobs", "documents"):
        op.drop_column(table, 'cancel_requested')
    # Postgres cannot drop an enum value; record cancelled work as failed.
    op.execute("UPDATE classification_jobs SET status = 'FAILED' WHERE status = 'CANCELLED'")
    op.execute("UPDATE documents SET upload_status = 'FAILED' WHERE upload_status = 'CANCELLED'")
    op.execute("UPDATE document_pages SET status = 'FAILED' WHERE status = 'CANCELLED'")
