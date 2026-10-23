# Bản đồ thích ứng — Tín hiệu dự án & Điều chỉnh hạ tầng AI Agent

Tài liệu này hướng dẫn cách điều chỉnh hạ tầng agent (`CLAUDE.md`, agents, skills, hooks) khi dự án TubeChain phát triển hoặc thay đổi. Được sử dụng bởi skill `workflow-adapt` khi phát hiện sự lệch pha giữa hạ tầng agent và mã nguồn thực tế.

## 1. Nguyên tắc thích ứng
1. **Bằng chứng trước, quy tắc sau:** Mọi đề xuất điều chỉnh phải có bằng chứng từ mã nguồn, log lỗi hoặc yêu cầu lặp lại của người dùng.
2. **Không nới lỏng guardrail cốt lõi:** Có thể điều chỉnh quy trình, thêm/bớt agent hoặc skill, nhưng **tuyệt đối không bỏ**:
   - Cổng kiểm thử: Không báo Done nếu test chưa chạy hoặc chưa PASS.
   - Ranh giới an toàn: Không xóa database `data/tubechain.db`, không xóa media người dùng, không force push.
   - Nguyên tắc trung thực: Chưa xác định được thì ghi `[cần xác nhận]`, không đoán mò.
3. **Mọi điều chỉnh phải có dấu vết:** Ghi nhận vào `.agent-bootstrap/project-profile.md` (mục 12) và `.claude/state/decisions-log.md`.

## 2. Bảng tín hiệu & Hướng điều chỉnh cho TubeChain

### 2.1 Hình dạng & Kiến trúc mã nguồn
| Tín hiệu phát hiện | Bằng chứng | Điều chỉnh tương ứng |
|---|---|---|
| Mã nguồn giữ nguyên 1 tầng Python | `app.py`, `core/`, `modules/` | Giữ định danh agent không hậu tố (`developer`, `architect`, `qa-reviewer`). |
| Thêm frontend framework riêng (React/Vue) | Thư mục `frontend/`, có `package.json` | Tách quy trình thành `developer-frontend` / `developer-backend`; phân định ranh giới API contract. |
| Thêm database khác hoặc thay SQLite | Dependency mới trong manifest | Cập nhật lại `docs/agent/knowledge/non-functional-standards.md` phù hợp cơ chế của DB mới. |

### 2.2 Kiểm thử & Chất lượng
| Tín hiệu phát hiện | Bằng chứng | Điều chỉnh tương ứng |
|---|---|---|
| Lệnh test thay đổi | Thêm cấu hình pytest mới hoặc script test riêng | Cập nhật `project-profile.md` và lệnh test trong `CLAUDE.md`, `tdd-playbook`. |
| Bổ sung linter / format (flake8, black, ruff) | File cấu hình `pyproject.toml`, `.ruff.toml` | Thêm bước kiểm tra lint vào cổng "Sau sửa" và skill `code-review`. |
| Có CI tự động (GitHub Actions) | Xuất hiện thư mục `.github/workflows/` | Đối chiếu test trên local với luồng CI; không tạo hook trùng lặp bước CI đã bảo vệ. |

### 2.3 Quy trình & Điều hành
| Tín hiệu phát hiện | Bằng chứng | Điều chỉnh tương ứng |
|---|---|---|
| Người dùng sửa cùng một hành vi ≥ 2 lần | Câu lệnh nhắc nhở của người dùng | Kích hoạt skill `workflow-adapt` để ghi nhận quy ước vào `CLAUDE.md` hoặc agent instructions. |
| Hook chặn nhầm thao tác hợp lệ | Hook stderr chặn lệnh an toàn | Cập nhật regex hoặc logic trong `.claude/hooks/pre-tool-use.py` sau khi viết test kiểm chứng. |
| Thành phần pipeline mới được thêm vào | Thêm phase mới ngoài 6 phase hiện tại | Thêm engine vào `modules/`, cập nhật contract trong `core/contracts.py`, cập nhật `CLAUDE.md`. |

## 3. Vòng lặp tự điều chỉnh sau bootstrap

```text
Phát hiện lệch ──► Thu thập bằng chứng ──► Đề xuất điều chỉnh ──► Người dùng duyệt ──► Cập nhật cấu hình ──► Ghi nhận dấu vết
```

Mỗi lần điều chỉnh phải là một thay đổi nhỏ, độc lập, có thể khôi phục (rollback) dễ dàng nếu cần.
