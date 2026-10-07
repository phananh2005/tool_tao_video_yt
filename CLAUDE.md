# TubeChain — Hướng dẫn dự án cho Claude Code

## Tổng quan dự án
TubeChain là công cụ sản xuất video YouTube theo hướng ưu tiên chạy tại máy người dùng. Mã nguồn hiện dùng Python + FastAPI (`app.py`), SQLite (`core/database.py`), giao diện tĩnh trong `web/`, các module pipeline trong `modules/` và kiểm thử pytest trong `tests/`. FFmpeg dùng để ghép video cơ bản. Trước khi giả định dependency hay lệnh chạy, hãy xác minh từ file trong repo; không tự bịa hướng dẫn cài đặt.

Pipeline sản phẩm gồm:
1. **Idea Engine** — lên ý tưởng, loại trùng lặp, lập chuỗi Rabbit Hole.
2. **Script Generator** — tạo kịch bản có cấu trúc và thời lượng.
3. **Voiceover Writer** — chỉ tạo lời thoại dạng văn bản.
4. **Scene Illustrator** — chia cảnh, tạo prompt/ảnh minh họa.
5. **Video Assembler** — ghép ảnh tĩnh tuần tự, đơn giản.
6. **SEO Optimizer** — tạo tiêu đề, mô tả, thẻ, chương và ý tưởng thumbnail.

Mã nguồn hiện cũng có luồng tổng hợp giọng nói **Phase 3.5 cũ**. Hãy phân biệt luồng này với việc tạo văn bản lời thoại ở Phase 3; không tự ý xóa hoặc mở rộng hành vi nào trong hai phần.

## Ràng buộc sản phẩm bắt buộc
- Giữ ứng dụng chạy tại máy: giao diện/API cục bộ và SQLite; không tự thêm cloud DB, triển khai từ xa hoặc lưu trữ từ xa.
- Dữ liệu lịch sử video chỉ gồm văn bản/metadata/chủ đề/embeddings; không giữ media video cũ làm dữ liệu lịch sử.
- Mỗi chuỗi Rabbit Hole tối đa **3 video**.
- Ngưỡng dedup: độ tương đồng `> 0.85` thì chặn; `0.60–0.85` thì cảnh báo; `< 0.60` thì cho qua. Dùng lại cấu hình/logic hiện có, không tạo nguồn ngưỡng trùng lặp.
- Phase 3 tạo văn bản lời thoại, không phải tính năng TTS. Xem phần Phase 3.5 hiện có như giai đoạn cũ riêng biệt.
- Dựng video: cho phép thêm hiệu ứng chuyển cảnh (transitions) giữa các ảnh tĩnh để video sinh động hơn, cùng với đầu vào audio hiện có; không thêm Ken Burns, animation phức tạp hoặc nhạc nền trừ khi có yêu cầu rõ ràng.
- Mọi thao tác AI phải đi qua provider adapter hiện có. Không khẳng định có chế độ API/thủ công nếu chưa xác minh trong mã; tuyệt đối không ghi cứng thông tin xác thực.
- Subagent chỉ hỗ trợ phát triển mã; không phải tác nhân chạy trong pipeline tạo video lúc sử dụng ứng dụng.

## Định tuyến và bàn giao
Chỉ dùng subagent khi chúng tạo giá trị; không ép mọi thay đổi nhỏ đi qua nhiều agent.

| Agent | Bí danh model | Trách nhiệm |
|---|---|---|
| `youtube-strategist` | `opus` | Chiến lược khán giả/nội dung YouTube: ý tưởng, góc tiếp cận, hook, duy trì người xem, chuỗi, tiêu đề, thumbnail và SEO. Đưa ra yêu cầu nội dung cùng tiêu chí đánh giá; không thiết kế contract kỹ thuật hoặc viết code. |
| `prompt-engineer` | `sonnet` | Thiết kế/đánh giá prompt template và cách kiểm thử đầu ra theo adapter hiện có. Không gọi provider trực tiếp hoặc tự ý đổi contract dùng chung. |
| `architect` | `opus` | Thiết kế/yêu cầu không tầm thường, data contract dùng chung, schema/migration SQLite, quyết định liên phase và tiêu chí nghiệm thu. Không implement mã ứng dụng. |
| `developer` | `sonnet` | Thực thi yêu cầu rõ ràng hoặc thiết kế đã thống nhất, tái sử dụng code, làm TDD cho thay đổi hành vi và chạy kiểm tra liên quan. |
| `qa-reviewer` | `opus` | Review độc lập diff, ràng buộc, bảo mật, regression và kiểm thử; thường báo lỗi thay vì sửa code sản phẩm. |

