# Quy trình phát triển AI — TubeChain

Dùng tài liệu này cùng ràng buộc dự án trong [`CLAUDE.md`](../../CLAUDE.md) và bằng chứng repository trong [`README.md`](README.md). Đây là quy trình hỗ trợ phát triển; subagent không tham gia runtime tạo video.

## Vai trò và ranh giới agent

| Vai trò | Khi phù hợp | Ranh giới / bàn giao |
|---|---|---|
| `youtube-strategist` | Mục tiêu khán giả/nội dung, tạo khác biệt cho ý tưởng, hook, giữ chân, thứ tự chuỗi và yêu cầu đóng gói YouTube. | Đưa ra tư vấn biên tập và tiêu chí nghiệm thu; không định nghĩa schema kỹ thuật hoặc hứa hẹn kết quả thuật toán. |
| `prompt-engineer` | Prompt template, cách tạo prompt và test/eval xác định cho nội dung sinh tự động. | Kiểm tra engine, adapter, parser và contract hiện có. Không gọi provider thật hoặc âm thầm đổi contract. |
| `architect` | Thiết kế kỹ thuật không tầm thường, contract API/data, schema/migration SQLite và thay đổi liên phase. | Báo hành vi đã xác minh, rủi ro, tiêu chí nghiệm thu; bàn giao thiết kế để implement. Bỏ qua với sửa nhỏ, cục bộ. |
| `developer` | Implement Python/FastAPI, SQLite, frontend, module pipeline và FFmpeg. | Dùng lại code, test thay đổi hành vi, chạy kiểm tra tập trung, báo kết quả thật. |
| `qa-reviewer` | Review diff độc lập về tính đúng, bảo mật, ràng buộc, hồi quy và chất lượng test. | Báo bằng chứng có thể hành động; thông thường không tự sửa code sản phẩm. |

Các agent khai báo `model: opus` hoặc `model: sonnet`. Hub dự án ghi runtime người dùng ánh xạ `opus` → Gemini 3.1 Pro và `sonnet` → Gemini 3.8 Flash; không thay alias bằng provider ID tự suy đoán.

## Định tuyến theo loại việc

### Khảo sát / hiểu repository

1. Dùng tìm kiếm chỉ-đọc, đọc source, nơi gọi và test gần nhất.
2. Ghi bằng chứng `path:line`; phân biệt hành vi quan sát được, nội dung tài liệu, suy luận và điều chưa biết.
3. Không đọc local settings, secret, browser profile, database, media người dùng hoặc log không liên quan.
4. Nếu người dùng yêu cầu deliverable nghiên cứu, tóm tắt phát hiện, khoảng trống, độ tin cậy và bước an toàn tiếp theo trước khi đề nghị sửa.

### Thiết kế nội dung/sản phẩm

Với tính năng tác động tới ý tưởng, kịch bản, lời thoại, cảnh, thumbnail, SEO hoặc metadata xuất bản:

1. `youtube-strategist` xác định mục tiêu creator/khán giả và tiêu chí biên tập có thể đánh giá.
2. Nếu ranh giới phase hoặc dữ liệu lưu/API bị ảnh hưởng, `architect` chuyển yêu cầu nội dung thành phạm vi kỹ thuật/contract.
3. `prompt-engineer` đề xuất thay đổi prompt theo parser/shape đầu ra hiện tại và test mẫu xác định bằng mock.
4. `developer` chỉ implement khi contract đã rõ; `qa-reviewer` kiểm tra độc lập diff và test.

Nếu chỉ đổi prompt, contract ổn định, có thể bỏ qua `architect` trừ khi kiểm tra code phát hiện đổi schema/contract. Tư vấn nội dung không chứng minh sẽ có view, CTR, retention hay thứ hạng. Với nội dung cần xác minh, yêu cầu kiểm chứng và duyệt của con người.

### Thiết kế kỹ thuật / implement

- **Thay đổi nhỏ, cô lập:** `developer` có thể xử lý trực tiếp với test tập trung.
- **Tính năng mới trong một module:** developer kiểm tra module/test, chạy `reuse-scan`, tuân contract cục bộ.
- **Thay đổi liên phase, API, contract, schema hoặc migration:** gọi `architect` trước; developer implement theo thiết kế đã duyệt; QA review.
- **Chỉ frontend:** kiểm tra asset tĩnh trong `web/`, route/response API ở `app.py` và `tests/test_frontend_static.py` khi phù hợp.
- **Persistence:** kiểm tra `core/database.py`, `core/contracts.py`, `tests/test_contracts_db.py`. Dùng DB test cô lập; không reset `data/tubechain.db`.
- **Media/FFmpeg:** kiểm tra `modules/video_assembler/` hoặc `modules/scene_illustrator/`, dùng fixture tạm. Không ghi đè hoặc xóa media người dùng.

### Debug

Dùng skill `debug-flow`:

1. Tái hiện bằng test tập trung hoặc fixture an toàn.
2. Cô lập route/module/ranh giới dữ liệu.
3. Chẩn đoán bằng code và bằng chứng, không đoán mò.
4. Sửa nhỏ nhất xử lý nguyên nhân gốc và thêm regression coverage.
5. Chạy lại test tái hiện cùng kiểm tra rộng phù hợp; báo lỗi và phần chưa rõ.

