# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: 65a47ab
- Run id dẫn chứng: R-workflow-C-001-s11 (xem `src/reports/benchmark.json`, 70 trials trên 14 claim × 5 seed 11,22,33,44,55)
- Pass rate / pass^5 / seed min-max / variance: 1.0 / 1.0 / 1.0–1.0 / 0.0
- Cost per success (mô phỏng, VND): 28.80
- Crash safety: 20/20 (src/reports/crash.json)
- Secret leak / approval bypass: 0 / 0

## Vì sao shape này

Trên cùng bộ 14 claim public và 5 seed (`11, 22, 33, 44, 55`, tổng 70 trial mỗi shape trong `src/reports/benchmark.json`), ba shape `workflow`, `single` và `orchestrator` đều đạt `pass_rate = 1.0`, `pass^5 = 1.0` và `seed_variance = 0.0`, trong khi `swarm` chỉ đạt `pass_rate = 0.9857` (69/70) và `pass^5 = 0.9286` (fail `C-002` ở seed `55` do tin số ngày trễ ghi trong ticket thay vì cột `delay_days` của order). Trong ba shape đạt 100%, `workflow` là kiến trúc **ít tự chủ nhất** và **rẻ nhất**: `cost_per_success_vnd = 28.80 VND` (rẻ hơn `single` 29.29 VND và rẻ hơn gần một nửa so với `orchestrator` 57.12 VND), chỉ gọi MockLLM 1 lần để soạn chữ trả lời, không có rủi ro model đi sai đường hay đọc nhầm trường dữ liệu.

## Có đáng đổi lấy multi-agent không

Không đáng. Với bài toán xử lý claim có quy trình cố định và nguồn sự thật nằm trong SQLite (`orders`, `policies`, `approvals`), tăng mức tự chủ lên multi-agent (`orchestrator` hay `swarm`) không tăng độ chính xác (thậm chí `swarm` giảm `pass^5` xuống `0.9286`) mà lại tăng chi phí gần gấp đôi (`57.12` VND ở `orchestrator` và `49.57` VND ở `swarm` so với `28.80` VND ở `workflow`) và tăng số tool call trung bình (`5.57` và `4.66` so với `2.79`). Quyết định này chỉ đảo lại khi bài toán phát sinh nhiều nguồn dữ liệu phi cấu trúc cần điều tra động hoặc phải tổng hợp nhiều bước tra cứu không thể cố định trước bằng code Python.

## Trace và bằng chứng

Trace của nhóm ghi các event: `tool` (`get_claim_view` với `found`/`has_order_id`; `lookup_order` với `visible` và `order` đã qua allowlist), `quote` (`amount_vnd`, `reason`, `clause_ids`), `issue_refund` (`ok`, `reason`, `conflict`), `crash` (khi có `InjectedCrash`), và `decision` (`status`, `proposal_amount`, `reason`). Nhóm cố ý **không** ghi: `ticket`, `claim` row thô, `principal_id`, `parent_secret`, `raw_headers`, SĐT, địa chỉ, tên hàng, và `internal_note` để tránh rò rỉ `CANARY_SECRET_*` hoặc PII và ngăn prompt injection từ ticket đi vào nhật ký. Nếu trace nằm ngoài chỗ scanner quét được, hệ thống chứng minh không lộ secret bằng việc kiểm tra ở mã nguồn (chỉ đọc qua `get_claim_view` / `lookup_order` allowlist và `make_handoff`) kết hợp unit test tự động (`test_workflow_extra.py`) assert không xuất hiện các chuỗi cấm trong file trace JSON.

## Giới hạn

MockLLM không phải model sản xuất; hành vi tool calling, sai lệch diễn giải ngôn ngữ tự nhiên và chi phí thật của LLM thương mại chưa được phản ánh. Latency để `unavailable` vì chạy mô phỏng offline. Không sửa JSON cho đủ 0.75.
