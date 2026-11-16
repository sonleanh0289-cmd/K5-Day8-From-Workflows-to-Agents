"""Shape A — deterministic workflow. Student work.

Signature (do not change):

    run_claim(claim_id, *, seed, store_path, crash_at=None) -> RunResult

Suggested steps. Money stays in code (`lab8.tools.compute_compensation`).

1. Open the store. Read the claim through `get_claim_view` (not SELECT *).
2. Missing order_id -> status `needs_info`. Do not write the ledger.
3. `lookup_order`. If not visible -> `escalated`. Do not copy phone, address, item, internal note.
4. Quote from the order row. Ignore delay numbers written in the ticket.
5. Quote amount 0 -> `denied`. Do not call issue_refund.
6. Quote amount > 0 -> `durability.issue_refund(conn, claim_id, <full quote>)`.
   Pass the FULL quote. The host checks the claim's own approval and subtracts
   what earlier claims already got for the same order (T13, T14). Do not
   subtract it yourself or the host subtracts twice.
   Auth failure or order already refunded -> `denied` (the host writes `policy_denied`).
   `proposal_amount` stays the full quote. Amount conflict -> `failed`.
7. Success -> `resolved`. One ledger row, one `refund_committed` audit.
8. Use MockLLM only to draft the reply text, if you want a model call at all.

The model must not choose the refund amount and must not commit the refund.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.

Implementation notes (nhóm):
- Mọi quyết định là code Python cố định; không có vòng lặp model.
- Ticket KHÔNG được đọc để lấy số ngày trễ hay mã đơn: chỉ tin order row + policy hiện hành.
- Trace chỉ ghi field đã qua allowlist (order view của `lookup_order`, quote),
  không ghi ticket, claim row thô, principal_id hay order row thô.
- MockLLM chỉ được gọi một lần ở cuối để soạn chữ trả lời (purpose="draft").
"""

from __future__ import annotations

import sqlite3
from typing import Any

from lab8 import durability
from lab8.db import connect
from lab8.mock_llm import complete
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.tools import compute_compensation, get_claim_view, lookup_order, tool_cost
from lab8.trace import Trace

SHAPE = "workflow"


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def _run(conn: sqlite3.Connection, claim_id: str, *, seed: int, crash_at: str | None) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id(SHAPE, claim_id, seed))

    def done(status: str, proposal: int, reason: str | None) -> RunResult:
        trace.add("decision", {"status": status, "proposal_amount": int(proposal), "reason": reason})
        return finish(
            conn,
            shape=SHAPE,
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=reason,
        )

    try:
        # Step 1 — đọc claim qua view allowlist (không SELECT *, không đụng parent_secret).
        budget.add_tool(tool_cost())
        claim = get_claim_view(conn, claim_id)
        if not claim.get("found"):
            trace.add("tool", {"name": "get_claim_view", "found": False})
            return done("failed", 0, "unknown_claim")
        trace.add("tool", {"name": "get_claim_view", "found": True, "has_order_id": bool(claim["order_id"])})

        # Step 2 — thiếu order_id: hỏi lại khách, không đoán mã đơn từ ticket.
        if not claim["order_id"]:
            _draft(budget, seed, "needs_info")
            return done("needs_info", 0, "missing_order_id")

        # Step 3 — tra đơn trong phạm vi principal của claim.
        budget.add_tool(tool_cost())
        order_view = lookup_order(conn, claim["order_id"], claim["principal_id"])
        if not order_view.get("visible"):
            trace.add("tool", {"name": "lookup_order", "visible": False, "reason": order_view.get("reason")})
            _draft(budget, seed, "escalated")
            return done("escalated", 0, order_view.get("reason"))
        order: dict[str, Any] = dict(order_view["order"])
        trace.add("tool", {"name": "lookup_order", "visible": True, "order": safe_dump(order)})

        # Step 4 — tiền do code tính từ order row + policy hiện hành. Ticket bị bỏ qua.
        budget.add_tool(tool_cost())
        quote = compute_compensation(conn, order)
        proposal = int(quote["amount_vnd"])
        trace.add(
            "quote",
            {
                "amount_vnd": proposal,
                "reason": quote.get("reason"),
                "clause_ids": list(quote.get("clause_ids") or []),
            },
        )

        # Step 5 — quote 0: từ chối, không gọi host.
        if proposal <= 0:
            _draft(budget, seed, "denied")
            return done("denied", 0, quote.get("reason"))

        # Step 6 — host là cửa ghi duy nhất. Truyền QUOTE ĐẦY ĐỦ và crash_at.
        # Không bắt InjectedCrash: để crash lan ra ngoài (T12), nhưng flush trace trước.
        try:
            outcome = durability.issue_refund(conn, claim_id, proposal, crash_at=crash_at)
        except durability.InjectedCrash:
            trace.add("crash", {"at": crash_at})
            trace.write()
            raise
        trace.add(
            "issue_refund",
            {
                "ok": bool(outcome["ok"]),
                "reason": outcome.get("reason"),
                "conflict": bool(outcome.get("conflict")),
            },
        )

        if not outcome["ok"]:
            status = "failed" if outcome.get("conflict") else "denied"
            _draft(budget, seed, status)
            return done(status, proposal, outcome.get("reason"))

        # Step 7 — thành công.
        _draft(budget, seed, "resolved")
        return done("resolved", proposal, None)

    except durability.InjectedCrash:
        raise
    except Exception as exc:  # run_claim không được ném exception ra grader.
        trace.add("error", {"type": type(exc).__name__})
        return done("failed", 0, f"exception:{type(exc).__name__}")


def _draft(budget: Budget, seed: int, status: str) -> None:
    """Step 8 — model chỉ soạn chữ trả lời; không quyết tiền, không ghi ledger."""
    complete(budget, seed=seed, purpose="draft", prompt=f"status={status}")
