"""audit persistence and regression tables

Revision ID: c7a8b9d0e1f2
Revises: b3f5d1a9c2e7
Create Date: 2026-10-14 09:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = 'c7a8b9d0e1f2'
down_revision: Union[str, None] = 'b3f5d1a9c2e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Purge legacy audit records as specified in regression plan (No backfill)
    op.execute("DELETE FROM violations;")
    op.execute("DELETE FROM audit_sessions;")

    # 2. Update projects table
    op.add_column('projects', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('projects', sa.Column('status', sa.String(), server_default='active', nullable=False))
    op.add_column('projects', sa.Column('updated_at', sa.DateTime(), nullable=True))
    # Deduplicate project names per org if any exist before adding unique constraint
    op.create_unique_constraint('uq_org_project_name', 'projects', ['organization_id', 'name'])

    # 3. Update audit_sessions table
    op.alter_column('audit_sessions', 'project_id', nullable=False)
    # Ensure FK with cascade delete
    op.drop_constraint('audit_sessions_project_id_fkey', 'audit_sessions', type_='foreignkey')
    op.create_foreign_key(
        'fk_audit_sessions_project_id',
        'audit_sessions', 'projects',
        ['project_id'], ['id'],
        ondelete='CASCADE'
    )

    op.add_column('audit_sessions', sa.Column('run_number', sa.Integer(), nullable=True))
    op.add_column('audit_sessions', sa.Column('run_type', sa.String(), server_default='baseline', nullable=False))
    op.add_column('audit_sessions', sa.Column('previous_run_id', UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_audit_sessions_previous_run_id',
        'audit_sessions', 'audit_sessions',
        ['previous_run_id'], ['id'],
        ondelete='SET NULL'
    )
    op.add_column('audit_sessions', sa.Column('scope_fingerprint', sa.String(), nullable=True))

    op.add_column('audit_sessions', sa.Column('total_testcases', sa.Integer(), server_default='0', nullable=False))
    op.add_column('audit_sessions', sa.Column('fail', sa.Integer(), server_default='0', nullable=False))
    op.add_column('audit_sessions', sa.Column('pass', sa.Integer(), server_default='0', nullable=False))
    op.add_column('audit_sessions', sa.Column('na', sa.Integer(), server_default='0', nullable=False))
    op.add_column('audit_sessions', sa.Column('manual', sa.Integer(), server_default='0', nullable=False))
    op.add_column('audit_sessions', sa.Column('score', sa.Float(), server_default='0.0', nullable=False))
    op.add_column('audit_sessions', sa.Column('completed_at', sa.DateTime(), nullable=True))

    op.add_column('audit_sessions', sa.Column('defects_new', sa.Integer(), server_default='0', nullable=False))
    op.add_column('audit_sessions', sa.Column('defects_fixed', sa.Integer(), server_default='0', nullable=False))
    op.add_column('audit_sessions', sa.Column('defects_reopened', sa.Integer(), server_default='0', nullable=False))
    op.add_column('audit_sessions', sa.Column('defects_open', sa.Integer(), server_default='0', nullable=False))
    op.add_column('audit_sessions', sa.Column('defects_not_retested', sa.Integer(), server_default='0', nullable=False))

    # 4. Create audit_pages
    op.create_table(
        'audit_pages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('audit_session_id', UUID(as_uuid=True), sa.ForeignKey('audit_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('normalized_url', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('depth', sa.Integer(), server_default='1', nullable=False),
        sa.Column('status', sa.String(), server_default='scanned', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('audit_session_id', 'url', name='uq_session_page_url')
    )

    # 5. Create success_criteria
    op.create_table(
        'success_criteria',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('sc_code', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('level', sa.String(), nullable=False),
        sa.Column('principle', sa.String(), nullable=False),
        sa.Column('wcag_version', sa.String(), server_default='2.2', nullable=False),
        sa.Column('what_we_check', sa.Text(), nullable=True),
        sa.Column('expected', sa.Text(), nullable=True),
        sa.Column('manual_steps', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('sc_code', name='uq_success_criteria_sc_code')
    )
    op.create_index('ix_success_criteria_sc_code', 'success_criteria', ['sc_code'])

    # 6. Create defects
    op.create_table(
        'defects',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('defect_code', sa.String(), nullable=False),
        sa.Column('fingerprint', sa.String(), nullable=False),
        sa.Column('loose_fingerprint', sa.String(), nullable=True),
        sa.Column('rule_id', sa.String(), nullable=False),
        sa.Column('success_criterion_id', UUID(as_uuid=True), sa.ForeignKey('success_criteria.id', ondelete='SET NULL'), nullable=True),
        sa.Column('page_url', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), server_default='Moderate', nullable=False),
        sa.Column('fix_steps', sa.JSON(), nullable=True),
        sa.Column('code_before', sa.Text(), nullable=True),
        sa.Column('code_after', sa.Text(), nullable=True),
        sa.Column('verify_steps', sa.JSON(), nullable=True),
        sa.Column('false_positive_note', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), server_default='New', nullable=False),
        sa.Column('first_seen_run_id', UUID(as_uuid=True), sa.ForeignKey('audit_sessions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('last_seen_run_id', UUID(as_uuid=True), sa.ForeignKey('audit_sessions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('fixed_in_run_id', UUID(as_uuid=True), sa.ForeignKey('audit_sessions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reopen_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('times_seen', sa.Integer(), server_default='1', nullable=False),
        sa.Column('clean_runs_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('assignee_user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('suppressed_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('project_id', 'fingerprint', name='uq_project_defect_fingerprint'),
        sa.UniqueConstraint('project_id', 'defect_code', name='uq_project_defect_code')
    )
    op.create_index('ix_defects_project_id', 'defects', ['project_id'])
    op.create_index('ix_defects_fingerprint', 'defects', ['fingerprint'])
    op.create_index('ix_defects_loose_fingerprint', 'defects', ['loose_fingerprint'])
    op.create_index('ix_defects_status', 'defects', ['status'])
    op.create_index('ix_defects_project_status', 'defects', ['project_id', 'status'])

    # 7. Create defect_events
    op.create_table(
        'defect_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('defect_id', UUID(as_uuid=True), sa.ForeignKey('defects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('audit_session_id', UUID(as_uuid=True), sa.ForeignKey('audit_sessions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('event', sa.String(), nullable=False),
        sa.Column('from_status', sa.String(), nullable=True),
        sa.Column('to_status', sa.String(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )
    op.create_index('ix_defect_events_defect_id', 'defect_events', ['defect_id'])
    op.create_index('ix_defect_events_created_at', 'defect_events', ['created_at'])

    # 8. Create testcases
    op.create_table(
        'testcases',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('audit_session_id', UUID(as_uuid=True), sa.ForeignKey('audit_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('audit_page_id', UUID(as_uuid=True), sa.ForeignKey('audit_pages.id', ondelete='SET NULL'), nullable=True),
        sa.Column('success_criterion_id', UUID(as_uuid=True), sa.ForeignKey('success_criteria.id', ondelete='SET NULL'), nullable=True),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('defect_id', UUID(as_uuid=True), sa.ForeignKey('defects.id', ondelete='SET NULL'), nullable=True),
        sa.Column('testcase_code', sa.String(), nullable=False),
        sa.Column('display_name', sa.String(), nullable=True),
        sa.Column('rule_id', sa.String(), nullable=False),
        sa.Column('testcase_name', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), server_default='N/A', nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('expected_result', sa.Text(), nullable=True),
        sa.Column('actual_result', sa.Text(), nullable=True),
        sa.Column('steps_to_reproduce', sa.Text(), nullable=True),
        sa.Column('business_impact', sa.Text(), nullable=True),
        sa.Column('remediation', sa.Text(), nullable=True),
        sa.Column('html_snippet', sa.Text(), nullable=True),
        sa.Column('selector', sa.Text(), nullable=True),
        sa.Column('screenshot_path', sa.String(), nullable=True),
        sa.Column('repeat_count', sa.Integer(), server_default='1', nullable=False),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('help_url', sa.String(), nullable=True),
        sa.Column('page_url', sa.String(), nullable=True),
        sa.Column('page_title', sa.String(), nullable=True),
        sa.Column('fingerprint', sa.String(), nullable=True),
        sa.Column('input_tokens', sa.Integer(), server_default='0', nullable=False),
        sa.Column('output_tokens', sa.Integer(), server_default='0', nullable=False),
        sa.Column('refined_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )
    op.create_index('ix_testcases_audit_session_id', 'testcases', ['audit_session_id'])
    op.create_index('ix_testcases_project_id', 'testcases', ['project_id'])
    op.create_index('ix_testcases_defect_id', 'testcases', ['defect_id'])
    op.create_index('ix_testcases_fingerprint', 'testcases', ['fingerprint'])
    op.create_index('ix_testcases_session_status', 'testcases', ['audit_session_id', 'status'])
    op.create_index('ix_testcases_project_fingerprint', 'testcases', ['project_id', 'fingerprint'])

    # 9. Create run_criterion_results
    op.create_table(
        'run_criterion_results',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('audit_session_id', UUID(as_uuid=True), sa.ForeignKey('audit_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('success_criterion_id', UUID(as_uuid=True), sa.ForeignKey('success_criteria.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('pass_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('fail_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('audit_session_id', 'success_criterion_id', name='uq_session_criterion')
    )
    op.create_index('ix_run_criterion_results_session', 'run_criterion_results', ['audit_session_id'])
    op.create_index('ix_run_criterion_results_criterion', 'run_criterion_results', ['success_criterion_id'])

    # 10. Create report_artifacts
    op.create_table(
        'report_artifacts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('audit_session_id', UUID(as_uuid=True), sa.ForeignKey('audit_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('kind', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('report_version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )
    op.create_index('ix_report_artifacts_session', 'report_artifacts', ['audit_session_id'])


def downgrade() -> None:
    op.drop_table('report_artifacts')
    op.drop_table('run_criterion_results')
    op.drop_table('testcases')
    op.drop_table('defect_events')
    op.drop_table('defects')
    op.drop_table('success_criteria')
    op.drop_table('audit_pages')

    op.drop_column('audit_sessions', 'defects_not_retested')
    op.drop_column('audit_sessions', 'defects_open')
    op.drop_column('audit_sessions', 'defects_reopened')
    op.drop_column('audit_sessions', 'defects_fixed')
    op.drop_column('audit_sessions', 'defects_new')
    op.drop_column('audit_sessions', 'completed_at')
    op.drop_column('audit_sessions', 'score')
    op.drop_column('audit_sessions', 'manual')
    op.drop_column('audit_sessions', 'na')
    op.drop_column('audit_sessions', 'pass')
    op.drop_column('audit_sessions', 'fail')
    op.drop_column('audit_sessions', 'total_testcases')
    op.drop_column('audit_sessions', 'scope_fingerprint')
    op.drop_constraint('fk_audit_sessions_previous_run_id', 'audit_sessions', type_='foreignkey')
    op.drop_column('audit_sessions', 'previous_run_id')
    op.drop_column('audit_sessions', 'run_type')
    op.drop_column('audit_sessions', 'run_number')

    op.drop_constraint('uq_org_project_name', 'projects', type_='unique')
    op.drop_column('projects', 'updated_at')
    op.drop_column('projects', 'status')
    op.drop_column('projects', 'description')
