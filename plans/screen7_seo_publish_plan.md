# Kế hoạch Hoàn thiện Màn hình 7: SEO & Publish (Phase 6)

## 1. Hiện trạng & Vấn đề tồn đọng
- **Lỗi Crash Backend:** Route API \POST /api/phase6/generate/{script_id}\ đang gọi sai hàm \engine.generate_metadata(script_dict)\. Lớp \SEOOptimizerEngine\ không hề chứa hàm này, thay vào đó là hàm \ormat_upload_info\.
- **Giao diện không đúng thiết kế:** Giao diện Screen 7 hiện tại chỉ là một danh sách các ô Text xếp dọc, hoàn toàn thiếu đi phần minh họa Thumbnail. Các Text Input đang bị đặt ở trạng thái \eadonly\ không cho người dùng sửa đổi trước khi copy.
- **Thiếu tiện ích \Copy All\:** Người dùng phải copy từng trường dữ liệu (Title, Description, Tags) để dán vào YouTube, rất mất thời gian.

## 2. Yêu cầu Nâng cấp (Các Agent cần tham gia)

### 2.1. Cập nhật API Phase 6 (web-coder)
- Chỉnh sửa file \pp.py\ phần API Phase 6:
  - Khởi tạo thêm kết nối Database để lấy \	itle\ (từ bảng \ideas\) và \sset_dict\ (từ bảng \ssets\).
  - Gọi hàm chuẩn: \seo_data, file_path = engine.format_upload_info(script_id, title, script_dict, asset_dict)\.
  - Lưu kết quả \seo_data\ (bao gồm cả trường \	humbnail_path\ được sinh tự động bởi engine) vào bảng \seos\ trong Database.

### 2.2. Tái cấu trúc Giao diện Màn hình 7 (web-coder)
Trong file \web/index.html\ cập nhật lại khối \<!-- PHASE 6: SEO & PUBLISH -->\:
- Sử dụng \grid grid-cols-1 md:grid-cols-2 gap-6\ để chia màn hình làm 2 cột:
  - **Cột trái (Thumbnail & Concept):**
    - Hiện ảnh Bìa (Thumbnail) do AI tự vẽ từ đường dẫn \seoData.thumbnail_path\ thông qua thẻ \<img>\. (Lưu ý đường dẫn tĩnh cần ánh xạ qua folder \/data\).
    - Bên dưới ảnh hiển thị text của trường \	humbnail_concept\ để gợi ý chữ nên chèn vào ảnh.
  - **Cột phải (Metadata Youtube):**
    - Các form Input / Textarea cho: **Title**, **Description**, **Timestamps** (\	imestamps_text\), và **Tags**.
    - **XÓA BỎ** thuộc tính \eadonly\ để người dùng có thể tự trau chuốt lại văn phong.
    - Một nút bự \[📋 Copy Tất Cả Dữ Liệu]\. Nút này sẽ kết hợp 4 trường văn bản thành một khối Text chuẩn format và lưu vào Clipboard (\
avigator.clipboard.writeText\).
- Thêm biến state để đánh dấu quá trình đang \loading\ khi tạo SEO & Thumbnail (Vì vẽ Thumbnail sẽ mất chút thời gian).

## 3. Luồng Triển khai Đề xuất

1. **Gọi agent \web-coder\:** Thực hiện trọn gói cả Backend lẫn Frontend. Sửa hàm gọi API trong \pp.py\ và cấu trúc lại HTML/JS của màn hình 7 trong \web/index.html\.
2. **Kiểm tra (QA):** Khởi chạy web, thử nhấn tạo SEO. Theo dõi Terminal của Backend xem AI có sinh được Timestamps (từ thông số Duration) và tự vẽ được Thumbnail hay không. Kiểm tra nút Copy xem paste ra Notepad có chuẩn xác không.
