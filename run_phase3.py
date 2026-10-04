import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.database import init_db, get_scripts_without_voiceover, get_script_by_id, save_voiceover
from modules.idea_engine.adapter import GeminiWebAdapter
from modules.voiceover.engine import VoiceoverEngine

def main():
    init_db()
    
    scripts = get_scripts_without_voiceover()
    if not scripts:
        print("\n=> Không có Kịch bản (Script) nào đang chờ tạo lời thoại.")
        return
        
    print("\n=== DANH SÁCH KỊCH BẢN CHƯA CÓ LỜI THOẠI (VOICEOVER) ===")
    for row in scripts:
        print(f"[{row['script_id']}] - Chủ đề: {row['title']}")
        
    choice = input("\nNhập số ID của Kịch bản muốn tạo lời thoại: ").strip()
    if not choice.isdigit():
        return
        
    script_id = int(choice)
    script_dict = get_script_by_id(script_id)
    
    if not script_dict:
        print("=> Lỗi: ID không hợp lệ.")
        return
        
    title_for_vo = next((r['title'] for r in scripts if r['script_id'] == script_id), "Unknown")
    print(f"\n=> Bắt đầu tạo lời thoại cho: '{title_for_vo}'")
    
    adapter = GeminiWebAdapter()
    engine = VoiceoverEngine(adapter=adapter)
    
    vo_obj = engine.generate_full_voiceover(script_id, script_dict, title_for_vo)
    
    if not vo_obj.voiceover_scenes:
        print("=> Lỗi: Sinh lời thoại thất bại.")
        return
        
    print("\n" + "="*50)
    print("=== HOÀN TẤT: PREVIEW LỜI THOẠI (VOICEOVER) ===")
    print("="*50)
    print(f"Đã tạo lời thoại cho {len(vo_obj.voiceover_scenes)} phân cảnh.\n")
    
    for vo in vo_obj.voiceover_scenes[:5]: # Preview 5 cảnh đầu
        print(f"🎙️ [Scene {vo.scene_number}]")
        print(f"   {vo.spoken_text}")
        print("-" * 40)
    
    if len(vo_obj.voiceover_scenes) > 5:
        print("  ... (Còn tiếp)")
        
    save_voiceover(script_id, vo_obj)
    print(f"\n=> [THÀNH CÔNG] Đã lưu Voiceover cho Script ID {script_id} vào Database.")

if __name__ == '__main__':
    main()
