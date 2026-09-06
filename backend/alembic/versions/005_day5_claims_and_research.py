"""Day 5 Schema: External Claims, Research Tasks, Results & Evaluations

Revision ID: 005_day5_claims_and_research
Revises: 004_day4_issue_reviews
Create Date: 2026-09-04 00:13:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '005_day5_claims_and_research'
down_revision: Union[str, None] = '004_day4_issue_reviews'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create claims table
    op.create_table(
        'claims',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('scene_id', sa.String(length=36), nullable=False),
        sa.Column('claim_text', sa.Text(), nullable=False),
        sa.Column('claim_type', sa.String(length=50), nullable=False, server_default='REAL_WORLD_CLAIM'),
        sa.Column('subject', sa.String(length=255), nullable=True),
        sa.Column('predicate', sa.String(length=100), nullable=True),
        sa.Column('object', sa.String(length=255), nullable=True),
        sa.Column('temporal_context', sa.String(length=100), nullable=True),
        sa.Column('location_context', sa.String(length=100), nullable=True),
        sa.Column('requires_research', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('research_priority', sa.String(length=20), nullable=False, server_default='MEDIUM'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='UNVERIFIED'),
        sa.Column('claim_fingerprint', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scene_id'], ['scenes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_claim_project_status', 'claims', ['project_id', 'status'])
    op.create_index('idx_claim_fingerprint', 'claims', ['project_id', 'claim_fingerprint'])

    # 2. Create research_tasks table
    op.create_table(
        'research_tasks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('scene_id', sa.String(length=36), nullable=False),
        sa.Column('claim_id', sa.String(length=36), nullable=False),
        sa.Column('objective', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('provider', sa.String(length=50), nullable=False, server_default='parallel'),
        sa.Column('requested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scene_id'], ['scenes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_rt_project_claim', 'research_tasks', ['project_id', 'claim_id'])

    # 3. Create research_results table
    op.create_table(
        'research_results',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('research_task_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('excerpt', sa.Text(), nullable=False),
        sa.Column('relevance_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('retrieved_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('raw_metadata_json', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['research_task_id'], ['research_tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_rr_task_id', 'research_results', ['research_task_id'])

    # 4. Create research_evaluations table
    op.create_table(
        'research_evaluations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('research_task_id', sa.String(length=36), nullable=False),
        sa.Column('claim_id', sa.String(length=36), nullable=False),
        sa.Column('verdict', sa.String(length=50), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.90'),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('reasoning', sa.Text(), nullable=False),
        sa.Column('supporting_source_ids_json', sa.JSON(), nullable=False),
        sa.Column('contradicting_source_ids_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['research_task_id'], ['research_tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_re_task_claim', 'research_evaluations', ['research_task_id', 'claim_id'])


def downgrade() -> None:
    op.drop_table('research_evaluations')
    op.drop_table('research_results')
    op.drop_table('research_tasks')
    op.drop_table('claims')
