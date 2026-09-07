"""Issue Reviews and Decision Fingerprints Schema

Revision ID: 004_day4_issue_reviews
Revises: 003_day3_continuity_issues
Create Date: 2026-09-02 00:08:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '004_day4_issue_reviews'
down_revision: Union[str, None] = '003_day3_continuity_issues'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Extend issues table
    op.add_column('issues', sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('issues', sa.Column('reviewed_by', sa.String(length=50), nullable=True, server_default='writer'))
    op.add_column('issues', sa.Column('resolution_type', sa.String(length=50), nullable=True))
    op.add_column('issues', sa.Column('resolution_note', sa.Text(), nullable=True))
    op.add_column('issues', sa.Column('issue_fingerprint', sa.String(length=64), nullable=True))

    op.create_index('idx_issue_fingerprint', 'issues', ['project_id', 'issue_fingerprint'])

    # 2. Create issue_reviews table
    op.create_table(
        'issue_reviews',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('issue_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),  # ACCEPT | IGNORE | RESOLVE | REOPEN
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('previous_status', sa.String(length=20), nullable=False),
        sa.Column('new_status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['issue_id'], ['issues.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ir_issue_id', 'issue_reviews', ['issue_id'])
    op.create_index('idx_ir_project_id', 'issue_reviews', ['project_id'])


def downgrade() -> None:
    op.drop_index('idx_ir_project_id', table_name='issue_reviews')
    op.drop_index('idx_ir_issue_id', table_name='issue_reviews')
    op.drop_table('issue_reviews')

    op.drop_index('idx_issue_fingerprint', table_name='issues')
    op.drop_column('issues', 'issue_fingerprint')
    op.drop_column('issues', 'resolution_note')
    op.drop_column('issues', 'resolution_type')
    op.drop_column('issues', 'reviewed_by')
    op.drop_column('issues', 'reviewed_at')
