# TubeChain - Hệ thống Sản xuất Video YouTube End-to-End bằng AI

## 1. Tầm nhìn & Mục tiêu

TubeChain là tool local giúp tự động hóa quy trình sản xuất video YouTube — từ brainstorm ý tưởng, viết kịch bản, tạo lời thoại, sinh hình ảnh, đến ghép video hoàn chỉnh sẵn sàng upload. Toàn bộ chạy trên máy cá nhân, có giao diện web local.

### Vấn đề giải quyết

- Ý tưởng bị trùng lặp hoặc lặp lại góc nhìn nhàm chán
- Các video rời rạc, không tận dụng được liên kết nội dung để tăng Watch Time
- Quy trình sản xuất video thủ công tốn quá nhiều thời gian và công sức
- Thiếu nhất quán về chất lượng nội dung giữa các video

**Mục tiêu:** Biến kho video cũ thành "tài sản", tự động sinh chuỗi video mới có tính liên kết chặt chẽ, đảm bảo 100% không trùng lặp ngữ nghĩa. Cung cấp pipeline để đưa ý tưởng từ brainstorm → video sẵn sàng upload lên YouTube.

## 2. Phạm vi chủ đề (Content Pillars)

Tối ưu cho kênh **Edutainment & Self-Improvement** với 6 trụ cột chủ đề:

1. Những điều thú vị, kỳ lạ, có thể bạn chưa biết
2. Tâm lý học hành vi
3. Quản lý tài chính cá nhân
4. Phát triển bản thân
5. Sức khỏe & Ăn uống
6. Bí ẩn thế giới & Sự thật về cơ thể người

## 3. Pipeline Sản xuất Video (Production Pipeline)

Toàn bộ quy trình được chia thành **6 giai đoạn** tuần tự:

```
[Phase 1] Brainstorm & Chống trùng lặp
    ↓
[Phase 2] Phát triển Kịch bản (Script)
    ↓
[Phase 3] Tạo Lời thoại (Voiceover Script)
    ↓
[Phase 4] Sinh Hình ảnh theo Khung cảnh
    ↓
[Phase 5] Ghép Video (Assembly)
    ↓
[Phase 6] Tối ưu SEO & Xuất bản
```

---

### Phase 1: Brainstorm & Chống trùng lặp (Idea Engine)

Module đảm bảo ý tưởng luôn mới mẻ và có liên kết nội dung.

#### 3.1. Ma trận Liên kết Chủ đề (Topic Cross-Pollination)

Ghép **1 chủ đề chính + 1 chủ đề phụ** để tạo góc nhìn độc nhất.

> VD: Tài chính cá nhân + Tâm lý học hành vi → *"Hiệu ứng Diderot: Tại sao mua 1 món đồ mới lại kích hoạt chuỗi mua sắm không kiểm soát?"*

#### 3.2. Bộ lọc Chống trùng lặp (Angle Deduplication Filter)

Sử dụng **Vector Embedding** so sánh ngữ nghĩa và góc tiếp cận:

| Độ tương đồng | Hành động |
|---|---|
| > 85% | Chặn ý tưởng, cảnh báo trùng lặp |
| 60-85% | Cảnh báo "Trùng chủ đề nhưng có thể đổi góc nhìn" |
| < 60% | Cho phép (Ý tưởng mới) |

#### 3.3. Trình tạo Chuỗi "Hố sâu thỏ" (Rabbit Hole Series Builder)

Tự động thiết kế chuỗi **3 video** dẫn dắt:

1. **Video 1** - Gây tò mò / Bí ẩn
2. **Video 2** - Giải thích Khoa học / Tâm lý
3. **Video 3** - Giải pháp Hành động

Đầu ra kèm script CTA mẫu để nối tiếp giữa các video.

#### 3.4. Auto-Playlist & Binge-Watch Engine

Đề xuất Playlist theo 3 mô hình:

- **The Rabbit Hole** - Theo lộ trình 3 bước chuỗi video
- **The Cross-Pollination Mix** - Gom video giao thoa chủ đề
- **The Level-Up Path** - Cơ bản → Nâng cao → Thực chiến

Đầu ra: Tên Playlist chuẩn SEO, mô tả, thứ tự sắp xếp.

#### 3.5. Bãi rác Ý tưởng (Idea Graveyard)

Lưu trữ vĩnh viễn các ý tưởng bị từ chối. AI không bao giờ gợi ý lại ý tưởng có ngữ nghĩa tương tự.

**Đầu ra Phase 1:** Ý tưởng video đã được duyệt (title, angle, chủ đề chính/phụ, mối liên kết với video cũ).

---

### Phase 2: Phát triển Kịch bản (Script Generator)

Từ ý tưởng đã duyệt, AI sinh **kịch bản video hoàn chỉnh**.

#### Cấu trúc kịch bản chuẩn

