"""Project Settings and Story World Rules Schema

Revision ID: 008_project_settings
Revises: 007_day7_unified_runs
Create Date: 2026-09-05 21:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '008_project_settings'
down_revision = '007_day7_unified_runs'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'project_settings',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('reality_level', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('continuity_strictness', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('settings_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', name='uq_project_settings_project_id'),
        sa.CheckConstraint('reality_level >= 0 AND reality_level <= 10', name='chk_reality_level_bounds'),
        sa.CheckConstraint('continuity_strictness >= 0 AND continuity_strictness <= 10', name='chk_continuity_strictness_bounds')
    )
    op.create_index('ix_project_settings_project_id', 'project_settings', ['project_id'])

    op.create_table(
        'story_world_rules',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('rule_text', sa.Text(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_story_world_rules_project_id', 'story_world_rules', ['project_id'])

def downgrade() -> None:
    op.drop_index('ix_story_world_rules_project_id', table_name='story_world_rules')
    op.drop_table('story_world_rules')
    op.drop_index('ix_project_settings_project_id', table_name='project_settings')
    op.drop_table('project_settings')
