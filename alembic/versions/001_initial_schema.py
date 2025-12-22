"""initial schema

Revision ID: 001_initial
Revises:
Create Date: 2025-12-21 10:32:01

"""
from alembic import op
import sqlalchemy as sa


revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'videos',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('creator_id', sa.String(32), nullable=False),
        sa.Column('video_created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('views_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('likes_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('comments_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('reports_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_videos_creator_id', 'videos', ['creator_id'])
    op.create_index('ix_videos_video_created_at', 'videos', ['video_created_at'])
    op.create_index('ix_videos_created_at', 'videos', ['created_at'])

    op.create_table(
        'video_snapshots',
        sa.Column('id', sa.String(32), nullable=False),
        sa.Column('video_id', sa.String(36), nullable=False),
        sa.Column('views_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('likes_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('comments_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('reports_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('delta_views_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('delta_likes_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('delta_comments_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('delta_reports_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ondelete='CASCADE')
    )

    op.create_index('ix_video_snapshots_video_id', 'video_snapshots', ['video_id'])
    op.create_index('ix_video_snapshots_created_at', 'video_snapshots', ['created_at'])
    op.create_index('idx_video_snapshots_video_created', 'video_snapshots', ['video_id', 'created_at'])


def downgrade() -> None:
    op.drop_index('idx_video_snapshots_video_created', table_name='video_snapshots')
    op.drop_index('ix_video_snapshots_created_at', table_name='video_snapshots')
    op.drop_index('ix_video_snapshots_video_id', table_name='video_snapshots')
    op.drop_table('video_snapshots')

    op.drop_index('ix_videos_created_at', table_name='videos')
    op.drop_index('ix_videos_video_created_at', table_name='videos')
    op.drop_index('ix_videos_creator_id', table_name='videos')
    op.drop_table('videos')
