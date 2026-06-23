"""add crawl_progress table

Revision ID: b3f5d1a9c2e7
Revises: 74cff54d8f61
Create Date: 2026-06-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3f5d1a9c2e7'
down_revision: Union[str, None] = '74cff54d8f61'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('crawl_progress',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('crawl_task_id', sa.String(), nullable=False),
    sa.Column('url', sa.String(), nullable=False),
    sa.Column('scan_target', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('pages_discovered', sa.JSON(), nullable=True),
    sa.Column('pages_depth_map', sa.JSON(), nullable=True),
    sa.Column('url_to_menu_text', sa.JSON(), nullable=True),
    sa.Column('sitemaps_found', sa.JSON(), nullable=True),
    sa.Column('unauth_pages_discovered', sa.JSON(), nullable=True),
    sa.Column('auth_pages_discovered', sa.JSON(), nullable=True),
    sa.Column('storage_state', sa.JSON(), nullable=True),
    sa.Column('auth_headers', sa.JSON(), nullable=True),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('organization_id', sa.UUID(), nullable=False),
    sa.Column('project_id', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_crawl_progress_crawl_task_id'), 'crawl_progress', ['crawl_task_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_crawl_progress_crawl_task_id'), table_name='crawl_progress')
    op.drop_table('crawl_progress')
