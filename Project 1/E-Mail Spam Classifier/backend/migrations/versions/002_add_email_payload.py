"""Add body, body_html, spam_indicators, and internal_date to classified_emails

Revision ID: 002_add_email_payload
Revises: 001_initial_supabase_schema
Create Date: 2026-10-10 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_add_email_payload'
down_revision = '001_initial_supabase_schema'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('classified_emails', sa.Column('body', sa.Text(), nullable=True))
    op.add_column('classified_emails', sa.Column('body_html', sa.Text(), nullable=True))
    op.add_column('classified_emails', sa.Column('spam_indicators', sa.Text(), nullable=True))
    op.add_column('classified_emails', sa.Column('internal_date', sa.BigInteger(), nullable=True))
    op.create_index('idx_classified_emails_internal_date', 'classified_emails', ['internal_date'], unique=False)


def downgrade():
    op.drop_index('idx_classified_emails_internal_date', table_name='classified_emails')
    op.drop_column('classified_emails', 'internal_date')
    op.drop_column('classified_emails', 'spam_indicators')
    op.drop_column('classified_emails', 'body_html')
    op.drop_column('classified_emails', 'body')
