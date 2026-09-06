"""Day 9 Imported Documents and Scene provenance fields

Revision ID: 009_imported_documents
Revises: 008_project_settings
Create Date: 2026-09-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '009_imported_documents'
down_revision = '008_project_settings'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create imported_documents table
    op.create_table(
        'imported_documents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='UPLOADED'),
        sa.Column('parser_version', sa.String(length=50), nullable=False, server_default='1.0.0'),
        sa.Column('scene_detection_version', sa.String(length=50), nullable=False, server_default='1.0.0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('character_count', sa.Integer(), nullable=True),
        sa.Column('scene_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_imported_documents_project_id', 'imported_documents', ['project_id'])

    # 2. Add provenance columns to scenes table
    op.add_column('scenes', sa.Column('source_document_id', sa.String(length=36), nullable=True))
    op.add_column('scenes', sa.Column('source_page_start', sa.Integer(), nullable=True))
    op.add_column('scenes', sa.Column('source_page_end', sa.Integer(), nullable=True))
    op.add_column('scenes', sa.Column('source_type', sa.String(length=50), nullable=False, server_default='MANUAL'))

    op.create_foreign_key('fk_scenes_source_document_id', 'scenes', 'imported_documents', ['source_document_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_scenes_source_document_id', 'scenes', ['source_document_id'])

def downgrade() -> None:
    op.drop_constraint('fk_scenes_source_document_id', 'scenes', type_='foreignkey')
    op.drop_index('ix_scenes_source_document_id', table_name='scenes')
    op.drop_column('scenes', 'source_type')
    op.drop_column('scenes', 'source_page_end')
    op.drop_column('scenes', 'source_page_start')
    op.drop_column('scenes', 'source_document_id')

    op.drop_index('ix_imported_documents_project_id', table_name='imported_documents')
    op.drop_table('imported_documents')
