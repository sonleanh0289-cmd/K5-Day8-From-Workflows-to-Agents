# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R1 |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Google Research, 2026, *Towards a Science of Scaling Agent Systems* (benchmark thực nghiệm trên các cấu trúc multi-agent) |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Với các tác vụ có cấu trúc tuần tự cao và phụ thuộc trạng thái chặt chẽ, việc tăng số lượng agent/lời gọi phối hợp làm tăng chi phí (token/tool calls) mà không cải thiện độ chính xác so với kiến trúc đơn giản hơn. |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Kết luận trong Lab 8 giới hạn trên tập 14 claim public của LogiX-VN (`public_claims.jsonl`), chạy với `MockLLM` theo 5 seed (`11,22,33,44,55`), giá mô phỏng cố định (`pricing.yaml`), latency `unavailable`. |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Khi chuyển từ `workflow` (tuần tự, 1 model call soạn chữ) sang `orchestrator` (thêm investigator read-only + handoff) hoặc `single` (vòng ReAct), `pass_rate` giữ nguyên ở `1.0` nhưng `cost_per_success_vnd` sẽ tăng lên đáng kể (từ ~29 VND lên ~57 VND với `orchestrator`). |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Giữ cố định: `MockLLM`, bộ tool và host (`durability.issue_refund`, `compute_compensation`), 5 seed (`11,22,33,44,55`), 14 claim public, bảng giá `pricing.yaml`, cùng grader `metrics.py`. Biến duy nhất thay đổi: topology (`workflow` vs `single` vs `orchestrator` vs `swarm`). |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Lỗi tin vào số ngày trễ trong ticket ở `swarm` (seed 55) đo bằng `pass_rate`, `pass^5`, `seed_variance`; chi phí phối hợp đo bằng `cost_per_success_vnd`, `mean_model_calls`, `mean_tool_calls`; an toàn đo bằng `secret_leak_count` và `approval_bypass_count`. |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn): `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`
- Run id / file report: `src/reports/benchmark.json` (ví dụ `R-workflow-C-001-s11`, `R-single-C-001-s11`, `R-orchestrator-C-001-s11`, `R-swarm-C-001-s11`)
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu: **Đúng với giả thuyết.** `workflow`, `single` và `orchestrator` đều đạt `pass_rate = 1.0` (`70/70`), `pass^5 = 1.0`, `seed_variance = 0.0`; trong khi `cost_per_success_vnd` tăng từ `28.80 VND` (`workflow`) lên `29.29 VND` (`single`) và `57.12 VND` (`orchestrator`, gần gấp đôi), `mean_tool_calls` tăng từ `2.79` lên `5.57`. Riêng `swarm` giảm `pass_rate` xuống `0.9857` (`69/70`), `pass^5 = 0.9286`, `cost_per_success_vnd = 49.57 VND`.
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
