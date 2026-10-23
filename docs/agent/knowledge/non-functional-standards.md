# Chuẩn phi chức năng — Hiệu năng & Truy vấn SQLite TubeChain

Tài liệu quy định các tiêu chuẩn kỹ thuật về hiệu năng, truy cập dữ liệu và ranh giới hệ thống trong TubeChain.

## 1. Nguyên tắc cốt lõi
- **Số lần gọi cơ sở dữ liệu quan trọng hơn độ phức tạp câu lệnh:** Số lượng truy vấn SQLite phải là hằng số $O(1)$, tuyệt đối không tăng tuyến tính theo số bản ghi $O(N)$.
- **Lọc và gộp ở nơi có dữ liệu:** Đẩy việc lọc, sắp xếp xuống SQLite, chỉ lấy các trường cần thiết.
- **An toàn cục bộ:** Mọi dữ liệu lưu trữ tại máy người dùng (`data/tubechain.db`), không tạo kết nối cloud DB.

## 2. Ngưỡng số truy vấn mỗi API endpoint (SQLite)

Các ngưỡng dưới đây là giới hạn trên bắt buộc khi thiết kế và hiện thực API trong `app.py`:

| Loại thao tác API | Ngưỡng truy vấn tối đa | Thành phần bao gồm |
|---|---|---|
| **Đọc chi tiết (Detail)** | 3 truy vấn | Bản ghi chính + bản ghi phụ liên quan (ví dụ: script + voiceover) |
| **Đọc danh sách (List)** | 4 truy vấn | Đếm tổng số (nếu có) + dữ liệu trang + quan hệ cần nạp kèm |
| **Ghi (Create / Update / Delete)** | 6 truy vấn | Kiểm tra tồn tại + kiểm tra ràng buộc + ghi dữ liệu chính + cập nhật trạng thái liên quan |

### Quy tắc thực thi ngưỡng
- **Bắt buộc đánh giá lúc lập kế hoạch:** Khi thiết kế endpoint mới hoặc sửa endpoint hiện có, phải dự tính số truy vấn SQL. Nếu nghiệp vụ buộc phải vượt ngưỡng, phải **DỪNG LẠI** và giải thích phương án gộp truy vấn trước khi viết code.
- **TUYỆT ĐỐI KHÔNG** gọi SQLite bên trong vòng lặp (`for`/`while`). Phải dùng câu lệnh `IN (...)`, `JOIN`, hoặc xử lý theo lô (batch).
- **TUYỆT ĐỐI KHÔNG** lặp lại truy vấn lấy cùng một dữ liệu trong cùng một vòng đời request.

## 3. Ranh giới tác vụ nặng & Đồng bộ
- **Tác vụ AI dài (sinh ý tưởng, kịch bản, ảnh qua Gemini Web):** Có cơ chế chờ và timeout rõ ràng, xử lý lỗi khi browser/selector bị treo.
- **Tác vụ tổng hợp âm thanh (TTS Phase 3.5):** Chạy async hoặc tách biệt từng scene, có thời gian nghỉ (jitter) để tránh rate-limit.
- **Tác vụ dựng video (FFmpeg Phase 5):** Bắt buộc dùng `StreamingResponse` (Server-Sent Events) để truyền log tiến độ realtime cho người dùng, không để client bị timeout.

## 4. An toàn dữ liệu & Truy vấn tham số hóa
- **Bắt buộc dùng tham số hóa (Parameterized Queries):** Mọi câu truy vấn SQL dùng `cursor.execute("... WHERE id = ?", (val,))`.
- **TUYỆT ĐỐI KHÔNG** dùng f-string hoặc format chuỗi để ghép giá trị vào câu lệnh SQL nhằm ngăn chặn hoàn toàn nguy cơ SQL Injection.
- **TUYỆT ĐỐI KHÔNG** xóa dữ liệu dự án của người dùng trừ khi có yêu cầu rõ ràng qua API chuyên trách (`/api/projects/{id}/media`).
