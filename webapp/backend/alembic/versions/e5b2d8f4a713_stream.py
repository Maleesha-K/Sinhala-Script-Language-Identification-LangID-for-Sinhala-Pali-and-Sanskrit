"""Per-page language identification for streamed documents

Revision ID: e5b2d8f4a713
Revises: d4e8b1c6a902
Create Date: 2026-10-08 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5b2d8f4a713'
down_revision: Union[str, Sequence[str], None] = 'd4e8b1c6a902'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Classification model to run on each page as soon as it is OCR'd (None: OCR only).
    op.add_column('documents', sa.Column('lid_model', sa.String(length=128), nullable=True))
    # Set on the per-page jobs a document's OCR run queues.
    op.add_column('classification_jobs', sa.Column('page_number', sa.Integer(), nullable=True))
    op.add_column('classification_jobs', sa.Column('error_message', sa.Text(), nullable=True))
    op.create_index('ix_classification_jobs_document_id', 'classification_jobs', ['document_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_classification_jobs_document_id', table_name='classification_jobs')
    op.drop_column('classification_jobs', 'error_message')
    op.drop_column('classification_jobs', 'page_number')
    op.drop_column('documents', 'lid_model')