Không chạy migration database hoặc dọn dữ liệu phá hủy để tái hiện bug.

### Test và quality review

- Thay đổi hành vi: theo `tdd-playbook` (Red → Green → Refactor); không nói đã thấy Red nếu chưa chạy test thất bại.
- Lệnh test đã được ghi trong README: `python -m pytest`. Chưa xác nhận lệnh lint/type-check/build toàn repo.
- Chạy test liên quan hẹp nhất trước; mở rộng suite theo mức ảnh hưởng. Báo lệnh, kết quả, test bỏ qua và lý do.
- `qa-reviewer` kiểm tra code đổi, caller/contract trực tiếp và test; rà SQL parameterization, phạm vi path/xóa, secret, ràng buộc phase, tài nguyên/subprocess và trùng lặp không cần thiết.
- Hook nhắc nhở không chứng minh TDD đã được làm; test cũng không thay thế diff review.

### Tài liệu

- Nội dung thực tế phải khớp source. `system-description.md` có thông tin tổng quan rộng hơn và một phần aspirational/legacy; đối chiếu với code.
- Với docs-only, kiểm tra link và path được nhắc tới; không bịa dependency/lệnh cài khi không có manifest.
- Tách tài liệu phát triển harness khỏi hướng dẫn người dùng chạy TubeChain.

### DevOps / CI / release

Inventory repo đã xem không có cấu hình CI hoặc manifest dependency ở root. Không tự bịa pipeline hoặc thêm CI. Mọi yêu cầu thêm CI, đổi quyền, cài dependency, sửa runtime/production settings, deploy, release, commit, tag hoặc push cần phạm vi/phê duyệt rõ. Bắt đầu chỉ-đọc và nêu side effect dự kiến trước khi thao tác.

## Khi nào cần hỏi lại hoặc xin duyệt

**Hỏi người dùng trước** nếu lựa chọn chưa rõ có thể làm đổi đáng kể phạm vi, hành vi người dùng, dữ liệu lâu dài/schema, tương thích API, bảo mật/quyền riêng tư, chi phí/gửi dữ liệu ra ngoài, quyền truy cập hoặc gây hành động khó đảo ngược. Cũng hỏi trước khi sửa hướng dẫn gốc, settings/hooks/CI đang chạy hoặc cấu hình local/người dùng nếu chưa được cho phép đúng thay đổi đó.

**Tự chọn giả định an toàn** khi chi tiết thiếu ít ảnh hưởng, dễ đảo ngược và tương thích hành vi hiện có. Ghi giả định trong handoff/báo cáo; không hỏi câu mà câu trả lời không làm thay đổi cách xử lý.

Ví dụ:
- Hỏi: yêu cầu mơ hồ có thể dẫn tới xóa record đã lưu hoặc đổi shape đầu ra phase.
- Hỏi: chọn AI provider chạy thật, gửi dữ liệu repo ra ngoài hoặc tiêu API credit.
- Hỏi: sửa `.claude/settings.json`, `CLAUDE.md`, permission, hook hoặc CI ngoài kế hoạch đã duyệt.
- Tự giả định và ghi rõ: dùng style UI hiện có cho control nhỏ, không phá tương thích, nếu có một tiền lệ rõ ràng.

## State, handoff và hoàn tất

Dùng `.claude/skills/task-state-init` và `.claude/skills/progress-tracker` cho task lớn/nhiều bước; bỏ qua state file với sửa nhỏ. Không ghi đè lịch sử task trước khi kiểm tra.

Handoff nên có:

- Mục tiêu người dùng, phạm vi đã thống nhất và phần ngoài phạm vi.
- Quyết định, giả định, đường dẫn thiết kế/contract liên quan.
- File/module đã sửa hoặc dự kiến sửa.
- Test/kiểm tra đã chạy cùng kết quả chính xác; phần bỏ qua và lý do.
- Rủi ro, câu hỏi chưa giải quyết, blocker và người/bước tiếp theo.

Trước khi báo hoàn tất, xem diff/status để kiểm soát phạm vi, giữ nguyên thay đổi có sẵn, xác minh tiêu chí nghiệm thu và nêu rõ kiểm tra chưa chạy. Không commit/push/deploy nếu chưa được yêu cầu.

## Giới hạn hook hiện tại (ghi nhận, không đổi cấu hình)

- `.claude/settings.json` hiện chỉ đăng ký safety hook PreToolUse cho `Bash`. Không khẳng định hook bảo vệ PowerShell hoặc mọi shell.
- Pre-tool hook nhận diện một số chuỗi lệnh phá hủy cụ thể; không phải parser shell đầy đủ hay sandbox. Chaining lệnh, alias, script, shell khác và biến thể path có thể né kiểm tra chuỗi.
- Hook TDD PostToolUse chỉ nhắc sau `Write|Edit`; không thể ngăn hoặc hoàn tác edit đã hoàn tất.
- Hook script dùng đường dẫn tương đối theo cấu hình hiện tại; cần xác minh khi chạy trong worktree/CWD khác.
- Đây chỉ là ghi chú cho lần review sau; workflow này không thay đổi hooks, settings hoặc quyền.
