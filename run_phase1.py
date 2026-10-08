import sys
from core.logger import get_logger
logger = get_logger(__name__)
import os
import json

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.database import init_db, get_or_create_project, get_project_ideas, save_idea
from modules.idea_engine.adapter import GeminiWebAdapter
from modules.idea_engine.engine import IdeaEngine

THEMES = {
    "1": "Công nghệ & AI",
    "2": "Bí ẩn Vũ trụ",
    "3": "Lịch sử chưa kể",
    "4": "Tâm lý học hành vi",
    "5": "Quản lý Tài chính",
    "6": "Phát triển bản thân"
}

def main():
    init_db()
    logger.info("\n=== CHỌN CHỦ ĐỀ DỰ ÁN (THEME) ===")
    for key, value in THEMES.items():
        logger.info(f"[{key}] {value}")
        
    choice = input("\nNhập số (1-6) để chọn chủ đề: ").strip()
    theme_name = THEMES.get(choice)
    
    if not theme_name:
        logger.info("Lựa chọn không hợp lệ. Thoát.")
        return

    logger.info(f"\n=> Bạn đã chọn chủ đề: '{theme_name}'")
    project_id = get_or_create_project(theme_name)
    
    logger.info("\n[1/4] Đang khởi tạo Playwright để gọi Gemini...")
    adapter = GeminiWebAdapter()
    engine = IdeaEngine(adapter=adapter)
    
    logger.info("[2/4] Đang yêu cầu Gemini gợi ý 5 ý tưởng... (Vui lòng để yên cửa sổ Chrome lúc nó tự gõ)")
    new_ideas = engine.generate_ideas(theme_name, count=5)
    
    if not new_ideas:
        logger.info("Không nhận được ý tưởng hợp lệ từ Gemini. Vui lòng thử lại sau.")
        return

    logger.info("\n=== CÁC Ý TƯỞNG AI ĐỀ XUẤT ===")
    for idx, idea in enumerate(new_ideas):
        series_text = f"Có (Tập {idea.part_number})" if idea.rabbit_hole_series else "Không"
        logger.info(f"  Ý tưởng {idx+1}: {idea.title}")
        logger.info(f"    - Topics: {', '.join(idea.topics)}")
        logger.info(f"    - Series: {series_text}")
        logger.info(f"    - Summary: {idea.summary[:70]}...\n")

    logger.info("[3/4] Đang kiểm tra trùng lặp (Dedup) với Database...")
    history_ideas = get_project_ideas(project_id)
    
    processed_ideas = []
    for idea in new_ideas:
        max_sim = 0.0
        for old in history_ideas:
            sim = engine.calculate_similarity(idea.topics, old.topics)
            if sim > max_sim:
                max_sim = sim
        
        status = 'pass'
        if max_sim > 0.85:
            status = 'drop'
        elif max_sim >= 0.60:
            status = 'warn'
            
        processed_ideas.append({
            "idea": idea,
            "score": max_sim,
            "status": status
        })

    logger.info("[4/4] Đang lọc quy tắc Rabbit Hole và lưu vào Database...")
    valid_ideas_objs = [item['idea'] for item in processed_ideas if item['status'] != 'drop']
    rabbit_checked_objs = engine.enforce_rabbit_hole(valid_ideas_objs)
    
    saved_count = 0
    logger.info("\n=== KẾT QUẢ XỬ LÝ ===")
    for item in processed_ideas:
        idea_obj = item['idea']
        if item['status'] == 'drop':
            logger.info(f"  [BỎ QUA - TRÙNG LẶP] '{idea_obj.title}' (Similarity: {item['score']:.2f})")
            continue
            
        if idea_obj.rabbit_hole_series and idea_obj not in rabbit_checked_objs:
            logger.info(f"  [BỎ QUA - RABBIT HOLE] '{idea_obj.title}' (Vượt quá giới hạn 3 tập)")
            continue

        save_idea(project_id, idea_obj, item['score'], item['status'])
        saved_count += 1
        logger.info(f"  [ĐÃ LƯU - {item['status'].upper()}] '{idea_obj.title}' (Similarity: {item['score']:.2f})")

    logger.info(f"\n=> Hoàn tất! Đã lưu {saved_count} ý tưởng mới vào Database.")

if __name__ == '__main__':
    main()