| Phần | Thời lượng | Mục đích |
|---|---|---|
| **Hook** | 0:00 - 0:15 | Câu mở đầu gây tò mò, giữ người xem |
| **Intro** | 0:15 - 0:45 | Giới thiệu vấn đề, đặt bối cảnh |
| **Body** (3-5 phần) | 0:45 - 7:00 | Nội dung chính, chia thành các segment rõ ràng |
| **Climax** | 7:00 - 8:00 | Điểm nhấn / Twist / Insight bất ngờ |
| **CTA + Outro** | 8:00 - 8:30 | Kêu gọi hành động, dẫn sang video tiếp theo trong chuỗi |

#### Tính năng

- AI tự động điều chỉnh **tone & style** phù hợp với chủ đề
- Tự động chèn **transition hooks** giữa các segment để giữ retention
- Gợi ý **B-roll keywords** cho mỗi đoạn (dùng ở Phase 4)
- Đánh dấu **key moments** để tạo YouTube Chapters

**Đầu ra Phase 2:** Kịch bản có cấu trúc (sections, timestamps dự kiến, B-roll keywords, chapter markers).

---

### Phase 3: Tạo Lời thoại (Voiceover Script)

Chuyển kịch bản thành **lời thoại tự nhiên** để người dùng tự thu âm hoặc dùng tool TTS bên ngoài.

#### Tính năng

- Chuyển đổi kịch bản dạng outline → **lời nói tự nhiên** (spoken language)
- Tối ưu **độ dài câu** cho giọng đọc (tránh câu quá dài gây mất tự nhiên)
- Hỗ trợ nhiều **persona/giọng kể**: narrator trung tính, storyteller hấp dẫn, expert chuyên gia
- Chèn **pronunciation guides** cho thuật ngữ chuyên ngành hoặc tên riêng

> **Lưu ý:** Tool không tự động tạo giọng đọc (TTS). Người dùng tự thu âm hoặc sử dụng tool/dịch vụ TTS bên ngoài, sau đó import file audio vào để ghép video.

**Đầu ra Phase 3:** Voiceover script text theo từng scene, sẵn sàng để thu âm.

---

### Phase 4: Sinh Hình ảnh theo Khung cảnh (Scene Illustration)

Tạo hình ảnh minh họa cho từng segment/khung cảnh trong video.

#### Quy trình

1. **Scene Breakdown:** Phân tích kịch bản → chia thành các khung cảnh (scenes), mỗi scene khoảng 10-30 giây
2. **Prompt Generation:** Từ nội dung + B-roll keywords → sinh prompt hình ảnh chi tiết
3. **Image Generation:** Dùng AI sinh ảnh (nguồn AI chưa xác định — có thể qua API hoặc copy/paste thủ công từ chat web, sẽ quyết định trong quá trình phát triển)
4. **Style Consistency:** Đảm bảo phong cách hình ảnh nhất quán xuyên suốt video

#### Loại hình ảnh hỗ trợ

- **Illustration:** Hình minh họa cho concept trừu tượng
- **Infographic:** Biểu đồ, sơ đồ cho dữ liệu / so sánh
- **Scene recreation:** Tái tạo khung cảnh mô tả trong kịch bản
- **Text overlay:** Ảnh nền + text highlight cho key points

**Đầu ra Phase 4:** Bộ ảnh PNG/JPG theo thứ tự scene, kèm metadata (scene_id, duration, caption).

---

### Phase 5: Ghép Video (Video Assembly)

Ghép các hình ảnh thành video đơn giản.

#### Quy trình

1. **Timeline Builder:** Sắp xếp ảnh theo thứ tự scene, đồng bộ với duration đã định
2. **Ghép ảnh:** Nối các ảnh tuần tự thành video, mỗi ảnh hiển thị trong khoảng thời gian tương ứng với scene
3. **Audio track (tùy chọn):** Nếu người dùng đã import file audio (thu âm), ghép audio vào video

> **Lưu ý:** Dựng video ở mức đơn giản — ghép ảnh tuần tự. Không có hiệu ứng chuyển cảnh phức tạp, Ken Burns, hay animation. Nếu cần hiệu ứng, người dùng chỉnh sửa thêm bằng phần mềm bên ngoài.

#### Công cụ

- **FFmpeg** — ghép ảnh + audio thành MP4
- Output: **1080p**, format MP4 (H.264)

**Đầu ra Phase 5:** File video MP4 cơ bản, sẵn sàng chỉnh sửa thêm hoặc upload trực tiếp.

---

### Phase 6: Tối ưu SEO & Chuẩn bị Xuất bản

Tự động sinh metadata tối ưu cho YouTube.

#### Đầu ra

- **Title:** 3-5 tiêu đề gợi ý, tối ưu CTR (có power words, số, dấu hỏi)
- **Description:** Mô tả chuẩn SEO với timestamps, links liên quan, hashtags
- **Tags:** 15-30 tags kết hợp broad + specific keywords
- **Thumbnail concept:** Mô tả layout thumbnail + text overlay gợi ý
- **YouTube Chapters:** Timestamps tự động từ chapter markers trong kịch bản
- **End Screen suggestions:** Gợi ý video liên kết (từ Phase 1 Rabbit Hole data)
- **Cards:** Thời điểm và video gợi ý chèn Card trong video

