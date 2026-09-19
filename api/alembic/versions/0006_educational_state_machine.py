"""Add formal educational state-machine constraints.

Revision ID: 0006_educational_state_machine
Revises: 0005_context_engine
Create Date: 2026-09-18
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_educational_state_machine"
down_revision: str | None = "0005_context_engine"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

KNOWLEDGE_STATE_CHECK = (
    "knowledge_state IN ('NOT_INTRODUCED', 'INTRODUCED', 'BASIC_UNDERSTANDING', "
    "'STRONG_UNDERSTANDING', 'SUCCESSFULLY_APPLIED', 'NEEDS_CLARIFICATION', 'MISUNDERSTOOD')"
)
APPLICATION_STATE_CHECK = (
    "application_state IS NULL OR application_state IN "
    "('NOT_OBSERVED', 'ATTEMPTED', 'SUCCESSFULLY_APPLIED')"
)


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE educational_context
            SET knowledge_state = CASE lower(trim(knowledge_state))
                WHEN 'not_introduced' THEN 'NOT_INTRODUCED'
                WHEN 'not introduced' THEN 'NOT_INTRODUCED'
                WHEN 'introduced' THEN 'INTRODUCED'
                WHEN 'basic_understanding' THEN 'BASIC_UNDERSTANDING'
                WHEN 'basic understanding' THEN 'BASIC_UNDERSTANDING'
                WHEN 'strong_understanding' THEN 'STRONG_UNDERSTANDING'
                WHEN 'strong understanding' THEN 'STRONG_UNDERSTANDING'
                WHEN 'successfully_applied' THEN 'SUCCESSFULLY_APPLIED'
                WHEN 'successfully applied' THEN 'SUCCESSFULLY_APPLIED'
                WHEN 'needs_clarification' THEN 'NEEDS_CLARIFICATION'
                WHEN 'needs clarification' THEN 'NEEDS_CLARIFICATION'
                WHEN 'misunderstood' THEN 'MISUNDERSTOOD'
                ELSE 'INTRODUCED'
            END,
            application_state = CASE lower(trim(coalesce(application_state, '')))
                WHEN 'not_observed' THEN 'NOT_OBSERVED'
                WHEN 'not observed' THEN 'NOT_OBSERVED'
                WHEN 'attempted' THEN 'ATTEMPTED'
                WHEN 'needs practice' THEN 'ATTEMPTED'
                WHEN 'successfully_applied' THEN 'SUCCESSFULLY_APPLIED'
                WHEN 'successfully applied' THEN 'SUCCESSFULLY_APPLIED'
                WHEN 'consistent' THEN 'SUCCESSFULLY_APPLIED'
                ELSE 'NOT_OBSERVED'
            END
            """
        )
    )
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("educational_context", recreate="always") as batch_op:
            batch_op.create_check_constraint(
                "ck_educational_context_knowledge_state",
                KNOWLEDGE_STATE_CHECK,
            )
            batch_op.create_check_constraint(
                "ck_educational_context_application_state",
                APPLICATION_STATE_CHECK,
            )
    else:
        op.create_check_constraint(
            "ck_educational_context_knowledge_state",
            "educational_context",
            KNOWLEDGE_STATE_CHECK,
        )
        op.create_check_constraint(
            "ck_educational_context_application_state",
            "educational_context",
            APPLICATION_STATE_CHECK,
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("educational_context", recreate="always") as batch_op:
            batch_op.drop_constraint("ck_educational_context_application_state", type_="check")
            batch_op.drop_constraint("ck_educational_context_knowledge_state", type_="check")
    else:
        op.drop_constraint(
            "ck_educational_context_application_state",
            "educational_context",
            type_="check",
        )
        op.drop_constraint(
            "ck_educational_context_knowledge_state",
            "educational_context",
            type_="check",
        )
