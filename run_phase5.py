import sys
from core.logger import get_logger
logger = get_logger(__name__)
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.database import init_db, get_ready_to_render_projects_with_audio
from modules.video_assembler.engine import VideoAssemblerEngine

def main():
    init_db()
    engine = VideoAssemblerEngine()
    
    if not engine.check_ffmpeg():
        logger.error("Lỗi: Không tìm thấy FFmpeg.")
        return

    projects = get_ready_to_render_projects_with_audio()
    
    if not projects:
        logger.info("\n=> Không có dự án nào đủ điều kiện Render Video có lồng tiếng.")
        return
        
    logger.info("\n=== DANH SÁCH DỰ ÁN SẴN SÀNG RENDER VIDEO CÓ TIẾNG ===")
    for p in projects:
        logger.info(f"[{p['script_id']}] - Tên: {p['title']}")
        
    choice = input("\nNhập số ID của Dự án muốn Render: ").strip()
    if not choice.isdigit():
        return
        
    script_id = int(choice)
    target_project = next((p for p in projects if p['script_id'] == script_id), None)
    
    if target_project:
        engine.render_video_with_audio(script_id, target_project['timeline'])

if __name__ == '__main__':
    main()
