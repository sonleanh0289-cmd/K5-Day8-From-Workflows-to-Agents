"""Shape C: an orchestrator with read-only investigators.

The handoff contains no ticket or parent context. Investigators can inspect the
order, current policy, and refund history, but only the host can write a refund.
"""

from __future__ import annotations

import sqlite3

from lab8.db import connect
from lab8.durability import issue_refund
from lab8.handoff import make_handoff
from lab8.mock_llm import complete
from lab8.runtime import run_readonly_investigators
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace


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
    trace = Trace(make_run_id("orchestrator", claim_id, seed))

    # get_claim_view removes the parent secret and headers. The ticket remains
    # untrusted data, so it is neither traced nor forwarded to an investigator.
    budget.add_tool(tool_cost())
    claim = get_claim_view(conn, claim_id)
    if not claim["found"]:
        trace.add("decision", {"status": "failed", "reason": "unknown_claim"})
        return _finish(conn, claim_id, seed, "failed", 0, budget, trace, "unknown_claim")

    if not claim.get("order_id"):
        trace.add("decision", {"status": "needs_info", "reason": "missing_order_id"})
        _draft(budget, seed, "needs_info", 0)
        return _finish(conn, claim_id, seed, "needs_info", 0, budget, trace, "missing_order_id")

    # The model may help plan and draft, but cannot choose tools outside this
    # code-owned allowlist, calculate money, approve, or commit a refund.
    complete(budget, seed=seed, purpose="plan", prompt=f"investigate claim {claim_id}")
    handoff = make_handoff(
        request_id=f"REQ-{claim_id}",
        claim_id=claim_id,
        task="check_order_policy_and_refund_history",
        facts={},
        allowed_tools=[
            "lookup_order",
            "lookup_policy",
            "compute_compensation",
            "lookup_refund_history",
        ],
    )
    trace.add("handoff", safe_dump(handoff))
    investigated = run_readonly_investigators(
        conn, budget, handoff, principal_id=claim["principal_id"]
    )
    tools = investigated["tools"]
    order_view = tools["lookup_order"]
    trace.add(
        "investigator",
        {
            "order_visible": bool(order_view.get("visible")),
            "reason": order_view.get("reason"),
            "refund_history": tools.get("lookup_refund_history", {}),
        },
    )
    if not order_view.get("visible"):
        _draft(budget, seed, "escalated", 0)
        return _finish(
            conn, claim_id, seed, "escalated", 0, budget, trace, order_view.get("reason")
        )

    # compute_compensation uses structured order fields and current policy. The
    # host, not the shape, subtracts earlier refunds on this order.
    quote = tools["compute_compensation"]
    proposal = int(quote["amount_vnd"])
    trace.add("quote", safe_dump(quote))
    if proposal <= 0:
        trace.add("decision", {"status": "denied", "reason": quote.get("reason")})
        _draft(budget, seed, "denied", 0)
        return _finish(conn, claim_id, seed, "denied", 0, budget, trace, quote.get("reason"))

    trace.add("host_call", {"tool": "issue_refund", "proposal_amount": proposal})
    # A crash must propagate. Flush the safe trace first so even a crash run
    # leaves an inspectable artifact; the final run will write it again.
    trace.write()
    outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    if not outcome["ok"]:
        status = "failed" if outcome["conflict"] else "denied"
        trace.add("decision", {"status": status, "reason": outcome["reason"]})
        _draft(budget, seed, status, proposal)
        return _finish(
            conn, claim_id, seed, status, proposal, budget, trace, outcome["reason"]
        )

    trace.add("decision", {"status": "resolved", "reason": outcome["reason"]})
    _draft(budget, seed, "resolved", proposal)
    return _finish(conn, claim_id, seed, "resolved", proposal, budget, trace, None)


def _draft(budget: Budget, seed: int, status: str, proposal: int) -> None:
    """Count the model's drafting cost without letting its text drive decisions."""
    complete(budget, seed=seed, purpose="draft", prompt=f"status={status};proposal={proposal}")


def _finish(
    conn: sqlite3.Connection,
    claim_id: str,
    seed: int,
    status: str,
    proposal: int,
    budget: Budget,
    trace: Trace,
    reason: str | None,
) -> RunResult:
    return finish(
        conn,
        shape="orchestrator",
        claim_id=claim_id,
        seed=seed,
        status=status,
        proposal_amount=proposal,
        budget=budget,
        trace=trace,
        error_reason=reason,
    )