Trong runtime của người dùng, alias `opus` ánh xạ tới Gemini 3.1 Pro và `sonnet` ánh xạ tới Gemini 3.8 Flash. Giữ alias này trong frontmatter; không thay bằng model ID của provider tự suy đoán.

Định tuyến theo loại việc:
- **Tính năng nội dung/sản phẩm có AI sinh:** `youtube-strategist` xác định mục tiêu nội dung và tiêu chí → `architect` chuyển thành thiết kế/contract kỹ thuật → `prompt-engineer` soạn hoặc đánh giá prompt theo contract đã duyệt → `developer` implement → `qa-reviewer` kiểm tra độc lập.
- **Chỉ đổi prompt, contract đầu ra không đổi:** `prompt-engineer` → `developer` (kèm test) → `qa-reviewer` nếu mức rủi ro cần review.
- **Thay đổi kỹ thuật/schema/liên phase:** `architect` (nếu thiết kế không tầm thường) → `developer` → `qa-reviewer`.
- **Sửa nhỏ, phạm vi hẹp:** `developer` có thể làm trực tiếp với test tập trung; chỉ gọi thêm agent khi có ích.

`youtube-strategist` phụ trách chiến lược nội dung, không quyết định kiến trúc kỹ thuật. `prompt-engineer` phụ trách prompt/đánh giá prompt, không quyết định contract DB/API. Mọi đổi contract dùng chung phải được chuyển lại `architect` trước khi implement. Hai agent nội dung chỉ hỗ trợ lúc phát triển, không tham gia runtime tạo video.

## Quy trình kỹ thuật
1. Đọc source, nơi gọi, test và thiết kế liên quan; xác minh hành vi thật trước khi sửa.
2. Dùng skill `reuse-scan` trước khi tạo helper, route, schema, component hoặc hành vi lặp lại.
3. Với thay đổi hành vi và sửa lỗi, làm theo `tdd-playbook`: Red (chạy test thất bại liên quan nếu khả thi) → Green → Refactor → xác minh. Không được nói đã chạy test nếu chưa chạy.
4. Dùng `debug-flow` cho lỗi có thể tái hiện. Dùng `task-state-init` và `progress-tracker` cho việc lớn cần theo dõi, không dùng cho sửa vặt.
5. Chạy test liên quan hẹp trước, sau đó mở rộng theo phạm vi ảnh hưởng. Báo chính xác lệnh, kết quả và các kiểm tra chưa chạy.
6. Review diff để tránh mở rộng phạm vi, lệch contract, xóa nhầm data/media, lộ thông tin xác thực hoặc thay đổi không liên quan.

## An toàn và xử lý dữ liệu
- Không xóa hoặc khởi tạo lại `data/tubechain.db` hay media người dùng để làm test pass.
- Dùng DB/media fixture tạm cho test. Chỉ thao tác phá hủy trong đúng phạm vi người dùng yêu cầu và sau khi kiểm tra target.
- Không commit, force-push, triển khai hoặc publish nếu người dùng chưa yêu cầu rõ.
- Hook trong `.claude/settings.json` chỉ là lớp phòng vệ bổ sung có phạm vi hẹp. PreToolUse chặn một số lệnh phá hủy rõ ràng, không thay thế parser shell đầy đủ hay sandbox. PostToolUse TDD chỉ nhắc sau thao tác, không thể hoàn tác hoặc chặn edit đã xong.
- Không sửa `.claude/settings.local.json` hoặc cấu hình Claude Code cấp người dùng/toàn cục nếu chưa được yêu cầu rõ.

## File của framework
- Subagent riêng dự án: `.claude/agents/`
- Skill có thể nạp: `.claude/skills/<skill-name>/SKILL.md`
- Cấu hình và script hook: `.claude/settings.json`, `.claude/hooks/`
- Template state có thể dùng lại: `.claude/state/_template/`
- Tổng quan sản phẩm: `README.md`; mô tả sản phẩm/luồng cũ chi tiết: `system-description.md` (đối chiếu với implementation).
- Bản đồ harness và luồng công việc: [`docs/agent/README.md`](docs/agent/README.md), [`docs/agent/workflows.md`](docs/agent/workflows.md).
