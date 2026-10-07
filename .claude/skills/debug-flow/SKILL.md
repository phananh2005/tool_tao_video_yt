---
name: debug-flow
description: Chẩn đoán lỗi TubeChain có thể tái hiện hoặc test thất bại theo từng bước trước khi sửa code.
argument-hint: [failure-or-test]
---

# Quy trình debug: tái hiện, cô lập, chẩn đoán, sửa

1. **Tái hiện:** Ghi nhận lỗi, input, trạng thái và lệnh chính xác. Tạo hoặc tìm regression test tập trung. Dùng SQLite tạm và fixture; không gây rủi ro cho DB thật hoặc media người dùng.
2. **Cô lập:** Thu hẹp lỗi về route, contract, thao tác SQLite, module phase, frontend, provider adapter hoặc lệnh FFmpeg. Chạy test thất bại nhỏ nhất.
3. **Chẩn đoán:** Lần theo nơi gọi và dữ liệu; xác định nguyên nhân gốc bằng bằng chứng. Kiểm tra giá trị biên và khả năng tài liệu/schema lệch implementation.
4. **Sửa:** Thực hiện thay đổi nhỏ nhất xử lý nguyên nhân; thêm/sửa regression test. Áp dụng `tdd-playbook` khi phù hợp.
5. **Xác minh:** Chạy lại lỗi tái hiện, test module liên quan và test rộng hơn nếu cần. Báo đúng kết quả và phần còn chưa chắc chắn.
