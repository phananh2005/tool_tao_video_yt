import sys
from core.logger import get_logger
logger = get_logger(__name__)
import os
import json

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.database import init_db, get_ideas_without_script, get_idea_by_id, save_script
from modules.idea_engine.adapter import GeminiWebAdapter
from modules.script_gen.engine import ScriptGeneratorEngine

def main():
    init_db()
    
    ideas = get_ideas_without_script()
    if not ideas:
        logger.info("\n=> Không có Idea nào cần tạo kịch bản.")
        logger.info("   (Có thể tất cả đều đã có kịch bản, hoặc chưa có Idea nào thỏa mãn điều kiện Pass/Warn ở Phase 1).")
        return
        
    logger.info("\n=== DANH SÁCH CÁC Ý TƯỞNG (CHƯA CÓ KỊCH BẢN) ===")
    for row in ideas:
        logger.info(f"[{row['id']}] - Trạng thái: {row['status'].upper()} | Chủ đề: {row['title']}")
        
    choice = input("\nNhập số ID của Idea muốn làm kịch bản (hoặc nhấn Enter để thoát): ").strip()
    if not choice.isdigit():
        return
        
    idea_id = int(choice)
    idea_obj = get_idea_by_id(idea_id)
    
    if not idea_obj:
        logger.error("=> Lỗi: ID không hợp lệ.")
        return
        
    logger.info(f"\n=> Đã chọn Idea: '{idea_obj.title}'")
    
    # Khởi tạo Adapter với cấu hình cũ (Tự mở Chrome có Session)
    adapter = GeminiWebAdapter()
    engine = ScriptGeneratorEngine(adapter=adapter)
    
    # Thực thi quá trình sinh script nhiều bước (Chunking)
    script = engine.generate_full_script(idea_id, idea_obj)
    
    if not script.scenes:
        logger.error("=> Lỗi: Quá trình tạo kịch bản thất bại. Hãy kiểm tra lại kết nối hoặc tài khoản Gemini.")
        return
        
    logger.info("\n" + "="*50)
    logger.info("=== HOÀN TẤT: PREVIEW KỊCH BẢN ===")
    logger.info("="*50)
    logger.info(f"Tổng thời gian ước tính : {script.estimated_total_duration} giây")
    logger.info(f"Tổng số phân cảnh (Scenes): {len(script.scenes)}\n")
    
    for sc in script.scenes:
        logger.info(f"📺 [Scene {sc.scene_number}] - Thuộc Chương {sc.chapter_number} ({sc.duration_seconds}s)")
        logger.info(f"  🎬 Hình ảnh: {sc.visual_concept}")
        logger.info(f"  🗣️ Lời bình: {', '.join(sc.narration_outline)}")
        logger.info("-" * 40)
    
    # Lưu vào DB
    save_script(idea_id, script)
    logger.info(f"\n=> [THÀNH CÔNG] Đã lưu kịch bản cho Idea ID {idea_id} vào Database.")

if __name__ == '__main__':
    main()
