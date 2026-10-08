import sys
from core.logger import get_logger
logger = get_logger(__name__)
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.database import init_db, get_scripts_without_voiceover, get_script_by_id, save_voiceover
from modules.idea_engine.adapter import GeminiWebAdapter
from modules.voiceover.engine import VoiceoverEngine

def main():
    init_db()
    
    scripts = get_scripts_without_voiceover()
    if not scripts:
        logger.info("\n=> Không có Kịch bản (Script) nào đang chờ tạo lời thoại.")
        return
        
    logger.info("\n=== DANH SÁCH KỊCH BẢN CHƯA CÓ LỜI THOẠI (VOICEOVER) ===")
    for row in scripts:
        logger.info(f"[{row['script_id']}] - Chủ đề: {row['title']}")
        
    choice = input("\nNhập số ID của Kịch bản muốn tạo lời thoại: ").strip()
    if not choice.isdigit():
        return
        
    script_id = int(choice)
    script_dict = get_script_by_id(script_id)
    
    if not script_dict:
        logger.error("=> Lỗi: ID không hợp lệ.")
        return
        
    title_for_vo = next((r['title'] for r in scripts if r['script_id'] == script_id), "Unknown")
    logger.info(f"\n=> Bắt đầu tạo lời thoại cho: '{title_for_vo}'")
    
    adapter = GeminiWebAdapter()
    engine = VoiceoverEngine(adapter=adapter)
    
    vo_obj = engine.generate_full_voiceover(script_id, script_dict, title_for_vo)
    
    if not vo_obj.voiceover_scenes:
        logger.error("=> Lỗi: Sinh lời thoại thất bại.")
        return
        
    logger.info("\n" + "="*50)
    logger.info("=== HOÀN TẤT: PREVIEW LỜI THOẠI (VOICEOVER) ===")
    logger.info("="*50)
    logger.info(f"Đã tạo lời thoại cho {len(vo_obj.voiceover_scenes)} phân cảnh.\n")
    
    for vo in vo_obj.voiceover_scenes[:5]: # Preview 5 cảnh đầu
        logger.info(f"🎙️ [Scene {vo.scene_number}]")
        logger.info(f"   {vo.spoken_text}")
        logger.info("-" * 40)
    
    if len(vo_obj.voiceover_scenes) > 5:
        logger.info("  ... (Còn tiếp)")
        
    save_voiceover(script_id, vo_obj)
    logger.info(f"\n=> [THÀNH CÔNG] Đã lưu Voiceover cho Script ID {script_id} vào Database.")

if __name__ == '__main__':
    main()
