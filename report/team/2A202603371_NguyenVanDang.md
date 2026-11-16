# Báo cáo cá nhân — Nguyễn Văn Đăng

## 1. Thông tin thành viên

- Họ tên: Nguyễn Văn Đăng
- MSSV: 2A202603371
- Email: nguyenvandang22012k5@gmail.com
- GitHub: nguyenvandang2201

## 2. Phần việc phụ trách

Triển khai shape C `orchestrator` trong `src/lab8/shapes/orchestrator.py`; kiểm ranh giới handoff, trace và khả năng chạy lại sau crash. Mã của shape chỉ dùng tool đọc cho investigator. Quyền ghi refund thuộc về host.

## 3. Đóng góp cụ thể

- Commit code `14e0d76`: thay stub `not_implemented` bằng luồng đọc claim, tạo handoff có allowlist, chạy investigator, lấy quote từ order và policy hiện hành, rồi chuyển quote đầy đủ vào `durability.issue_refund`.
- Trace chỉ ghi handoff đã lọc và kết quả cần thiết cho audit; không ghi ticket, secret, header hay thông tin cá nhân của order. `crash_at` được chuyển tiếp để kiểm tra retry; trace được ghi trước điểm crash.
- Commit test `d8a4211`: thêm `src/tests/test_orchestrator_boundary.py` với hai test cho ranh giới handoff/trace và crash rồi resume.

## 4. Bằng chứng

- [Pull request triển khai orchestrator](https://github.com/sonleanh0289-cmd/K5-Day8-From-Workflows-to-Agents/pull/1), đã merge vào `main`.
- Chạy `python -m pytest -q -m student -o addopts= -k orchestrator`: 62 passed.
- Chạy `python -m pytest -q tests/test_orchestrator_boundary.py`: 2 passed.
- Benchmark public riêng `orchestrator` trên 14 claim × 5 seed: pass rate 1.000, pass^5 1.000; số này chỉ phản ánh bộ public.
- Bản tích hợp `main` trước commit test: cổng host 64 passed; ma trận student 247 passed, 1 failed ở T12 của `single` (shape bỏ `crash_at`). Đã sửa bằng cách truyền `crash_at` vào `issue_refund` trong `single.py`; sau sửa: cổng host 66 passed, ma trận student 248 passed.
- Crash suite `python -m lab8.crash_test --count 20 --out reports/crash.json`: `crash_safety 20/20`.
- Ablation R1 (`src/reports/ablation_r1_investigator.json`): orchestrator có cùng pass với workflow nhưng cost/success 57.12 so với 28.80 VND — là lý do nhóm chọn workflow thay vì shape mình phụ trách.

## 5. Công cụ AI đã dùng

Dùng OpenAI Codex để đọc contract, hỗ trợ viết code và test, chạy các lệnh kiểm chứng. Kết quả được đối chiếu bằng ma trận public, cổng host và benchmark của repo. Cần tự rà lại handoff allowlist, quyền ghi của host, lý do truyền quote đầy đủ và dữ liệu không được ghi vào trace trước khi trình bày với giảng viên.

## 6. Tự đánh giá

Phần `orchestrator` đạt các test public đã chạy, gồm T11 (retry) và T12 (crash). Chưa có kết quả chấm hidden; benchmark dùng MockLLM và giá token mô phỏng, không chứng minh hiệu năng với model thật.
