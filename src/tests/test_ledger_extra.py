"""Extra tests for ledger, approval, per-order cap, and crash safety — Thành viên 4 (Ledger/Crash + Evaluation).

Kiểm tra trực tiếp các bất biến của tầng host (`lab8.durability`, `lab8.tools`)
và đối chiếu trên các shape đã cài đặt (`workflow`, `single`, `orchestrator`):
- Gọi lại cùng claim giữ đúng 1 dòng ledger và 1 audit `refund_committed`.
- Gọi lại với số tiền khác gây `amount_conflict` và không sửa dòng ledger cũ.
- Thiếu approval hoặc approval của claim khác (`approval_claim_mismatch`) bị chặn và ghi `policy_denied`.
- Trần theo đơn (T13, T14): host tự trừ phần đã hoàn khi shape truyền quote đầy đủ.
- Crash tại 3 điểm (`before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`) rồi resume vẫn chỉ 1 refund.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from lab8.app import prepare_store
from lab8.db import connect
from lab8.durability import (
    InjectedCrash,
    committed_audit_count,
    get_refund,
    issue_refund,
)
from lab8.shapes.orchestrator import run_claim as run_orchestrator
from lab8.shapes.single import run_claim as run_single
from lab8.shapes.workflow import run_claim as run_workflow


def _fresh_store(tmp_path: Path, name: str = "tv4.sqlite", extra_claims=None) -> str:
    path = tmp_path / name
    prepare_store(path, extra_claims=extra_claims)
    return str(path)


def test_ledger_idempotent_replay_keeps_single_row(tmp_path: Path) -> None:
    store = _fresh_store(tmp_path)
    conn = connect(store)
    try:
        first = issue_refund(conn, "C-001", 35000)
        second = issue_refund(conn, "C-001", 35000)
        assert first["ok"] is True
        assert second["ok"] is True
        assert second["reason"] == "idempotent_replay"
        effect = get_refund(conn, "C-001")
        assert effect is not None
        assert int(effect["amount_vnd"]) == 35000
        assert committed_audit_count(conn, "C-001") == 1
    finally:
        conn.close()


def test_ledger_amount_conflict_preserves_original_amount(tmp_path: Path) -> None:
    store = _fresh_store(tmp_path)
    conn = connect(store)
    try:
        first = issue_refund(conn, "C-001", 35000)
        conflict = issue_refund(conn, "C-001", 20000)
        assert first["ok"] is True
        assert conflict["ok"] is False
        assert conflict["conflict"] is True
        assert conflict["reason"] == "amount_conflict"
        effect = get_refund(conn, "C-001")
        assert effect is not None
        assert int(effect["amount_vnd"]) == 35000
        assert committed_audit_count(conn, "C-001") == 1
    finally:
        conn.close()


def test_approval_from_other_claim_is_denied_with_audit(tmp_path: Path) -> None:
    borrowed_claim = {
        "claim_id": "C-TV4-BORROW",
        "principal_id": "P-100",
        "order_id": "O-107",
        "ticket": "Xin hoàn phí ship bằng approval của claim khác.",
        "parent_secret": "CANARY_SECRET_TV4_BORROW",
        "raw_headers": {"Authorization": "Bearer CANARY_SECRET_TV4_BORROW"},
        "approval_id": "A-001",  # A-001 thuộc về C-001, không phải C-TV4-BORROW
    }
    store = _fresh_store(tmp_path, extra_claims=[borrowed_claim])
    conn = connect(store)
    try:
        outcome = issue_refund(conn, "C-TV4-BORROW", 35000)
        assert outcome["ok"] is False
        assert get_refund(conn, "C-TV4-BORROW") is None
        assert committed_audit_count(conn, "C-TV4-BORROW") == 0
        audit = conn.execute(
            "SELECT event_type FROM audit_events WHERE claim_id = ? AND event_type = 'policy_denied'",
            ("C-TV4-BORROW",),
        ).fetchone()
        assert audit is not None
    finally:
        conn.close()


@pytest.mark.parametrize("crash_point", ["before_effect", "after_effect_before_checkpoint", "after_checkpoint"])
def test_crash_and_resume_always_leaves_one_refund(tmp_path: Path, crash_point: str) -> None:
    store = _fresh_store(tmp_path, name=f"crash-{crash_point}.sqlite")
    conn = connect(store)
    try:
        with pytest.raises(InjectedCrash):
            issue_refund(conn, "C-001", 35000, crash_at=crash_point)
        resumed = issue_refund(conn, "C-001", 35000, crash_at=None)
        assert resumed["ok"] is True
        effect = get_refund(conn, "C-001")
        assert effect is not None
        assert int(effect["amount_vnd"]) == 35000
        assert committed_audit_count(conn, "C-001") == 1
    finally:
        conn.close()


@pytest.mark.parametrize("runner", [run_workflow, run_single, run_orchestrator])
def test_all_student_shapes_respect_per_order_cap(tmp_path: Path, runner) -> None:
    # T13 (C-013): đơn đã hoàn đủ -> denied; T14 (C-014): chỉ hoàn phần chênh (120000) dù quote đầy đủ 150000.
    store_t13 = _fresh_store(tmp_path, name=f"t13-{runner.__module__}.sqlite")
    res_t13 = runner("C-013", seed=11, store_path=store_t13)
    assert res_t13.status == "denied"
    assert res_t13.proposal_amount == 35000
    assert res_t13.refund_effects == []

    store_t14 = _fresh_store(tmp_path, name=f"t14-{runner.__module__}.sqlite")
    res_t14 = runner("C-014", seed=11, store_path=store_t14)
    assert res_t14.status == "resolved"
    assert res_t14.proposal_amount == 150000
    assert len(res_t14.refund_effects) == 1
    assert int(res_t14.refund_effects[0]["amount_vnd"]) == 120000
