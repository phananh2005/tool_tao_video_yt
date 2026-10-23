# Kế hoạch Đánh giá Phương án Tăng Chất lượng Video Output

## Mục tiêu
Tối ưu hóa chất lượng video xuất ra từ FFmpeg ở Phase 5 (Video Assembler) để giữ được độ sắc nét tối đa từ ảnh gốc (Gemini), đồng thời phù hợp với nền tảng YouTube.

## Các Phương án Kỹ thuật

### Phương án 1: Tối ưu bộ mã hóa H.264 (Đang áp dụng một phần)
* **Thông số**: `-c:v libx264 -crf 16 -preset veryslow -tune stillimage`
* **Mô tả**: 
  - Hạ CRF xuống 16-18 (Visually Lossless).
  - Đẩy preset lên `veryslow` để nén hiệu quả nhất không mất chất lượng.
  - `-tune stillimage` tối ưu cho các cảnh ít chuyển động.
* **Đánh giá**:
  - **Ưu điểm**: Tương thích 100% với mọi thiết bị, sửa lỗi mờ nhòe rất tốt.
  - **Nhược điểm**: Thời gian render tăng nhẹ so với mặc định.
  - **Hành động**: Đã áp dụng `-crf 18` và `preset slow`. Có thể đẩy lên `veryslow` và `crf 16` nếu cần nét căng hơn nữa.

### Phương án 2: Đổi thuật toán Scale ảnh (Resampling)
* **Thông số**: Trong `-vf`, sử dụng `scale=...:flags=spline` hoặc `flags=lanczos`
* **Mô tả**: Khi ảnh từ Gemini không đúng tỷ lệ 16:9, FFmpeg phải scale/pad. Thuật toán `bicubic` mặc định gây mờ.
* **Đánh giá**:
  - **Ưu điểm**: Cải thiện rõ rệt viền (edges) và chi tiết nhỏ khi ảnh bị phóng to/thu nhỏ.
  - **Nhược điểm**: Không có.
  - **Hành động**: Đã áp dụng `lanczos`. Có thể thử nghiệm nghiệm thêm `spline` hoặc thêm unsharp mask `unsharp=5:5:0.5:5:5:0.0` để làm nét giả (sharpen).

### Phương án 3: Upscale video lên 4K (3840x2160)
* **Thông số**: Đổi `-vf` sang `scale=3840:2160...`
* **Mô tả**: Dù ảnh gốc có thể chỉ ở mức 1080p hoặc tương đương, việc render và up video lên YouTube ở chuẩn 1440p hoặc 4K ép YouTube sử dụng codec VP9 (chất lượng cao hơn hẳn mã hóa AVC/H264 mặc định cho kênh nhỏ).
* **Đánh giá**:
  - **Ưu điểm**: Mẹo SEO/Quality cực mạnh. Video tải lên YouTube nét hơn hẳn do được hưởng bitrate cao của YouTube.
  - **Nhược điểm**: Kích thước file lớn gấp 3-4 lần, render lâu hơn.
  - **Hành động**: Cần cân nhắc vì ảnh gốc Gemini trả về kích thước bao nhiêu? Nếu ảnh gốc nhỏ, việc upscale kết hợp `lanczos` vẫn có lợi trên YouTube.

### Phương án 4: Nâng cấp định dạng màu (Color Space)
* **Thông số**: Đổi `-pix_fmt yuv420p` thành `-pix_fmt yuv444p` hoặc `-colorspace bt709`
* **Mô tả**: Giữ lại nhiều thông tin màu sắc hơn. YouTube hỗ trợ nhận yuv444p nhưng sau đó vẫn nén lại, nhưng đầu vào tốt thì đầu ra sẽ tốt hơn. Đặt dải màu sắc nét BT.709.
* **Đánh giá**:
  - **Ưu điểm**: Màu rực rỡ hơn, bớt bệt màu ở các vùng chuyển sắc.
  - **Nhược điểm**: Một số trình phát video local (đời cũ) có thể không xem được yuv444p.
  - **Hành động**: Nên giữ `yuv420p` kết hợp khai báo profile màu: `-color_primaries bt709 -color_trc bt709 -colorspace bt709`.

### Phương án 5: Đổi Codec sang HEVC (H.265) hoặc VP9
* **Thông số**: `-c:v libx265 -crf 20` hoặc `-c:v libvpx-vp9 -crf 20 -b:v 0`
* **Mô tả**: Dùng chuẩn nén thế hệ mới.
* **Đánh giá**:
  - **Ưu điểm**: Cùng mức chất lượng nhưng dung lượng cực nhẹ, hoặc cùng dung lượng nhưng cực nét.
  - **Nhược điểm**: Thời gian render của H.265 và VP9 rất lâu so với H.264 (nếu không có GPU support như NVENC).
  - **Hành động**: Với Tool local không đòi hỏi lưu trữ gắt gao, x264 với CRF thấp vẫn tối ưu thời gian hơn. Không ưu tiên trừ khi file quá nặng.

## Kế hoạch hành động đề xuất (Tiếp theo)

1. **Bước 1**: Áp dụng thêm filter Sharpen nhẹ và chuẩn hóa màu sắc vào command FFmpeg để khắc phục hoàn toàn cảm giác "mờ".
2. **Bước 2**: Đánh giá tính khả thi của **Upscale 4K**. (Nếu người dùng muốn trải nghiệm chất lượng YouTube tối đa).
3. **Bước 3**: (Tuỳ chọn) Nếu máy cấu hình mạnh, đổi preset sang `veryslow` và `crf 16`.
