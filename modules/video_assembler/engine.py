import os
import subprocess
import shutil

class VideoAssemblerEngine:
    def __init__(self):
        pass
        
    def check_ffmpeg(self) -> bool:
        if shutil.which("ffmpeg") is None:
            return False
        return True

    def generate_concat_files(self, project_dir: str, timeline: list) -> tuple:
        video_concat_path = os.path.join(project_dir, 'video_concat.txt')
        audio_concat_path = os.path.join(project_dir, 'audio_concat.txt')
        
        with open(video_concat_path, 'w', encoding='utf-8') as f_v, open(audio_concat_path, 'w', encoding='utf-8') as f_a:
            for item in timeline:
                img_name = os.path.basename(item['image_path'])
                audio_name = os.path.basename(item['audio_path'])
                duration = item['duration']
                
                f_v.write(f"file '{img_name}'\n")
                f_v.write(f"duration {duration}\n")
                
                f_a.write(f"file '{audio_name}'\n")
                
            if timeline:
                last_img = os.path.basename(timeline[-1]['image_path'])
                f_v.write(f"file '{last_img}'\n")
                
        return video_concat_path, audio_concat_path

    def render_video_with_audio(self, script_id: int, timeline: list) -> bool:
        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'projects', str(script_id)))
        
        print("\n[Engine] Bước 1: Khởi tạo dữ liệu Ảnh và Âm thanh cho FFmpeg...")
        v_concat, a_concat = self.generate_concat_files(project_dir, timeline)
        
        output_file = os.path.join(project_dir, "final_video_with_voice.mp4")
        if os.path.exists(output_file):
            os.remove(output_file)
            
        print(f"[Engine] Bước 2: Bắt đầu Render video lồng tiếng...")
        
        command = [
            "ffmpeg", 
            "-f", "concat", "-safe", "0", "-i", v_concat,  # Input 1: Video (Ảnh)
            "-f", "concat", "-safe", "0", "-i", a_concat,  # Input 2: Audio (Tiếng)
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest", # Cắt video nếu audio hoặc video bị lệch đuôi
            output_file
        ]
        
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                print(f"[Engine] => Render thành công! Video có tiếng lưu tại: {output_file}")
                return True
            else:
                print(f"[Engine] => LỖI FFmpeg:\n{result.stderr}")
                return False
        except Exception as e:
            print(f"[Engine] => Lỗi thực thi FFmpeg: {e}")
            return False
