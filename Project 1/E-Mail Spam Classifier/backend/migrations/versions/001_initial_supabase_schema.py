"""Initial schema for Supabase Auth and multi-user Gmail monitoring

Revision ID: 001_initial_supabase_schema
Revises: 
Create Date: 2026-10-09 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_initial_supabase_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 1. users table (stores application profile mapped to Supabase Auth UUID)
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # 2. gmail_connections table (stores per-user encrypted Gmail tokens and watch status)
    op.create_table(
        'gmail_connections',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('gmail_address', sa.String(length=255), nullable=True),
        sa.Column('encrypted_credentials_json', sa.Text(), nullable=False),
        sa.Column('history_id', sa.String(length=255), nullable=True),
        sa.Column('watch_expiration', sa.BigInteger(), nullable=True),
        sa.Column('monitoring_status', sa.String(length=50), server_default='inactive', nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('gmail_address'),
        sa.UniqueConstraint('user_id')
    )

    # 3. classified_emails table (stores per-user isolated email metadata and predictions)
    op.create_table(
        'classified_emails',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('message_id', sa.String(length=255), nullable=False),
        sa.Column('sender', sa.String(length=255), nullable=True),
        sa.Column('subject', sa.Text(), nullable=True),
        sa.Column('snippet', sa.Text(), nullable=True),
        sa.Column('prediction', sa.String(length=50), nullable=True),
        sa.Column('strength', sa.String(length=50), nullable=True),
        sa.Column('timestamp', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'message_id', name='_user_message_uc')
    )
    op.create_index('idx_classified_emails_user_id', 'classified_emails', ['user_id'], unique=False)


def downgrade():
    op.drop_index('idx_classified_emails_user_id', table_name='classified_emails')
    op.drop_table('classified_emails')
    op.drop_table('gmail_connections')
    op.drop_table('users')
