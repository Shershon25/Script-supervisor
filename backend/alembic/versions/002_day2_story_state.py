"""Story State Schema: Relationships and Knowledge States

Revision ID: 002_day2_story_state
Revises: 001_initial_day1_schema
Create Date: 2026-09-01 23:34:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_day2_story_state'
down_revision: Union[str, None] = '001_initial_day1_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Relationships Table
    op.create_table(
        'relationships',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('source_entity_id', sa.String(length=36), nullable=False),
        sa.Column('relationship_type', sa.String(length=100), nullable=False),
        sa.Column('target_entity_id', sa.String(length=36), nullable=True),
        sa.Column('scene_id', sa.String(length=36), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('source_type', sa.String(length=50), nullable=False, server_default='SCREENPLAY'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_entity_id'], ['entities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_entity_id'], ['entities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scene_id'], ['scenes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_rel_project_id', 'relationships', ['project_id'])
    op.create_index('idx_rel_source_entity', 'relationships', ['source_entity_id'])
    op.create_index('idx_rel_target_entity', 'relationships', ['target_entity_id'])

    # Knowledge States Table
    op.create_table(
        'knowledge_states',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('character_entity_id', sa.String(length=36), nullable=False),
        sa.Column('knowledge', sa.Text(), nullable=False),
        sa.Column('source_scene_id', sa.String(length=36), nullable=False),
        sa.Column('knowledge_type', sa.String(length=50), nullable=False, server_default='explicitly_established'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['character_entity_id'], ['entities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_scene_id'], ['scenes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ks_project_id', 'knowledge_states', ['project_id'])
    op.create_index('idx_ks_character_entity', 'knowledge_states', ['character_entity_id'])


def downgrade() -> None:
    op.drop_index('idx_ks_character_entity', table_name='knowledge_states')
    op.drop_index('idx_ks_project_id', table_name='knowledge_states')
    op.drop_table('knowledge_states')

    op.drop_index('idx_rel_target_entity', table_name='relationships')
    op.drop_index('idx_rel_source_entity', table_name='relationships')
    op.drop_index('idx_rel_project_id', table_name='relationships')
    op.drop_table('relationships')
