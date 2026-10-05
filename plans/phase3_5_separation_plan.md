# Kế hoạch Tách Phase 3.5 (Voice Synthesis)

## 1. Yêu cầu (Scope)
- Tách biệt rõ ràng Phase 3 (Viết lời thoại Voiceover) và Phase 3.5 (Tổng hợp âm thanh).
- Phase 3.5 là bước **BẮT BUỘC** trước khi cho phép vào Phase 4 (Scene Illustrator).
- Nếu chưa có file âm thanh, hệ thống sẽ chặn không cho sinh hình ảnh (Phase 4).
- Giao diện (UI) cần có nút "Quay lại Phase trước" ở các màn hình để người dùng linh hoạt điều hướng nếu lỡ ấn nhầm hoặc muốn sửa.

## 2. Giao thức Dữ liệu (Data Contract & Schema)
### 2.1. Cập nhật Schema Database
- Cần bổ sung cột trạng thái vào bảng `voiceovers` để hệ thống biết âm thanh đã được sinh xong chưa.
- Lệnh: `ALTER TABLE voiceovers ADD COLUMN is_synthesized BOOLEAN DEFAULT 0;`

### 2.2. Trạng thái Dashboard (State Machine)
Câu query Dashboard sẽ đánh giá Phase như sau:
- 6: SEO (seo_metadata)
- 4: Assets (assets)
- 3.5: Voice Synthesis (voiceovers.is_synthesized = 1)
- 3: Voiceover Text (voiceovers)
- 2: Script (scripts)

## 3. Phân chia Task cho Agents

### 3.1. `db-architect`
- Viết script migration: Alter bảng `voiceovers` thêm cột `is_synthesized`.
- Cập nhật Data Contract: Xác định rõ khi gọi `/api/phase3_5/synthesize`, API phải set `is_synthesized = 1` sau khi tổng hợp xong.

### 3.2. `web-coder`
- **Backend (`app.py`)**:
  - Chỉnh sửa câu query trong `get_dashboard()` để hỗ trợ Phase 3.5.
  - Sửa logic chặn (Guard) ở `/api/phase4/generate`: Nếu `is_synthesized == 0`, trả về lỗi 400 (Phải tạo audio trước).
  - API Sinh âm thanh cập nhật database để gán `is_synthesized = True`.
- **Frontend (`web/index.html`)**:
  - Tách UI hiện tại của Phase 3 thành 2 bước rõ ràng hoặc disable nút "Vẽ Hình Ảnh" nếu chưa tạo audio.
  - Thêm nút "Quay lại Phase 3" ở Phase 4, "Quay lại Phase 4" ở Phase 5 để điều hướng ngược.

### 3.3. `qa-test-engineer`
- Chạy golden test để xác nhận bấm "Vẽ hình ảnh" khi chưa có âm thanh sẽ bị chặn (UI disable + API return 400).
- Xác nhận nút Quay lại hoạt động trơn tru.
