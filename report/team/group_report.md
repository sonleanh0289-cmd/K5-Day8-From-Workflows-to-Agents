# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm: 9999
- Thành viên: xem `TEAM.md`
- Commit chốt (trùng `report/team/decision_adr.md`): `65a47ab`

## 2. Mục tiêu và cách tiếp cận

Bài toán của Lab 8 là xử lý yêu cầu bồi thường hoàn phí vận chuyển cho công ty giả lập LogiX-VN trên cùng một hợp đồng `run_claim(claim_id, *, seed, store_path, crash_at=None) -> RunResult` với 4 kiến trúc có mức tự chủ tăng dần: `workflow` (Shape A), `single` (Shape B), `orchestrator` (Shape C) và `swarm` (Shape D đối chứng).

Nhóm chia việc song song theo từng shape và kiểm thử: thành viên 1 làm `workflow` + tích hợp repo; thành viên 2 làm `single`; thành viên 3 làm `orchestrator` + kiểm tra handoff/trace; thành viên 4 kiểm tra `durability` / crash suite và chạy benchmark tổng hợp. Thứ tự triển khai: chạy xanh cổng host (`pytest -q`) $\rightarrow$ hoàn thiện `workflow` làm chuẩn $\rightarrow$ hoàn thiện `single` và `orchestrator` $\rightarrow$ chuẩn hóa `crash_at` và trace $\rightarrow$ chạy `crash_test` và `benchmark`.

## 3. Giải pháp

Cả ba shape do nhóm viết đều tuân thủ ranh giới cứng: **code quyết định số tiền, policy, approval và idempotency; model chỉ đọc hoặc soạn chữ trả lời**, tuyệt đối không tin số ngày trễ hay câu lệnh giả trong `ticket`.

- **Shape A (`workflow`):** Thực thi tuần tự cố định trong Python: đọc claim qua `get_claim_view` (không `SELECT *`) $\rightarrow$ thiếu `order_id` trả `needs_info` $\rightarrow$ `lookup_order` kiểm tra quyền sở hữu (không thấy trả `escalated`) $\rightarrow$ `compute_compensation` tính quote từ order row và policy hiện hành (`is_current=1`, `effective_date <= as_of`) $\rightarrow$ quote bằng 0 trả `denied` $\rightarrow$ quote > 0 truyền **quote đầy đủ** và `crash_at` vào `durability.issue_refund`. MockLLM chỉ gọi 1 lần (`purpose="draft"`) để soạn câu trả lời.
- **Shape B (`single`):** Sử dụng vòng lặp ReAct `lab8.runtime.run_react` với `max_steps=8`. Ở mỗi bước, `decide` gọi tool chỉ đọc (`get_claim_view`, `lookup_order`, `compute_compensation`), không có quyền gọi `issue_refund`. Sau khi vòng lặp kết thúc ở trạng thái `ready_to_refund`, code bên ngoài mới gọi `durability.issue_refund(..., crash_at=crash_at)` và xử lý `InjectedCrash`.
- **Shape C (`orchestrator`):** Orchestrator tạo gói `handoff` bằng `lab8.handoff.make_handoff` chỉ gồm allowlist `allowed_tools` (`lookup_order`, `lookup_policy`, `compute_compensation`) với `facts={}` (không truyền `parent_secret`, `raw_headers` hay toàn bộ claim row). `run_readonly_investigators` chỉ chạy các tool đọc; orchestrator dựa vào kết quả đã lọc để gọi `durability.issue_refund`.
- **An toàn trace & crash:** Trace ở cả 3 shape chỉ ghi các trường allowlist (`order_facts`, `quote`, `issue_refund`, `decision`), không ghi `ticket`, `parent_secret`, `raw_headers`, SĐT, địa chỉ, tên hàng hay ghi chú nội bộ. Khi gặp `InjectedCrash`, shape ghi event `crash`, gọi `trace.write()` để lưu nhật ký rồi ném tiếp exception ra ngoài cho bài test T12 kiểm chứng.

## 4. Kết quả

Số liệu trích trực tiếp từ `src/reports/benchmark.json` (14 claim public $\times$ 5 seed `11, 22, 33, 44, 55` = 70 trials/shape) và `src/reports/crash.json`:

| Shape | Pass rate | Pass^5 | Seed min–max | Variance | Cost / success (VND) | Mean / p95 steps |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| `workflow` | 1.0000 (70/70) | 1.0000 | 1.0000–1.0000 | 0.0 | 28.80 | 4.43 / 5.0 |
| `single` | 1.0000 (70/70) | 1.0000 | 1.0000–1.0000 | 0.0 | 29.29 | 7.21 / 8.0 |
| `orchestrator` | 1.0000 (70/70) | 1.0000 | 1.0000–1.0000 | 0.0 | 57.12 | 4.29 / 5.0 |
| `swarm` | 0.9857 (69/70) | 0.9286 | 0.9286–1.0000 | 0.000816 | 49.57 | 2.80 / 3.0 |

- **Crash safety (`src/reports/crash.json`):** `20/20` kịch bản pass (gồm `before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`, `amount_conflict_on_retry`, `retry_without_approval`, `swarm_after_effect_before_checkpoint`).
- **Quyết định kiến trúc:** Chọn `workflow` (chi tiết trong `report/team/decision_adr.md` và `report/team/research_card.md`).

## 5. Khó khăn và cách xử lý

- **Lỗi quên truyền `crash_at` ở `single.py`:** Ở lần chạy thử ma trận student đầu tiên, toàn bộ 4 shape chỉ đạt `247 passed` (thiếu 1 test). Kiểm tra mã nguồn phát hiện `single.py` còn `del crash_at` ở đầu hàm `run_claim` và chưa truyền `crash_at` vào `issue_refund`. Sau khi bỏ `del crash_at`, truyền `crash_at=crash_at` và flush trace trước khi re-raise `InjectedCrash`, ma trận student đạt đủ `248 passed`.
- **Lỗi kết nối GitHub & môi trường Windows:** Khi chạy PowerShell gặp khác biệt lệnh kích hoạt venv (`.\.venv\Scripts\Activate.ps1` thay vì `source .venv/bin/activate`) và cấu hình bỏ qua thư mục `venv/` qua `.git/info/exclude` để không push nhầm lên repo nhóm.

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân `report/team/MSSV_HoTen.md`.

## 7. Hạn chế và hướng cải thiện

- **Hạn chế:** MockLLM không phải model sản xuất; kết quả chưa phản ánh biến động chất lượng từ LLM thực tế khi gặp câu hỏi tự nhiên phức tạp; latency để `unavailable`.
- **Điều kiện làm kết luận thay đổi:** Nếu mở rộng bài toán sang xử lý bằng chứng hình ảnh, tài liệu hợp đồng phi cấu trúc hoặc cần đối chiếu nhiều hệ thống bên ngoài không cố định trước được, kiến trúc `orchestrator` với investigator chuyên biệt có thể phù hợp hơn `workflow`.

## 8. Tài liệu tham khảo

- `docs/business_rules.md`, `docs/contracts.md`, `docs/metrics.md` trong repo Lab 8 LogiX-VN.
- Google Research (2026), *Towards a Science of Scaling Agent Systems*.
