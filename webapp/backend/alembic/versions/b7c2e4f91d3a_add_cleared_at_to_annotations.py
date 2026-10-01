"""Add cleared_at to Annotation

Revision ID: b7c2e4f91d3a
Revises: a01886d28c50
Create Date: 2026-10-01 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c2e4f91d3a'
down_revision: Union[str, Sequence[str], None] = 'a01886d28c50'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('annotations', sa.Column('cleared_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('annotations', 'cleared_at')
