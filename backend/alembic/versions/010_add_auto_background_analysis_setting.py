"""Add auto_background_analysis_enabled to project_settings

Revision ID: 010_add_auto_background_analysis_setting
Revises: 009_imported_documents
Create Date: 2026-09-07 14:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '010_add_auto_background_analysis_setting'
down_revision = '009_imported_documents'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column(
        'project_settings',
        sa.Column('auto_background_analysis_enabled', sa.Boolean(), nullable=False, server_default='true')
    )

def downgrade() -> None:
    op.drop_column('project_settings', 'auto_background_analysis_enabled')
