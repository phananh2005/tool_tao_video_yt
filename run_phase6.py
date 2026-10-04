import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.database import init_db, get_rendered_projects_without_seo, save_seo_metadata
from modules.idea_engine.adapter import GeminiWebAdapter
from modules.seo_optimizer.engine import SEOOptimizerEngine

def main():
    init_db()
    
    projects = get_rendered_projects_without_seo()
    if not projects:
        print("\n=> Không có Dự án nào cần tối ưu SEO.")
        return
        
    print("\n=== DANH SÁCH DỰ ÁN SẴN SÀNG TỐI ƯU SEO & XUẤT BẢN ===")
    for p in projects:
        print(f"[{p['script_id']}] - Tên: {p['title']}")
        
    choice = input("\nNhập số ID của Dự án: ").strip()
    if not choice.isdigit():
        return
        
    script_id = int(choice)
    target = next((p for p in projects if p['script_id'] == script_id), None)
    
    if not target:
        print("=> Lỗi: ID không hợp lệ.")
        return
        
    print(f"\n=> Bắt đầu sinh bộ từ khóa SEO cho: '{target['title']}'")
    
    adapter = GeminiWebAdapter()
    engine = SEOOptimizerEngine(adapter=adapter)
    
    result = engine.format_upload_info(script_id, target['title'], target['script_dict'], target['asset_dict'])
    
    if result:
        seo_data, file_path = result
        save_seo_metadata(script_id, seo_data)
        
        print("\n" + "="*50)
        print("🎉 HOÀN TẤT PHASE 6: SẴN SÀNG XUẤT BẢN 🎉")
        print("="*50)
        print(f"Đã lưu thành công bộ thông tin Upload YouTube!")
        print(f"👉 File của bạn nằm tại: {file_path}")
        print("Bạn chỉ cần copy toàn bộ nội dung file này dán vào Youtube Studio là xong.")
    else:
        print("=> Lỗi: Quá trình tối ưu SEO thất bại.")

if __name__ == '__main__':
    main()