**Đầu ra Phase 6:** File metadata sẵn sàng dùng khi upload video.

## 4. Kiến trúc kỹ thuật

> **Nguyên tắc:** Đơn giản, nhẹ, chạy 100% local. Không deploy, không cloud services.

| Thành phần | Công nghệ | Ghi chú |
|---|---|---|
| Frontend | HTML/CSS/JS thuần hoặc framework nhẹ (Vue/Svelte) | Giao diện web local, đơn giản nhất có thể |
| Backend | Python (Flask hoặc FastAPI) | Xử lý logic pipeline, serve API cho frontend |
| Database | SQLite | File-based, không cần cài đặt, đủ cho tool local |
| Vector Search | Embedding lưu file JSON + cosine similarity | Cho bộ lọc chống trùng lặp |
| AI (Text) | **Chưa xác định** | Có thể qua API (OpenAI, Claude, Gemini) hoặc copy/paste từ chat web. Quyết định trong quá trình phát triển |
| AI (Image) | **Chưa xác định** | Tương tự — có thể qua API (Gemini, DALL-E) hoặc tải ảnh thủ công từ chat web |
| Video Assembly | FFmpeg | Ghép ảnh thành video đơn giản |
| Storage | Filesystem local | Lưu trực tiếp trên ổ cứng, tổ chức theo thư mục project |

### Database

- **SQLite:** Đủ cho tool chạy local. Lưu metadata (project, ideas, scripts, scenes, SEO), quan hệ giữa các video (Video_Links), idea graveyard.
- **Vector Embeddings:** Lưu dạng JSON file cạnh DB. Khi cần so sánh trùng lặp, load vào memory tính cosine similarity.

### Storage (Filesystem local)

```
/data
  /tubechain.db          ← SQLite database
  /embeddings.json       ← Vector embeddings cho dedup
  /projects
    /{project_id}
      /scripts           ← Kịch bản + lời thoại (text files)
      /images            ← Ảnh từng scene (PNG/JPG)
      /audio             ← File audio thu âm (nếu có, do user import)
      /video             ← Video output
      /metadata           ← SEO metadata
```

## 5. Luồng hoạt động tổng thể

```
[INPUT] Chủ đề thô từ người dùng
    │
    ▼
[PHASE 1] Idea Engine
    │  Context Retrieval → AI Generation → Dedup Check → Ideas Vault
    │  Output: Ý tưởng đã duyệt + liên kết nội dung
    ▼
[PHASE 2] Script Generator
    │  Ý tưởng → AI viết kịch bản → Cấu trúc hóa
    │  Output: Kịch bản có cấu trúc (hook, body, climax, CTA)
    ▼
[PHASE 3] Voiceover Writer
    │  Kịch bản → Chuyển thành lời nói tự nhiên
    │  Output: Voiceover script text (người dùng tự thu âm)
    ▼
[PHASE 4] Scene Illustrator
    │  Kịch bản + B-roll keywords → Image prompts → AI sinh ảnh (hoặc tải thủ công)
    │  Output: Bộ ảnh minh họa theo scene
    ▼
[PHASE 5] Video Assembler
    │  Ảnh + Audio (nếu có) → Ghép tuần tự → Render MP4
    │  Output: Video MP4 cơ bản
    ▼
[PHASE 6] SEO Optimizer
    │  Nội dung → Title, Description, Tags, Chapters, Thumbnail concept
    │  Output: Metadata sẵn sàng upload
    ▼
[OUTPUT] Video + Metadata sẵn sàng xuất bản lên YouTube
```

## 6. Trạng thái Pipeline (Project Status Flow)

Mỗi project (video) đi qua các trạng thái:

```
IDEA → SCRIPTING → VOICEOVER → ILLUSTRATING → ASSEMBLING → SEO → READY → PUBLISHED
```

Người dùng có thể:
- **Review & chỉnh sửa** output của mỗi phase trước khi chuyển sang phase tiếp theo
- **Quay lại** phase trước nếu cần sửa
- **Chạy tự động** toàn bộ pipeline (auto mode) hoặc **từng bước** (step mode)

## 7. Giao diện chính (UI Overview)

| Màn hình | Mô tả |
|---|---|
| **Dashboard** | Tổng quan projects, trạng thái pipeline |
| **Idea Board** | Brainstorm, mindmap liên kết, bộ lọc trùng lặp |
| **Script Editor** | Xem/sửa kịch bản, preview cấu trúc video |
| **Voiceover Script** | Xem/sửa lời thoại, copy text để thu âm |
| **Scene Gallery** | Xem/sửa/upload lại ảnh từng scene |
| **Video Preview** | Xem video đã ghép |
| **Publish Center** | SEO metadata, thumbnail concept |