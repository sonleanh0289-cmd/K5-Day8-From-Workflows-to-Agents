"""Focused regression tests for the single-agent shape."""

import json
from pathlib import Path

from lab8.shapes.single import run_claim


def test_single_resolves_claim_and_writes_matching_trace(public_db):
    result = run_claim("C-001", seed=987654, store_path=str(public_db))

    assert result.status == "resolved"
    assert result.proposal_amount == 35_000
    assert len(result.refund_effects) == 1
    assert result.refund_effects[0]["amount_vnd"] == 35_000
    assert result.committed_audit_count == 1

    trace_path = Path(result.trace_path)
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    assert trace["run_id"] == result.run_id
    assert isinstance(trace["events"], list)
