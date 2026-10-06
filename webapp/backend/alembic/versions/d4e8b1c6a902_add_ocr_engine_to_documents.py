"""Add ocr_engine to documents

Revision ID: d4e8b1c6a902
Revises: c3d9a7e5f210
Create Date: 2026-10-06 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e8b1c6a902'
down_revision: Union[str, Sequence[str], None] = 'c3d9a7e5f210'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Every existing document was OCR'd by Tesseract, the only engine until now.
    op.add_column(
        'documents',
        sa.Column('ocr_engine', sa.String(length=64), nullable=False, server_default='tesseract'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('documents', 'ocr_engine')
