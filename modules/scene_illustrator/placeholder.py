import os
import subprocess
from core.logger import get_logger

logger = get_logger(__name__)


def create_placeholder_image(output_path: str, scene_number: int, reason: str = "") -> bool:
    """Tạo ảnh tĩnh dự phòng chuẩn 1920x1080 bằng FFmpeg khi AI từ chối vẽ ảnh."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    if reason:
        logger.info(f"Tạo placeholder cho Scene {scene_number} do lý do: {reason}")
    safe_text = f"Scene {scene_number} - Image Placeholder"
    sub_text = "AI Refusal - Please regenerate"

    cmd_text = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", "color=c=0x1e293b:s=1920x1080:d=1",
        "-vf", (
            f"drawtext=text='{safe_text}':fontcolor=0xf8fafc:fontsize=54:"
            f"x=(w-text_w)/2:y=(h-text_h)/2-35,"
            f"drawtext=text='{sub_text}':fontcolor=0x94a3b8:fontsize=30:"
            f"x=(w-text_w)/2:y=(h-text_h)/2+35"
        ),
        "-update", "1", "-frames:v", "1", output_path
    ]

    try:
        res = subprocess.run(
            cmd_text, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            timeout=15
        )
        if res.returncode == 0 and os.path.isfile(output_path) and os.path.getsize(output_path) > 0:
            return True
    except Exception as e:
        logger.warning(f"Lỗi vẽ text trên placeholder bằng ffmpeg: {e}")

    # Fallback an toàn tuyệt đối 100% không cần fontfile (màu nền solid dark slate)
    cmd_solid = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", "color=c=0x1e293b:s=1920x1080:d=1",
        "-update", "1", "-frames:v", "1", output_path
    ]
    try:
        res_solid = subprocess.run(
            cmd_solid, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            timeout=15
        )
        return res_solid.returncode == 0 and os.path.isfile(output_path) and os.path.getsize(output_path) > 0
    except Exception as e:
        logger.error(f"Lỗi tạo ảnh placeholder ffmpeg: {e}")
        return False
