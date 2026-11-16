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

## 4. Bằng chứng

- Commit triển khai shape: `a07d88c` — `Implement single ReAct shape CP2`.
- Commit thêm test: `e4e1ccc` — `Add focused single shape regression test`.
- Test: `src/tests/test_single_shape.py::test_single_resolves_claim_and_writes_matching_trace`.
- Đã chạy `python -m pytest -q tests/test_single_shape.py`; kết quả được ghi nhận: `1 passed`.
- `src/reports/crash.json` ghi nhận crash suite 20/20; suite này không thay thế việc kiểm tra riêng T12 của shape `single`.
- Các commit trên nằm trong lịch sử nhánh `vankd`; nhánh đã được cập nhật và push lên `origin/vankd`.

## 5. Công cụ AI đã dùng

- Dùng ChatGPT để đọc hướng dẫn lab, giải thích contract của shape `single`, hỗ trợ triển khai và tạo test regression.
- Tự kiểm tra bằng cách chạy test riêng `python -m pytest -q tests/test_single_shape.py` và xem kết quả `1 passed`.

## 6. Tự đánh giá

Đã hoàn thành phần triển khai CP2 và nối crash injection theo CP3. Test regression riêng đã pass; cần chạy lại T11/T12 cho `single` để xác nhận hành vi retry/crash của shape này sau thay đổi.
