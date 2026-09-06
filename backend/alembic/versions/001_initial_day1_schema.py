"""Initial Day 1 Schema

Revision ID: 001_initial_day1_schema
Revises: 
Create Date: 2026-08-31 20:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_day1_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Projects Table
    op.create_table(
        'projects',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Scenes Table
    op.create_table(
        'scenes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('scene_number', sa.Integer(), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'scene_number', name='uq_project_scene_number')
    )

    # Entities Table
    op.create_table(
        'entities',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('attributes_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_entity_project_type_name', 'entities', ['project_id', 'type', 'name'])

    # Facts Table
    op.create_table(
        'facts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('subject_entity_id', sa.String(length=36), nullable=False),
        sa.Column('predicate', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('scene_id', sa.String(length=36), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subject_entity_id'], ['entities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scene_id'], ['scenes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Events Table
    op.create_table(
        'events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('scene_id', sa.String(length=36), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('actor_entity_id', sa.String(length=36), nullable=True),
        sa.Column('target_entity_id', sa.String(length=36), nullable=True),
        sa.Column('location_entity_id', sa.String(length=36), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('attributes_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['scene_id'], ['scenes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['actor_entity_id'], ['entities.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['target_entity_id'], ['entities.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['location_entity_id'], ['entities.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('events')
    op.drop_table('facts')
    op.drop_index('idx_entity_project_type_name', table_name='entities')
    op.drop_table('entities')
    op.drop_table('scenes')
    op.drop_table('projects')
