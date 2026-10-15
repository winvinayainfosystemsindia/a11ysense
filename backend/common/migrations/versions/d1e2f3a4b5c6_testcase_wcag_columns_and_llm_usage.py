"""testcase wcag columns and llm usage ledger

Revision ID: d1e2f3a4b5c6
Revises: c7a8b9d0e1f2
Create Date: 2026-10-15 11:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'c7a8b9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)

    existing_cols = {c['name'] for c in insp.get_columns('testcases')}
    if 'wcag_criteria' not in existing_cols:
        op.add_column('testcases', sa.Column('wcag_criteria', sa.String(), nullable=True))
    if 'wcag_level' not in existing_cols:
        op.add_column('testcases', sa.Column('wcag_level', sa.String(), nullable=True))
    if 'wcag_principle' not in existing_cols:
        op.add_column('testcases', sa.Column('wcag_principle', sa.String(), nullable=True))

    existing_tables = insp.get_table_names()
    if 'llm_usage' not in existing_tables:
        op.create_table(
            'llm_usage',
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('task_id', sa.String(), nullable=False),
            sa.Column('provider', sa.String(), nullable=False),
            sa.Column('model', sa.String(), nullable=False),
            sa.Column('input_tokens', sa.Integer(), server_default='0', nullable=False),
            sa.Column('output_tokens', sa.Integer(), server_default='0', nullable=False),
            sa.Column('cached', sa.Boolean(), server_default=sa.false(), nullable=False),
            sa.Column('cost_usd', sa.Float(), server_default='0', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
        )
        op.create_index('ix_llm_usage_task_id', 'llm_usage', ['task_id'])


def downgrade() -> None:
    op.drop_index('ix_llm_usage_task_id', table_name='llm_usage')
    op.drop_table('llm_usage')
    op.drop_column('testcases', 'wcag_principle')
    op.drop_column('testcases', 'wcag_level')
    op.drop_column('testcases', 'wcag_criteria')
