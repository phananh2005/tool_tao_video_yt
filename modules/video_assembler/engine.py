import os
import subprocess
import shutil

class VideoAssemblerEngine:
    def __init__(self):
        pass
        
    def check_ffmpeg(self) -> bool:
        """Kiểm tra xem máy tính đã cài đặt FFmpeg chưa."""
        if shutil.which("ffmpeg") is None:
            return False
        return True

    def generate_concat_file(self, project_dir: str, timeline: list) -> str:
        """Tạo file concat.txt chuẩn FFmpeg để nối ảnh."""
        concat_path = os.path.join(project_dir, 'concat.txt')
        
        with open(concat_path, 'w', encoding='utf-8') as f:
            for item in timeline:
                # Đường dẫn phải sử dụng dấu '/' chuẩn Unix cho FFmpeg dù ở trên Windows
                # image_path có dạng: data/projects/1/scene_1.jpg
                # Vì concat.txt nằm cùng thư mục project, ta chỉ cần lấy tên file
                img_name = os.path.basename(item['image_path'])
                duration = item['duration']
                
                f.write(f"file '{img_name}'\n")
                f.write(f"duration {duration}\n")
                
            # FFmpeg yêu cầu lặp lại tấm ảnh cuối cùng mà không có dòng duration
            if timeline:
                last_img = os.path.basename(timeline[-1]['image_path'])
                f.write(f"file '{last_img}'\n")
                
        return concat_path

    def render_video(self, script_id: int, timeline: list) -> bool:
        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'projects', str(script_id)))
        
        print("\n[Engine] Bước 1: Khởi tạo dữ liệu Timeline cho FFmpeg...")
        concat_file = self.generate_concat_file(project_dir, timeline)
        
        output_file = os.path.join(project_dir, "final_video.mp4")
        
        # Xóa file cũ nếu đã tồn tại để tránh FFmpeg hỏi "Overwrite? [y/N]" làm treo terminal
        if os.path.exists(output_file):
            os.remove(output_file)
            
        print(f"[Engine] Bước 2: Bắt đầu Render video (Có thể mất vài phút tùy độ dài video)...")
        
        # Lệnh FFmpeg:
        # -f concat -safe 0: Đọc file danh sách
        # -i ... : Input file
        # -vf ... : Bộ lọc Scale đảm bảo luôn ép về 1920x1080 (cắt bỏ phần thừa, giữ đúng tỷ lệ 16:9, lấp đầy viền đen)
        # -c:v libx264: Chuẩn nén H264 phổ thông nhất
        # -pix_fmt yuv420p: Đảm bảo tương thích với mọi trình phát video và trình duyệt
        
        command = [
            "ffmpeg", 
            "-f", "concat", 
            "-safe", "0", 
            "-i", concat_file,
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
            "-fps_mode", "vfr",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            output_file
        ]
        
        try:
            # Chạy ẩn quá trình render, chỉ hiện khi có lỗi
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0:
                print(f"[Engine] => Render thành công! File lưu tại: {output_file}")
                return True
            else:
                print(f"[Engine] => LỖI FFmpeg:\n{result.stderr}")
                return False
        except Exception as e:
            print(f"[Engine] => Lỗi thực thi FFmpeg: {e}")
            return False
