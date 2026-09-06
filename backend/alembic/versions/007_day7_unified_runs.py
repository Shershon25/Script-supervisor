"""Day 7 Scene Analysis Runs table

Revision ID: 007_day7_unified_runs
Revises: 006_day6_retrieval_reasoning
Create Date: 2026-09-04 01:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '007_day7_unified_runs'
down_revision = '006_day6_retrieval_reasoning'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'scene_analysis_runs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('scene_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='COMPLETED'),
        sa.Column('entities_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('facts_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('events_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('issues_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('claims_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('research_reused_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scene_id'], ['scenes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scene_analysis_runs_project_id', 'scene_analysis_runs', ['project_id'])
    op.create_index('ix_scene_analysis_runs_scene_id', 'scene_analysis_runs', ['scene_id'])

def downgrade() -> None:
    op.drop_index('ix_scene_analysis_runs_scene_id', table_name='scene_analysis_runs')
    op.drop_index('ix_scene_analysis_runs_project_id', table_name='scene_analysis_runs')
    op.drop_table('scene_analysis_runs')
