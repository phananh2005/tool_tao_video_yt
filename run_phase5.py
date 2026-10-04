import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.database import init_db, get_ready_to_render_projects
from modules.video_assembler.engine import VideoAssemblerEngine

def main():
    init_db()
    
    engine = VideoAssemblerEngine()
    
    # 1. Kiểm tra môi trường
    if not engine.check_ffmpeg():
        print("\n" + "!"*60)
        print("LỖI NGHIÊM TRỌNG: KHÔNG TÌM THẤY FFMPEG")
        print("Hệ thống yêu cầu phải cài đặt phần mềm FFmpeg để ghép video.")
        print("Vui lòng tải FFmpeg, giải nén và thêm vào biến môi trường (PATH) của Windows.")
        print("!"*60 + "\n")
        return

    # 2. Lấy dữ liệu
    projects = get_ready_to_render_projects()
    
    if not projects:
        print("\n=> Không có dự án nào đủ điều kiện Render (Cần phải tải xong Hình ảnh ở Phase 4 trước).")
        return
        
    print("\n=== DANH SÁCH DỰ ÁN ĐÃ SẴN SÀNG RENDER VIDEO ===")
    for p in projects:
        total_time = sum([item['duration'] for item in p['timeline']])
        mins, secs = divmod(total_time, 60)
        print(f"[{p['script_id']}] - Tên: {p['title']}")
        print(f"      Tổng số ảnh: {len(p['timeline'])} | Thời lượng: {mins} phút {secs} giây")
        
    choice = input("\nNhập số ID của Dự án muốn Render (hoặc Enter để thoát): ").strip()
    if not choice.isdigit():
        return
        
    script_id = int(choice)
    target_project = next((p for p in projects if p['script_id'] == script_id), None)
    
    if not target_project:
        print("=> Lỗi: ID không hợp lệ.")
        return
        
    print(f"\n=> Bắt đầu quá trình Ghép Video cho: '{target_project['title']}'")
    
    # 3. Tiến hành Render
    success = engine.render_video(script_id, target_project['timeline'])
    
    if success:
        print("\n" + "="*50)
        print("🎉 HOÀN TẤT QUÁ TRÌNH SẢN XUẤT VIDEO 🎉")
        print("="*50)
        print("Bước tiếp theo dành cho bạn:")
        print("1. Mở file final_video.mp4 lên để xem lại nhịp độ ảnh.")
        print("2. Sử dụng file kịch bản lời thoại (đã tạo ở Phase 3).")
        print("3. Bỏ video vào phần mềm dựng (Capcut/Premiere), tự thu âm giọng đọc và căn chỉnh khớp với ảnh.")
        print("Chúc bạn có một video Youtube triệu view!")

if __name__ == '__main__':
    main()
