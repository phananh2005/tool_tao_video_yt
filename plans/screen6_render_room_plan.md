# Kế hoạch Hoàn thiện Màn hình 6: Render Room (Phase 5)

## 1. Hiện trạng & Vấn đề tồn đọng
- **Giao diện tĩnh & thô sơ:** UI hiện tại của Phase 5 chỉ hiển thị một dòng chữ cứng "Video đã được render thành công!" và nút "Render Lại" mà không phản ánh đúng trạng thái thực tế (Chưa render / Đang render / Đã render xong). Nút "Bắt đầu Ghép Video" to bản không có.
- **Không có Log thời gian thực (Real-time Log):** Backend đang gọi lệnh FFmpeg bằng hàm \subprocess.run\ (blocking). Điều này khiến giao diện web bị treo (loading spinner) trong suốt quá trình render, không thể thấy được tiến trình của FFmpeg (màn hình console đen chữ xanh) như thiết kế hệ thống yêu cầu.
- **Thiếu Trình phát Video (Video Player):** Sau khi ghép video xong, chưa có thẻ \<video>\ để người dùng phát và xem lại thành quả ngay trên nền tảng Web.

## 2. Yêu cầu Nâng cấp (Các Agent cần tham gia)

### 2.1. Nâng cấp Video Assembler Engine (media-coder)
- Cập nhật \modules/video_assembler/engine.py\: Thêm hàm \ender_video_stream(script_id, timeline)\.
- Hàm này không dùng \subprocess.run\ mà sử dụng \subprocess.Popen\ kết hợp với \yield\ để tạo thành một Generator. Hàm sẽ liên tục đọc từng dòng \stdout\ / \stderr\ của FFmpeg (kèm theo dòng \yield "[DONE]"\ ở cuối để báo hiệu hoàn tất).

### 2.2. Xây dựng Streaming API (web-coder)
- Sửa/Thay thế API \POST /api/phase5/render/{script_id}\ trong \pp.py\ thành API trả về luồng dữ liệu (Stream). Sử dụng \StreamingResponse\ của FastAPI (chuẩn Server-Sent Events, hoặc text stream). API này gọi Generator từ bước 2.1 để đẩy text liên tục xuống Frontend.
- Xây dựng API \GET /api/phase5/status/{script_id}\ để trả về đường dẫn video hiện tại (nếu file \inal_video_with_voice.mp4\ đã tồn tại sẵn trong thư mục).

### 2.3. Cải tiến UI/UX Màn hình 6 (web-coder)
Trong file \web/index.html\:
- Quản lý 3 trạng thái của Phase 5: \idle\ (chờ render), \endering\ (đang render), và \done\ (đã xong).
- **Trạng thái \idle\:** Hiển thị nút bấm to bản \[🎬 Bắt đầu Ghép Video]\.
- **Trạng thái \endering\:** 
  - Giao diện console (Terminal giả lập): Một khối \<div>\ nền đen, chữ xanh rêu (monospace), thanh cuộn auto-scroll xuống dưới cùng (dùng JavaScript đọc luồng \etch\ qua \getReader()\).
- **Trạng thái \done\:**
  - Hiển thị thông báo hoàn tất, giữ nguyên hoặc thu nhỏ khung log.
  - Hiển thị thẻ \<video controls class="w-full max-w-3xl mx-auto rounded shadow">\ để người dùng play trực tiếp file MP4 thông qua URL được mount qua folder \/data\. 

## 3. Luồng Triển khai Đề xuất

1. **Gọi agent \media-coder\:** Xử lý việc biến quá trình chạy FFmpeg thành một Generator (\yield\) theo thời gian thực thay vì block.
2. **Gọi agent \web-coder\:** Tạo StreamingResponse trong \pp.py\ và tích hợp logic giải mã Stream + UI Console log vào \web/index.html\.
3. **Kiểm tra (QA):** Khởi động Web, vào Màn hình 6, bấm "Bắt đầu Ghép Video", quan sát khung Log đen xem có hiển thị chữ chạy liên tục giống CMD không, và Video Player có hoạt động ngay sau khi xong không.
