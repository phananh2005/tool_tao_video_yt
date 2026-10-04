# Kế hoạch Triển khai Giao diện Web (Web UI Local)

## Mục tiêu
Chuyển đổi toàn bộ trải nghiệm từ dòng lệnh (CLI) sang một giao diện Web Local trực quan. Giúp người dùng dễ dàng theo dõi tiến độ, xem trước hình ảnh/video, và quan trọng nhất là CÓ QUYỀN CHỈNH SỬA (Edit) dữ liệu ở từng bước trước khi chốt hạ chuyển sang bước tiếp theo.

## Stack Công Nghệ (Nhẹ & Không cần Build)
- **Backend:** `FastAPI` (Python) - Rất mạnh trong việc xử lý các tác vụ bất đồng bộ (Async) như gọi Playwright hay render FFmpeg mà không làm treo Web.
- **Frontend:** HTML/CSS/JavaScript thuần. Sử dụng `TailwindCSS` và `Vue.js` (dạng nhúng CDN, không cần cài Node.js). Giúp giao diện hiện đại, code cực kỳ nhẹ và độc lập.
- **Giao tiếp:** Gọi REST API qua `fetch()`.

## Kiến trúc 7 Màn hình (Theo AGENTS.md)

1. **🏠 Màn hình 1: Dashboard (Quản lý Dự án)**
   - Hiển thị danh sách các Dự án (từ Database).
   - Thanh trạng thái tiến độ: Dự án này đang kẹt ở Phase nào (Chưa có script? Chưa có ảnh?).

2. **💡 Màn hình 2: Idea Factory (Phase 1)**
   - Form chọn Chủ đề (Themes).
   - Nút `[Brainstorm]`.
   - Bảng (Table) hiển thị 5 Ý tưởng. Hiển thị rõ mác màu Xanh (Pass) / Vàng (Warn) / Đỏ (Drop).

3. **📝 Màn hình 3: Script Builder (Phase 2)**
   - Trình bày Kịch bản dưới dạng Timeline / Thẻ (Cards).
   - **Tính năng ăn tiền:** Cho phép người dùng bấm vào dòng Text để tự sửa chữ (Edit) nội dung hình ảnh hoặc phân cảnh nếu AI viết chưa vừa ý.

4. **🎙️ Màn hình 4: Voice Studio (Phase 3 & 3.5)**
   - Hiển thị Lời bình (Spoken Text) kèm theo một nút `[▶️ Play]` để nghe thử file âm thanh AI sinh ra.
   - Nếu nghe không ưng, có thể gõ lại chữ và bấm nút `[Thu âm lại]`.

5. **🎨 Màn hình 5: Art Gallery (Phase 4)**
   - Hiển thị toàn bộ Hình ảnh AI vẽ dưới dạng Lưới (Grid/Gallery).
   - Nút `[Vẽ lại ảnh này]` ở dưới mỗi ảnh (Dùng khi AI vẽ hỏng hoặc bị lệch khuôn mặt).

6. **🎬 Màn hình 6: Render Room (Phase 5)**
   - Nút to đùng `[Bắt đầu Ghép Video]`.
   - Một màn hình đen hiển thị log Render của FFmpeg theo thời gian thực.
   - Trình phát Video (Video Player) xuất hiện khi render xong để xem trực tiếp trên Web.

7. **🚀 Màn hình 7: SEO & Publish (Phase 6)**
   - Bố cục 2 cột: Cột trái hiện Thumbnail to đùng, cột phải hiện Form Text (Title, Desc, Tags, Timestamps) kèm nút `[Copy All]`.

## Lộ trình Thực thi của agent `web-coder`
- **Bước 1:** Viết file `app.py` chứa bộ khung FastAPI, mapping với các logic sẵn có trong thư mục `modules/`.
- **Bước 2:** Xây dựng file `index.html` và các file cấu trúc web trong thư mục `web/`.
- **Bước 3:** Đấu nối API bằng Javascript và kiểm thử toàn bộ luồng tạo 1 video trên Web.
