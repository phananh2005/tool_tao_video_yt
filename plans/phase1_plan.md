# Kế hoạch triển khai Phase 1: Idea Engine & Gemini Web Adapter

## 1. Tổng quan
- **Mục tiêu:** Xây dựng Phase 1 (Idea Engine) kết hợp Web Automation (MODE_WEB_AUTO qua Playwright gọi Gemini).
- **Ràng buộc:** Tuân thủ AGENTS.md (Local 100%, Rabbit Hole 3 video, Dedup filter 60%/85%).

## 2. Nhiệm vụ các Agent

### 2.1 db-architect (Bước 1)
- **Nhiệm vụ:** Thiết kế data schema và AI Provider Contract.
- **Đầu ra:**
  - Schema SQLite cho projects, ideas.
  - Contract IdeaJSON định dạng chuẩn.
  - Base Contract cho AIProvider (hỗ trợ mode gemini_web_auto).

### 2.2 idea-engine-coder (Bước 2)
- **Nhiệm vụ:** Implement core logic tại modules/idea_engine/.
- **Đầu ra:**
  - GeminiWebAdapter dùng thư viện playwright giao tiếp web Gemini.
  - Logic lọc trùng lặp (Dedup) bằng cosine similarity (>85% drop, 60-85% warn, <60% pass).
  - Logic tạo chuỗi Rabbit Hole (đúng 3 video, không hơn).

### 2.3 qa-test-engineer (Bước 3)
- **Nhiệm vụ:** Viết test đảm bảo chất lượng tại 	ests/.
- **Đầu ra:**
  - Unit test cho các ngưỡng Dedup.
  - Unit test xác nhận Rabbit Hole luôn <= 3 video.
  - Mock test cho Web Adapter (tránh việc pop-up Chrome khi chạy CI).
