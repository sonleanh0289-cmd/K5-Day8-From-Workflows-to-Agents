# Báo cáo cá nhân — Kiều Đình Văn

## 1. Thông tin thành viên

- Họ tên: Kiều Đình Văn
- MSSV: 2A202603376
- Email: vankd2307@gmail.com
- GitHub: [vankd2307](https://github.com/vankd2307)

## 2. Phần việc phụ trách

- Shape B — single ReAct agent trong `src/lab8/shapes/single.py` và test regression riêng cho shape này.

## 3. Đóng góp cụ thể

- Triển khai luồng xử lý claim cho shape `single`: đọc claim và order bằng tool, tính quote qua `compute_compensation`, rồi yêu cầu host kiểm tra và ghi refund.
- Giới hạn vòng ReAct ở 8 bước; ghi trace theo contract và chỉ đưa các field đã chọn lọc vào trace.
- Thêm test `test_single_resolves_claim_and_writes_matching_trace`, kiểm tra claim `C-001`, số tiền đề xuất/hoàn, audit và `run_id` trong trace.
- Bổ sung truyền `crash_at` vào `issue_refund`; khi crash được tiêm, shape ghi trace đã lọc rồi để `InjectedCrash` truyền ra ngoài.
- Tham gia CP5 bằng cách chạy public benchmark 4 shape × 14 claim × 5 seed và ghi nhận metric vào hồ sơ nhóm.

## 4. Bằng chứng

- Commit triển khai shape: `a07d88c` — `Implement single ReAct shape CP2`.
- Commit thêm test: `e4e1ccc` — `Add focused single shape regression test`.
- Commit bổ sung crash handling: `1e1a156` — `Complete single shape crash handling`.
- Test: `src/tests/test_single_shape.py::test_single_resolves_claim_and_writes_matching_trace`.
- Đã chạy `python -m pytest -q tests/test_single_shape.py`; kết quả: `1 passed`.
- Đã chạy test student của `single` bằng `python -m pytest -q -m student -o addopts= -k "single and not workflow and not orchestrator and not swarm"`; kết quả: `62 passed`.
- Đã chạy riêng test T12 crash/resume của `single`; kết quả: `1 passed`.
- Cổng host `python -m pytest -q`: `65 passed, 248 deselected`.
- Crash suite `python -m lab8.crash_test --count 20 --out reports/crash.json`: `crash_safety 20/20`.
- Public benchmark `src/reports/benchmark.json`, run id dẫn chứng `R-workflow-C-001-s11`: workflow 70/70 pass, pass^5 1.000, cost/success mô phỏng 28.80 VND; toàn benchmark có 70 trial mỗi shape.
- `python -m lab8.check_submission`: `0 FAIL, 1 WARN` trước khi commit các file CP5; warning là working tree còn thay đổi.
- Các commit đã có trên nhánh `vankd` và được push lên `origin/vankd`.

## 5. Công cụ AI đã dùng

- Dùng ChatGPT để đọc hướng dẫn lab, giải thích contract của shape `single`, hỗ trợ triển khai và tạo test regression.
- Tự kiểm tra bằng pytest: test regression riêng `1 passed`, ma trận student `single` `62 passed`, T12 `1 passed`, cổng host `65 passed`; crash suite đạt `20/20`.

## 6. Tự đánh giá

Đã hoàn thành phần single ở CP2–CP4 và tạo bằng chứng public benchmark ở CP5. Benchmark public đề xuất workflow là kiến trúc đủ dùng với cost thấp nhất; quyết định nhóm và thông tin các thành viên khác cần được xác nhận. Hidden self-check/grade chưa thực hiện vì workspace chưa có `student_drop/`.
