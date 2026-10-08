import json
import os
import sqlite3
import time
import re
from core import database
from core.contracts import AIProviderContract, AssetSceneJSON, AssetJSON

class SceneIllustratorEngine:
    def __init__(self, adapter: AIProviderContract):
        self.adapter = adapter

    def _extract_json_array(self, text: str) -> list:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            text = match.group(0)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return []

    def develop_art_direction(self, all_scenes: list) -> str:
        # Trích xuất một số scene tiêu biểu để AI nắm được không khí
        sample_scenes = all_scenes[:5] + all_scenes[-2:]
        context = "\n".join([f"- {sc['visual_concept']}" for sc in sample_scenes])

        prompt = f"""
        Nhiệm vụ: Xây dựng GIÁM ĐỐC NGHỆ THUẬT (Art Direction) ĐỒNG NHẤT cho một video YouTube.
        Dưới đây là một số hình ảnh xuất hiện trong video:
        {context}

        Yêu cầu:
        Bạn là một Giám đốc Nghệ thuật (Art Director) hàng đầu. Hãy định nghĩa MỘT phong cách hình ảnh (Visual Style) xuyên suốt cho video này để tất cả các ảnh tạo ra trông như cùng một bộ phim.
        Hãy viết một đoạn mô tả phong cách bằng TIẾNG ANH (khoảng 30-50 từ) gồm: Style (Cinematic, 3D, Anime, Minimalist...), Lighting (Dramatic, soft...), Color Palette (Muted, vibrant...), và Mood.

        Chỉ trả về đoạn mô tả phong cách bằng tiếng Anh thuần túy.
        """
        return self.adapter.generate_text(prompt, expected_format='text').strip()

    def generate_single_image(self, script_id: int, scene_number: int, prompt: str) -> str:
        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'projects', str(script_id)))
        os.makedirs(project_dir, exist_ok=True)
        img_name = f"scene_{scene_number}.jpg"
        img_path = os.path.join(project_dir, img_name)
        print(f"\n=> [Scene {scene_number}] Vẽ lại ảnh với Prompt: {prompt}")

        # Xóa file cũ nếu có để force lưu file mới (dù adapter.generate_image thường tự ghi đè)
        if os.path.exists(img_path):
            try:
                os.remove(img_path)
            except Exception:
                pass

        try:
            img_url = self.adapter.generate_image(prompt, save_path=img_path)
        except Exception as e:
            print(f"  -> LỖI KHI VẼ ẢNH: {e}")
            img_url = None

        if img_url and os.path.exists(img_path):
            print("  -> TẢI ẢNH THÀNH CÔNG!")
            return f"data/projects/{script_id}/{img_name}"
        else:
            print("  -> LỖI: Trình giả lập không thể sinh hoặc tải ảnh về.")
            return None

    def _get_existing_assets(self, script_id: int) -> dict:
        conn = sqlite3.connect(database.DB_PATH)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT content FROM assets WHERE script_id = ?", (script_id,))
            row = cursor.fetchone()
        finally:
            conn.close()

        if not row:
            return {}

        try:
            asset_data = json.loads(row[0])
        except (TypeError, ValueError, UnicodeDecodeError, RecursionError):
            return {}

        if not isinstance(asset_data, dict):
            return {}

        assets = asset_data.get('assets', [])
        if not isinstance(assets, list):
            return {}

        scenes = {}
        for asset in assets:
            if not isinstance(asset, dict):
                continue
            scene_number = asset.get('scene_number')
            try:
                hash(scene_number)
            except TypeError:
                continue
            scenes[scene_number] = asset
        return scenes

    def generate_assets(self, script_id: int, script_dict: dict, voiceover_scenes: list = None) -> AssetJSON:
        all_scenes = script_dict['scenes']
        voiceover_by_scene = {}
        for voiceover_scene in voiceover_scenes or []:
            scene_number = voiceover_scene['scene_number']
            if scene_number in voiceover_by_scene:
                raise ValueError(f"Duplicate voiceover scene_number: {scene_number}")
            voiceover_by_scene[scene_number] = voiceover_scene.get('spoken_text', '')

        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'projects', str(script_id)))
        os.makedirs(project_dir, exist_ok=True)

        existing_assets = self._get_existing_assets(script_id)

        print(f"\n[Engine] BƯỚC 1: Xây dựng Giám đốc Nghệ thuật (Art Direction) cho toàn bộ video...")
        art_direction = self.develop_art_direction(all_scenes)
        print(f"  -> Phong cách chủ đạo: {art_direction}")

        print(f"\n[Engine] BƯỚC 2: Tối ưu hóa Image Prompts (Chuyển đổi ý tưởng thành cú pháp vẽ ảnh chuyên nghiệp) & Vẽ ảnh...")
        final_assets = []

        for sc in all_scenes:
            s_num = sc['scene_number']
            visual_concept = sc['visual_concept']
            spoken_text = voiceover_by_scene.get(s_num, '')

            # Sử dụng AI để Optimize Image Prompt cho scene này
            optimize_prompt = f"""
            Rewrite the following scene description into a highly detailed, professional Text-to-Image prompt (in English).

            Visual Concept: {visual_concept}
            Narration happening in this scene: "{spoken_text}"
            Global Art Style for the video: {art_direction}

            RULES:
            - Combine the visual concept and narration into one cohesive, highly descriptive visual scene.
            - Focus on composition, subject action, camera angle, and the exact art style provided.
            - Do not include text, words, logos, or letters in the image.
            - Output ONLY the final image prompt text in English, nothing else. Maximum 100 words.
            """
            optimized_concept = self.adapter.generate_text(optimize_prompt, expected_format='text').strip()
            # Xóa các dấu ngoặc kép bọc ngoài nếu có
            if optimized_concept.startswith('"') and optimized_concept.endswith('"'):
                optimized_concept = optimized_concept[1:-1]

            image_prompt = (
                f"{optimized_concept}\n\n"
                f"Global Style: {art_direction}\n\n"
                "IMPORTANT: No text, no words, no letters, no logos, no watermarks."
            )

            img_name = f"scene_{s_num}.jpg"
            img_path = os.path.join(project_dir, img_name)

            print(f"\n=> [Scene {s_num}] Original: {visual_concept}")
            print(f"  -> AI Optimized Prompt: {optimized_concept}")

            if (
                os.path.exists(img_path)
                and os.path.getsize(img_path) > 0
                and (
                    existing_scene := existing_assets.get(s_num)
                ) is not None
                and existing_scene.get('image_prompt') == image_prompt
                and existing_scene.get('image_path') == f"data/projects/{script_id}/{img_name}"
            ):
                print("  -> Ảnh đã tồn tại với prompt hiện tại (Skip).")
                rel_path = f"data/projects/{script_id}/{img_name}"
                final_assets.append(AssetSceneJSON(scene_number=s_num, image_prompt=image_prompt, image_path=rel_path))
                continue

            try:
                img_url = self.adapter.generate_image(image_prompt, save_path=img_path)
            except Exception as e:
                print(f"  -> LỖI KHI VẼ ẢNH: {e}")
                img_url = None

            if img_url and os.path.exists(img_path):
                print("  -> TẢI ẢNH THÀNH CÔNG!")
                rel_path = f"data/projects/{script_id}/{img_name}"
                final_assets.append(AssetSceneJSON(scene_number=s_num, image_prompt=image_prompt, image_path=rel_path))
            else:
                print("  -> LỖI: Gemini từ chối vẽ ảnh hoặc không thể trích xuất/tải ảnh về.")
                final_assets.append(AssetSceneJSON(scene_number=s_num, image_prompt=image_prompt, image_path=""))

            time.sleep(5)

        return AssetJSON(script_id=script_id, assets=final_assets)
