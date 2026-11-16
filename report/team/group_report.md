# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu được lấy từ `src/reports/benchmark.json` do công cụ lab sinh.

## 1. Thông tin nhóm

- Tên nhóm: Chưa được cung cấp.
- Thành viên và đóng góp: xem `TEAM.md`; hiện workspace mới có thông tin của Kiều Đình Văn.
- Mã nguồn dùng cho benchmark: `17a77b5`.

## 2. Mục tiêu và cách tiếp cận

Nhóm so sánh bốn shape xử lý cùng claim hoàn phí trên cùng public world, MockLLM, bảng giá và các seed 11, 22, 33, 44, 55. Mục tiêu là chọn kiến trúc ít tự chủ nhất vẫn tuân thủ luật nghiệp vụ. Workflow, single và orchestrator được triển khai trong các module riêng; swarm có sẵn được giữ làm baseline.

## 3. Giải pháp

Workflow dùng các bước Python cố định để đọc claim/order, tính quote và gọi host. Single chạy ReAct có giới hạn, chỉ dùng tool đọc; code tính quote và host kiểm approval, cap theo order, idempotency trước khi ghi refund. Orchestrator chuyển context qua handoff allowlist cho investigator chỉ đọc rồi nhận kết quả để quyết định gọi host. Swarm là shape tham chiếu.

Ở các shape, model không quyết định số tiền và không ghi ledger. Trace của single ghi bước tool, facts order đã allowlist, quote, kết quả host và trạng thái; không ghi ticket nguyên văn, secret, header hay thông tin cá nhân nhạy cảm.

## 4. Kết quả

Benchmark gồm 14 public claim × 5 seed = 70 trial mỗi shape. Số liệu tổng hợp:

| Shape | Pass rate | Pass^5 | Seed min–max | Variance | Cost/success (VND mô phỏng) | Mean / p95 steps |
|---|---:|---:|---:|---:|---:|---:|
| workflow | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 28.80 | 4.43 / 5 |
| single | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 29.29 | 7.21 / 8 |
| orchestrator | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 57.12 | 4.29 / 5 |
| swarm | 0.986 | 0.929 | 0.929–1.000 | 0.000816 | 49.57 | 2.80 / 3 |

Workflow là đề xuất hiện tại vì có cùng pass rate public tối đa với cost thấp nhất và mức tự chủ thấp nhất. Crash suite đạt `20/20` trong `src/reports/crash.json`. Workspace chưa có `student_drop/`, nên chưa chạy hidden self-check và chưa có hidden grade chính thức. Xem `report/team/decision_adr.md` và `report/team/research_card.md` để biết quyết định và ablation.

## 5. Khó khăn và cách xử lý

Benchmark lần đầu không mở được SQLite trong thư mục Temp của Windows do quyền truy cập. Chạy lại với quyền phù hợp đã sinh report thành công. Trước đó pytest cũng từng gặp quyền bị từ chối ở thư mục tạm; các kết quả chạy sau cùng là cổng host `65 passed`, ma trận student `single` `62 passed`, T12 của `single` `1 passed`. JSON report được để công cụ sinh, không sửa tay.

## 6. Tổng hợp đóng góp

Đóng góp đã có bằng chứng trong workspace gồm triển khai shape single, test regression và xử lý crash CP3; chi tiết trong `TEAM.md` và `report/team/2A202603376_KieuDinhVan.md`. Các thành viên khác cần bổ sung thông tin, dòng đóng góp và báo cáo cá nhân của mình trước khi nộp nhóm.

## 7. Hạn chế và hướng cải thiện

MockLLM và bảng giá là mô phỏng, không đại diện hóa đơn API; latency là `unavailable`. Public corpus chỉ có 14 claim nên kết quả 100% không đảm bảo hành vi trên hidden hoặc workload thực. Cần chạy hidden self-check khi được cấp `student_drop/` và dùng hidden grade chính thức để xác nhận shape được chọn. Quyết định cũng cần xem lại nếu workload thực có nhiều tác vụ song song hơn hoặc workflow không đạt ngưỡng chất lượng.

## 8. Tài liệu tham khảo

Kim, Y. & Liu, X. (2026). [Towards a science of scaling agent systems: When and why agent systems work](https://www.research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/). Google Research. Nghiên cứu này chỉ làm cơ sở cho giả thuyết; kết luận báo cáo dựa trên số đo của benchmark lab.
