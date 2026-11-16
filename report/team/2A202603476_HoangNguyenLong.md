## 1. Thông tin thành viên

- Họ tên: Hoàng Nguyên Long
- MSSV: 2A202603476
- GitHub: longhn-0108

## 2. Phần việc phụ trách

- **Ledger / Policy / Crash Safety & Evaluation**:
  - Kiểm thử bất biến của SQLite ledger, idempotency key (`refund:{claim_id}`), approval matching, per-order cap (T13, T14) và crash/resume (`InjectedCrash`).
  - Chạy bộ `crash_test` (20 kịch bản) xuất `src/reports/crash.json` và chạy `benchmark` (4 shape × 14 claim × 5 seed = 280 trials) xuất `src/reports/benchmark.json`.
  - Đóng góp số liệu thực nghiệm vào `report/team/decision_adr.md`, `report/team/research_card.md` và `report/team/group_report.md`.

## 3. Đóng góp cụ thể

- Viết bộ test `src/tests/test_ledger_extra.py` (8 test cases):
  - `test_ledger_idempotent_replay_keeps_single_row`: xác minh gọi lại cùng claim giữ đúng 1 dòng `refund_ledger` và 1 audit `refund_committed`.
  - `test_ledger_amount_conflict_preserves_original_amount`: xác minh gọi lại với số tiền khác trả `amount_conflict` và không ghi đè dòng cũ.
  - `test_approval_from_other_claim_is_denied_with_audit`: xác minh mượn `approval_id` của claim khác bị host chặn và ghi audit `policy_denied`.
  - `test_crash_and_resume_always_leaves_one_refund`: kiểm tra cả 3 điểm crash (`before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`) đều an toàn khi resume.
  - `test_all_student_shapes_respect_per_order_cap`: xác minh cả 3 shape `workflow`, `single`, `orchestrator` đều qua T13 (`denied`) và T14 (`proposal_amount=150000`, thực nhận `120000`).

## 4. Bằng chứng

- File test: `src/tests/test_ledger_extra.py` (`python -m pytest -q tests/test_ledger_extra.py` → `8 passed`).
- Crash suite: `python -m lab8.crash_test --count 20 --out reports/crash.json` → `crash_safety 20/20`.
- Benchmark 4 shape × 5 seed: `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`:
  - `workflow`: `pass_rate = 1.0`, `pass^5 = 1.0`, `variance = 0.0`, `cost_per_success = 28.80 VND`
  - `single`: `pass_rate = 1.0`, `pass^5 = 1.0`, `variance = 0.0`, `cost_per_success = 29.29 VND`
  - `orchestrator`: `pass_rate = 1.0`, `pass^5 = 1.0`, `variance = 0.0`, `cost_per_success = 57.12 VND`
  - `swarm`: `pass_rate = 0.9857` (69/70), `pass^5 = 0.9286`, `variance = 0.000816`, `cost_per_success = 49.57 VND` (fail `C-002` ở seed 55).

## 5. Công cụ AI đã dùng

- Dùng trợ lý AI để rà soát các edge-case của `durability.py` / `policy.py` (approval mismatch, per-order cap, 3 điểm `InjectedCrash`) và gợi ý cấu trúc test pytest.
- Tự kiểm tra bằng cách chạy trực tiếp `pytest`, `crash_test` và `benchmark` trong môi trường `.venv` sạch, đối chiếu số liệu trong `src/reports/benchmark.json` và `src/reports/crash.json`.

## 6. Tự đánh giá

- Hoàn thành đầy đủ test kiểm chứng ledger/crash/approval và chạy đánh giá công bằng trên 4 shape × 5 seed.
- Hiểu rõ cơ chế idempotency (`refund:{claim_id}`), transaction `BEGIN IMMEDIATE` chống race condition khi tính trần theo đơn, và lý do nhóm chọn `workflow` (đạt 100% ở mọi seed với chi phí thấp nhất).
