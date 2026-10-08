from core.logger import get_logger
logger = get_logger(__name__)
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
        resized_dir = os.path.join(project_dir, 'resized_images')

        if not os.path.exists(resized_dir):
            os.makedirs(resized_dir)

        with open(video_concat_path, 'w', encoding='utf-8') as f_v, open(audio_concat_path, 'w', encoding='utf-8') as f_a:
            for item in timeline:
                img_path = item['image_path']
                img_name = os.path.basename(img_path)
                resized_img_name = f"resized_{img_name}"
                resized_img_path = os.path.join(resized_dir, resized_img_name)

                # Resize and pad each image to exact 1920x1080 to avoid concat demuxer resolution issues
                if not os.path.exists(resized_img_path):
                    subprocess.run([
                        "ffmpeg", "-y", "-i", os.path.join(project_dir, img_name),
                        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease:flags=lanczos,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,unsharp=5:5:0.5:5:5:0.0",
                        "-q:v", "2",
                        resized_img_path
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)

                audio_name = os.path.basename(item['audio_path'])
                duration = item['duration']

                f_v.write(f"file 'resized_images/{resized_img_name}'\n")
                f_v.write(f"duration {duration}\n")

                f_a.write(f"file '{audio_name}'\n")

            if timeline:
                last_img = os.path.basename(timeline[-1]['image_path'])
                f_v.write(f"file 'resized_images/resized_{last_img}'\n")

        return video_concat_path, audio_concat_path

    def _build_xfade_command(self, project_dir: str, timeline: list, audio_concat_path: str, output_file: str) -> list:
        fade_d = 0.5
        inputs_args = []
        filter_lines = []

        n = len(timeline)
        current_audio_time = 0.0

        for i, item in enumerate(timeline):
            T_i = item['duration']
            img_name = os.path.basename(item['image_path'])
            resized_img_path = os.path.join(project_dir, 'resized_images', f"resized_{img_name}")

            if n == 1:
                v_dur = T_i
            elif i == 0 or i == n - 1:
                v_dur = T_i + fade_d / 2
            else:
                v_dur = T_i + fade_d

            inputs_args.extend(["-loop", "1", "-framerate", "30", "-t", str(v_dur), "-i", resized_img_path])

            if i > 0:
                offset = current_audio_time - fade_d / 2
                in_pad = f"[v{i-1}]" if i > 1 else "[0:v]"
                out_pad = f"[v{i}]"
                next_input = f"[{i}:v]"

                line = f"{in_pad}{next_input}xfade=transition=fade:duration={fade_d}:offset={offset}{out_pad}"
                filter_lines.append(line)

            current_audio_time += T_i

        filter_script = ";\n".join(filter_lines)
        if n > 1:
            filter_script += f";\n[v{n-1}]format=yuv420p[vout]"
        else:
            filter_script = "[0:v]format=yuv420p[vout]"

        cmd = ["ffmpeg"] + inputs_args + [
            "-f", "concat", "-safe", "0", "-i", audio_concat_path,
            "-filter_complex", filter_script,
            "-map", "[vout]", "-map", f"{n}:a",
            "-c:v", "libx264",
            "-preset", "veryslow",
            "-tune", "stillimage",
            "-crf", "16",
            "-color_primaries", "bt709",
            "-color_trc", "bt709",
            "-colorspace", "bt709",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-y",
            output_file
        ]
        return cmd

    def render_video_stream(self, script_id: int, timeline: list):
        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'projects', str(script_id)))

        yield f"data: [Engine] Bước 1: Khởi tạo dữ liệu Ảnh và Âm thanh cho FFmpeg...\n\n"
        v_concat, a_concat = self.generate_concat_files(project_dir, timeline)

        output_file = os.path.join(project_dir, "final_video_with_voice.mp4")
        if os.path.exists(output_file):
            os.remove(output_file)

        yield f"data: [Engine] Bước 2: Bắt đầu Render video lồng tiếng (với hiệu ứng chuyển cảnh)...\n\n"

        command = self._build_xfade_command(project_dir, timeline, a_concat, output_file)

        try:
            # Dùng Popen để stream logs realtime
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            for line in iter(process.stdout.readline, ''):
                if line:
                    yield f"data: {line.strip()}\n\n"

            process.stdout.close()
            return_code = process.wait()

            if return_code == 0:
                yield f"data: [Engine] => Render thành công! Video có tiếng lưu tại: {output_file}\n\n"
                yield "data: [DONE]\n\n"
            else:
                yield f"data: [Engine] => LỖI FFmpeg (Exit code: {return_code})\n\n"
                yield "data: [ERROR]\n\n"
        except Exception as e:
            yield f"data: [Engine] => Lỗi thực thi FFmpeg: {str(e)}\n\n"
            yield "data: [ERROR]\n\n"

    def render_video_with_audio(self, script_id: int, timeline: list) -> bool:
        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'projects', str(script_id)))

        logger.info("\n[Engine] Bước 1: Khởi tạo dữ liệu Ảnh và Âm thanh cho FFmpeg...")
        v_concat, a_concat = self.generate_concat_files(project_dir, timeline)

        output_file = os.path.join(project_dir, "final_video_with_voice.mp4")
        if os.path.exists(output_file):
            os.remove(output_file)

        logger.info(f"[Engine] Bước 2: Bắt đầu Render video lồng tiếng (với hiệu ứng chuyển cảnh)...")

        command = self._build_xfade_command(project_dir, timeline, a_concat, output_file)

        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            if result.returncode == 0:
                logger.info(f"[Engine] => Render thành công! Video có tiếng lưu tại: {output_file}")
                return True
            else:
                logger.error(f"[Engine] => LỖI FFmpeg:\n{result.stderr}")
                return False
        except Exception as e:
            logger.error(f"[Engine] => Lỗi thực thi FFmpeg: {e}")
            return False
