"""Security and crash boundaries of the orchestrator shape."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lab8.app import prepare_store
from lab8.db import connect
from lab8.durability import InjectedCrash
from lab8.handoff import ALLOWED_FIELDS, FACT_KEYS, READONLY_TOOLS, WRITE_TOOLS
from lab8.schemas import make_run_id
from lab8.shapes.orchestrator import run_claim


def test_orchestrator_handoff_and_trace_exclude_parent_data(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    store = tmp_path / "handoff.sqlite"
    prepare_store(store)
    conn = connect(store)
    try:
        claim = conn.execute(
            "SELECT ticket, parent_secret, raw_headers_json FROM claims WHERE claim_id = ?",
            ("C-010",),
        ).fetchone()
        order = conn.execute(
            "SELECT phone, address, internal_note, item_name FROM orders WHERE order_id = ?",
            ("O-107",),
        ).fetchone()
        forbidden = [*claim, *order]
    finally:
        conn.close()

    result = run_claim("C-010", seed=55, store_path=str(store))
    assert result.status == "resolved"
    trace_text = Path(result.trace_path).read_text(encoding="utf-8")
    trace = json.loads(trace_text)
    handoffs = [event["payload"] for event in trace["events"] if event["kind"] == "handoff"]
    assert len(handoffs) == 1
    handoff = handoffs[0]
    assert set(handoff) <= ALLOWED_FIELDS
    assert set(handoff["facts"]) <= FACT_KEYS
    assert set(handoff["allowed_tools"]) <= READONLY_TOOLS
    assert not set(handoff["allowed_tools"]) & WRITE_TOOLS
    assert not any(value and value in trace_text for value in forbidden)


def test_orchestrator_crash_leaves_safe_trace_and_resumes_once(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    store = tmp_path / "crash.sqlite"
    prepare_store(store)
    with pytest.raises(InjectedCrash):
        run_claim(
            "C-012",
            seed=11,
            store_path=str(store),
            crash_at="after_effect_before_checkpoint",
        )

    run_id = make_run_id("orchestrator", "C-012", 11)
    crash_trace = tmp_path / "traces" / f"{run_id}.json"
    trace_text = crash_trace.read_text(encoding="utf-8")
    trace = json.loads(trace_text)
    assert trace["run_id"] == run_id
    assert isinstance(trace["events"], list) and trace["events"]
    assert "CANARY_SECRET_" not in trace_text

    resumed = run_claim("C-012", seed=11, store_path=str(store))
    assert resumed.status == "resolved"
    conn = connect(store)
    try:
        refund_count = conn.execute(
            "SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = ?", ("C-012",)
        ).fetchone()["n"]
        audit_count = conn.execute(
            "SELECT COUNT(*) AS n FROM audit_events "
            "WHERE claim_id = ? AND event_type = 'refund_committed'",
            ("C-012",),
        ).fetchone()["n"]
    finally:
        conn.close()
    assert refund_count == audit_count == 1
