import sys
from core.logger import get_logger
logger = get_logger(__name__)
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.database import init_db, get_scripts_without_assets, get_script_by_id, save_asset
from modules.idea_engine.adapter import GeminiWebAdapter
from modules.scene_illustrator.engine import SceneIllustratorEngine

def main():
    init_db()
    
    scripts = get_scripts_without_assets()
    if not scripts:
        logger.info("\n=> Không có Kịch bản nào đang chờ tạo Hình ảnh (Assets).")
        return
        
    logger.info("\n=== DANH SÁCH KỊCH BẢN CHƯA CÓ HÌNH ẢNH ===")
    for row in scripts:
        logger.info(f"[{row['script_id']}] - Chủ đề: {row['title']}")
        
    choice = input("\nNhập số ID của Kịch bản muốn tạo ảnh: ").strip()
    if not choice.isdigit():
        return
        
    script_id = int(choice)
    script_dict = get_script_by_id(script_id)
    
    if not script_dict:
        logger.error("=> Lỗi: ID không hợp lệ.")
        return
        
    title = next((r['title'] for r in scripts if r['script_id'] == script_id), "Unknown")
    logger.info(f"\n=> Bắt đầu quá trình tạo Hình ảnh cho: '{title}'")
    
    adapter = GeminiWebAdapter()
    engine = SceneIllustratorEngine(adapter=adapter)
    
    asset_obj = engine.generate_assets(script_id, script_dict)
    
    if asset_obj.assets:
        save_asset(script_id, asset_obj)
        logger.info("\n" + "="*50)
        logger.info(f"=== THÀNH CÔNG: Đã tải xong {len(asset_obj.assets)} ảnh ===")
        logger.info("="*50)
        logger.info(f"=> Đường dẫn thư mục chứa ảnh: data/projects/{script_id}/")
    else:
        logger.error("=> Lỗi: Không tải được ảnh nào.")

if __name__ == '__main__':
    main()
