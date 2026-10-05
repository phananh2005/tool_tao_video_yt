# Kế hoạch Xử lý Nút "Xóa Media"

## 1. Yêu cầu (Scope)
- Nút "Xóa Media" (từng script) hoặc "Dọn Media Theme" (cả project) sẽ tiến hành dọn dẹp các tệp tin nặng (ảnh, âm thanh, video) trên ổ cứng.
- Dữ liệu dạng text (title, script, metadata) phải được giữ lại trong SQLite để `Idea Engine` (Phase 1) có thể dùng chống trùng lặp sau này.
- Video/Idea sau khi xóa media sẽ **không hiển thị** trên giao diện Dashboard (phần active_scripts) nữa để tránh rác giao diện.

## 2. Giao thức Dữ liệu (Data Contract & Schema)
- Bảng `ideas`: Tận dụng trường `status`. Thay vì xóa hẳn row, ta sẽ cập nhật `status = 'archived'`.
- Câu query ở màn hình Dashboard: Thêm điều kiện `WHERE i.status != 'archived'` để ẩn các ý tưởng này khỏi UI.
- Phase 1 (Idea Engine) khi check trùng lặp (Dedup) vẫn sẽ SELECT toàn bộ text từ Database bất kể `status` là gì (luồng này hiện tại đã tự động hỗ trợ do không filter theo status khi pull embedding).

## 3. Phân chia Task cho Agents

### 3.1. `db-architect`
- Review lại schema xem có cần thêm trường dữ liệu không (Kết luận: Không cần, dùng chung cột `status` hiện có và set thành `archived`).
- Xác nhận câu lệnh UPDATE an toàn: `UPDATE ideas SET status = 'archived' WHERE id = ?`.

### 3.2. `web-coder`
- **Backend (`app.py`)**:
  - API `DELETE /api/scripts/{script_id}/media`: Gọi hàm xóa folder vật lý + update `status = 'archived'` trong DB.
  - Sửa `get_dashboard()`: Thêm `WHERE i.status != 'archived'`.
- **Frontend (`web/index.html`)**:
  - Gắn sự kiện `@click="deleteScriptMedia"` vào nút bấm.
  - Sau khi gọi API thành công, reload lại Dashboard.

### 3.3. `qa-test-engineer`
- Chạy thử xóa một video đã xong, kiểm tra folder vật lý có bị xóa không.
- Kiểm tra lại Dashboard xem video đó có biến mất không.
- Kiểm tra các video "đang làm dở" không bị ảnh hưởng nếu ấn nút dọn cấp Project.
