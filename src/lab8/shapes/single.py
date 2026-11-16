"""Shape B — one ReAct agent. Student work.

Use `lab8.runtime.run_react` with max_steps=8. `decide` may pick a read tool.
It must not call `issue_refund`. After the loop, the host validates the quote
and is the only writer.

A decide() that trusts ticket text over the order row will fail hidden claims
where the customer overstates the delay or cites a superseded clause.

Per-order cap: an order may already have been refunded by an earlier claim.
The read tool `lookup_refund_history` shows how much. The host still enforces
the cap, so pass the full quote to `durability.issue_refund`, not a net amount.

Caps: stop at 8 steps. Count model calls in the Budget so cost stays comparable.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.runtime import run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
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


def _run(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    seed: int,
    crash_at: str | None = None,
) -> RunResult:
    budget = Budget()
    run_id = make_run_id("single", claim_id, seed)
    trace = Trace(run_id)

    def decide(observation: dict[str, Any]) -> dict[str, Any]:
        previous_tool = observation.get("last_tool")
        previous_result = observation.get("last_result")
        if previous_tool:
            _trace_tool_result(trace, previous_tool, previous_result or {})

        stage = str(previous_tool or "start")
        complete(budget, seed=seed, purpose="single", prompt=stage)

        if previous_tool is None:
            action = {"tool": "get_claim_view", "args": {"claim_id": claim_id}}
        elif previous_tool == "get_claim_view":
            claim = previous_result or {}
            if not claim.get("found"):
                return _final(trace, "failed", 0, "unknown_claim")
            if not claim.get("order_id"):
                return _final(trace, "needs_info", 0, "missing_order_id")
            action = {
                "tool": "lookup_order",
                "args": {
                    "order_id": claim["order_id"],
                    "principal_id": claim["principal_id"],
                },
            }
        elif previous_tool == "lookup_order":
            order_result = previous_result or {}
            if not order_result.get("visible"):
                return _final(
                    trace,
                    "escalated",
                    0,
                    order_result.get("reason", "order_not_visible"),
                )
            action = {
                "tool": "compute_compensation",
                "args": {"order": order_result["order"]},
            }
        elif previous_tool == "compute_compensation":
            quote = previous_result or {}
            proposal = int(quote.get("amount_vnd", 0))
            if proposal <= 0:
                return _final(
                    trace,
                    "denied",
                    0,
                    quote.get("reason", "no_compensation"),
                )
            return _final(trace, "ready_to_refund", proposal, None)
        else:
            return _final(trace, "failed", 0, "unexpected_tool_result")

        trace.add("decision", {"tool": action["tool"]})
        return action

    react_result = run_react(
        conn,
        budget,
        observation={"claim": {"claim_id": claim_id}},
        decide=decide,
        max_steps=8,
    )
    final = react_result["final"]
    status = final.get("status", "failed")
    proposal = int(final.get("proposal_amount", 0))
    error_reason = final.get("error_reason")

    if react_result["stopped"] != "final":
        status = "failed"
        proposal = 0
        error_reason = "step_cap"

    if status != "ready_to_refund":
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=error_reason,
        )

    try:
        outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise
    trace.add(
        "host_refund",
        {
            "ok": bool(outcome["ok"]),
            "reason": outcome["reason"],
            "conflict": bool(outcome["conflict"]),
        },
    )
    if not outcome["ok"]:
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status="failed" if outcome["conflict"] else "denied",
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=outcome["reason"],
        )

    return finish(
        conn,
        shape="single",
        claim_id=claim_id,
        seed=seed,
        status="resolved",
        proposal_amount=proposal,
        budget=budget,
        trace=trace,
    )


def _final(
    trace: Trace,
    status: str,
    proposal_amount: int,
    error_reason: str | None,
) -> dict[str, Any]:
    trace.add(
        "decision",
        {"status": status, "proposal_amount": proposal_amount},
    )
    return {
        "final": {
            "status": status,
            "proposal_amount": proposal_amount,
            "error_reason": error_reason,
        }
    }


def _trace_tool_result(trace: Trace, tool: str, result: dict[str, Any]) -> None:
    if tool == "get_claim_view":
        payload = {
            "found": bool(result.get("found")),
            "claim_id": result.get("claim_id"),
            "order_id": result.get("order_id"),
        }
    elif tool == "lookup_order":
        payload = {
            "visible": bool(result.get("visible")),
            "reason": result.get("reason"),
        }
        order = result.get("order") or {}
        if order:
            payload["order_facts"] = {
                "status": order.get("status"),
                "delay_days": order.get("delay_days"),
                "shipping_fee_vnd": order.get("shipping_fee_vnd"),
                "paid_vnd": order.get("paid_vnd"),
                "damage_verified": order.get("damage_verified"),
            }
    elif tool == "compute_compensation":
        payload = {
            "amount_vnd": result.get("amount_vnd"),
            "reason": result.get("reason"),
            "clause_ids": result.get("clause_ids"),
            "parts": result.get("parts"),
        }
    else:
        payload = {"result": "omitted"}
    trace.add("tool_result", {"tool": tool, **payload})
