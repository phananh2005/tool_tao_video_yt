import os
import time
from core.contracts import AIProviderContract, AssetSceneJSON, AssetJSON

class SceneIllustratorEngine:
    def __init__(self, adapter: AIProviderContract):
        self.adapter = adapter

    def generate_assets(self, script_id: int, script_dict: dict) -> AssetJSON:
        all_scenes = script_dict['scenes']
        
        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'projects', str(script_id)))
        os.makedirs(project_dir, exist_ok=True)

        print(f"\n[Engine] Yêu cầu Gemini vẽ {len(all_scenes)} bức ảnh trực tiếp từ Web...")
        final_assets = []
        
        for sc in all_scenes:
            s_num = sc['scene_number']
            img_name = f"scene_{s_num}.jpg"
            img_path = os.path.join(project_dir, img_name)
            
            print(f"\n=> [Scene {s_num}] Visual Concept: {sc['visual_concept']}")
            
            # Cơ chế Resume
            if os.path.exists(img_path) and os.path.getsize(img_path) > 0:
                print("  -> Ảnh đã tồn tại (Skip).")
                rel_path = f"data/projects/{script_id}/{img_name}"
                final_assets.append(AssetSceneJSON(scene_number=s_num, image_prompt=sc['visual_concept'], image_path=rel_path))
                continue
            
            # Gọi Gemini vẽ, bóc link và tự tải bằng chính trình duyệt đó
            img_url = self.adapter.generate_image(sc['visual_concept'], save_path=img_path)
            
            if img_url and os.path.exists(img_path):
                print("  -> TẢI ẢNH THÀNH CÔNG!")
                rel_path = f"data/projects/{script_id}/{img_name}"
                final_assets.append(AssetSceneJSON(scene_number=s_num, image_prompt=sc['visual_concept'], image_path=rel_path))
            else:
                print("  -> LỖI: Gemini từ chối vẽ ảnh hoặc không thể trích xuất/tải ảnh về.")
                
            # Đợi 5s cho máy nguội trước khi bắt nó vẽ tiếp
            time.sleep(5)

        return AssetJSON(script_id=script_id, assets=final_assets)
