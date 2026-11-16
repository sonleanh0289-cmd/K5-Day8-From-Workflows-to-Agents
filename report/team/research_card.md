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
| CÂU | R1 / R2 / R3 / R4 | R1 · Scaling |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Kim & Liu, Google Research (2026), [Towards a science of scaling agent systems: When and why agent systems work](https://www.research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/); controlled benchmark across 180 agent configurations. |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Trong benchmark của tác giả, phối hợp nhiều agent giúp task song song hóa nhưng có thể làm giảm hiệu quả ở task tuần tự. |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Kết luận thuộc setup, model và benchmark của nghiên cứu; không khẳng định áp dụng trực tiếp cho LogiX-VN, MockLLM hoặc hidden set của lab. |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Với luồng claim chủ yếu tuần tự, workflow và orchestrator có thể đạt pass rate tương tự; workflow dự kiến giảm cost/success so với orchestrator ít nhất 20%. |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Ablation topology: so workflow với orchestrator; giữ MockLLM, tool inventory, 14 public claims, seeds 11/22/33/44/55, giá và evaluator cố định. Đổi shape kiến trúc; số lượt gọi tool/model và cost là kết quả đo, không được ép bằng nhau. |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Dự kiến phối hợp thêm không tăng pass tương xứng với cost trên flow tuần tự. Đo pass rate, pass^5, seed variance, cost/success và mean/p95 steps từ `reports/benchmark.json`; lỗi dự kiến: cost/success tăng mà pass rate không tăng. |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn): `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`
- Run id / file report: `R-workflow-C-001-s11`; `src/reports/benchmark.json`.
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu: Ủng hộ giả thuyết về cost: workflow và orchestrator cùng pass 70/70 (pass rate 1.000, pass^5 1.000), nhưng cost/success lần lượt là 28.80 và 57.12 VND, workflow thấp hơn khoảng 49%. Chưa có chênh lệch pass để đánh giá hiệu năng; không kết luận về task khác.
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
