"""Continuity Issues Table Schema

Revision ID: 003_day3_continuity_issues
Revises: 002_day2_story_state
Create Date: 2026-09-01 23:57:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003_day3_continuity_issues'
down_revision: Union[str, None] = '002_day2_story_state'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'issues',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('scene_id', sa.String(length=36), nullable=False),
        sa.Column('issue_type', sa.String(length=100), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='WARNING'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='OPEN'),
        sa.Column('evidence_json', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scene_id'], ['scenes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_issue_project_id', 'issues', ['project_id'])
    op.create_index('idx_issue_scene_id', 'issues', ['scene_id'])
    op.create_index('idx_issue_status', 'issues', ['status'])


def downgrade() -> None:
    op.drop_index('idx_issue_status', table_name='issues')
    op.drop_index('idx_issue_scene_id', table_name='issues')
    op.drop_index('idx_issue_project_id', table_name='issues')
    op.drop_table('issues')
