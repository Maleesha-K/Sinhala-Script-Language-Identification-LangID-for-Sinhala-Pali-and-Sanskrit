"""Add payment_transactions table

Revision ID: b123456789ab
Revises: a01886d28c50
Create Date: 2026-10-01 12:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b123456789ab'
down_revision: Union[str, Sequence[str], None] = 'a01886d28c50'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.execute("""
    DO $$ BEGIN
        CREATE TYPE paymentgateway AS ENUM ('payhere', 'manual');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """)
    op.execute("""
    DO $$ BEGIN
        CREATE TYPE paymentstatus AS ENUM ('pending', 'completed', 'failed', 'cancelled', 'refunded');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """)

    op.create_table(
        'payment_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('gateway', postgresql.ENUM('payhere', 'manual', name='paymentgateway', create_type=False), nullable=False, server_default='payhere'),
        sa.Column('order_id', sa.String(length=64), nullable=False),
        sa.Column('payhere_payment_id', sa.String(length=64), nullable=True),
        sa.Column('package_name', sa.String(length=128), nullable=False),
        sa.Column('amount_lkr', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='LKR'),
        sa.Column('credits_amount', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'completed', 'failed', 'cancelled', 'refunded', name='paymentstatus', create_type=False), nullable=False, server_default='pending'),
        sa.Column('payment_method', sa.String(length=64), nullable=True),
        sa.Column('raw_payload', sa.JSON(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index(op.f('ix_payment_transactions_user_id'), 'payment_transactions', ['user_id'], unique=False)
    op.create_index(op.f('ix_payment_transactions_order_id'), 'payment_transactions', ['order_id'], unique=True)
    op.create_index(op.f('ix_payment_transactions_payhere_payment_id'), 'payment_transactions', ['payhere_payment_id'], unique=True)
    op.create_index(op.f('ix_payment_transactions_status'), 'payment_transactions', ['status'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_payment_transactions_status'), table_name='payment_transactions')
    op.drop_index(op.f('ix_payment_transactions_payhere_payment_id'), table_name='payment_transactions')
    op.drop_index(op.f('ix_payment_transactions_order_id'), table_name='payment_transactions')
    op.drop_index(op.f('ix_payment_transactions_user_id'), table_name='payment_transactions')
    op.drop_table('payment_transactions')
    op.execute("DROP TYPE IF EXISTS paymentgateway")
    op.execute("DROP TYPE IF EXISTS paymentstatus")
