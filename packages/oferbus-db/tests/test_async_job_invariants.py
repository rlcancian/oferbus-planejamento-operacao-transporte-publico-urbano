from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Index

from oferbus_db import Base


def test_computation_job_has_tenant_aware_run_foreign_key() -> None:
    table = Base.metadata.tables["oferbus.computation_job"]
    constraint = next(
        c for c in table.constraints
        if isinstance(c, ForeignKeyConstraint) and c.name == "fk_computation_job_tenant_run"
    )
    assert {column.name for column in constraint.columns} == {"organization_id", "run_id"}


def test_computation_job_has_progress_and_retry_checks() -> None:
    table = Base.metadata.tables["oferbus.computation_job"]
    names = {c.name for c in table.constraints if isinstance(c, CheckConstraint)}
    assert "ck_computation_job_progress" in names
    assert "ck_computation_job_attempt_count" in names
    assert "ck_computation_job_max_attempts" in names


def test_computation_job_has_claim_and_idempotency_indexes() -> None:
    table = Base.metadata.tables["oferbus.computation_job"]
    indexes = {index.name: index for index in table.indexes if isinstance(index, Index)}
    assert "ix_computation_job_claim" in indexes
    assert indexes["uq_computation_job_org_idempotency"].unique is True
