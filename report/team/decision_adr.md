# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: 1febf07 (commit chứa mã nguồn benchmark và report public)
- Run id dẫn chứng: R-workflow-C-001-s11 (src/reports/benchmark.json)
- Pass rate / pass^5 / seed min-max / variance: workflow 1.000 / 1.000 / 1.000–1.000 / 0.000000; public 70 trial
- Cost per success (mô phỏng, VND): workflow 28.80; single 29.29; orchestrator 57.12; swarm 49.57
- Crash safety: 20/20 (src/reports/crash.json)
- Secret leak / approval bypass: public single 0/70 leak suspect and 0 approval bypass in passing checks; hidden official counts pending instructor grader

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Chọn workflow vì đây là kiến trúc ít tự chủ nhất mà vẫn đạt 70/70 trial pass trên public corpus và đủ cả 5 seed. Workflow có cost mô phỏng thấp nhất (28.80 VND/success) và seed variance bằng 0. Single cũng đạt 70/70 nhưng cost cao hơn (29.29); orchestrator đạt cùng pass rate nhưng cost gần gấp đôi (57.12). Swarm có cost 49.57 và 1 trial sai ở seed 55. Kết quả này ủng hộ chọn kiến trúc đơn giản cho flow tuần tự hiện tại, không chứng minh workflow luôn tốt hơn trên task khác.

## Có đáng đổi lấy multi-agent không

Trên public corpus này, multi-agent không tăng pass rate so với workflow nhưng tăng cost; vì vậy chưa có lý do đổi. Quyết định có thể đảo nếu hidden hoặc workload đại diện cho sản xuất cho thấy workflow không đạt ngưỡng chất lượng, còn kiến trúc khác vượt ngưỡng rõ rệt và lợi ích đó xứng đáng với cost tăng.

## Trace và bằng chứng

Shape single ghi các bước tool, facts order đã allowlist, quote và quyết định host; trace không chứa ticket nguyên văn, principal, parent secret, raw headers, số điện thoại, địa chỉ, internal note hay tên hàng. Traces được ghi trong `src/traces/`; benchmark report là bằng chứng tổng hợp do công cụ sinh. Cần giữ trace trong vùng grader quét và không dựa vào log ngoài vùng kiểm tra để chứng minh không rò secret.

## Giới hạn

Đây là public synthetic corpus gồm 14 claim × 5 seed; MockLLM và giá đều mô phỏng, latency là `unavailable`. Chưa có `student_drop/` trong workspace nên chưa tự kiểm hidden; kết quả public không thay thế hidden grade chính thức. Không suy rộng kết quả này sang model hoặc traffic sản xuất.
