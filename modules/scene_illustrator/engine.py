import json
from core.logger import get_logger
logger = get_logger(__name__)
import os
import sqlite3
import time
import re
from core import database
from core.contracts import AIProviderContract, AssetSceneJSON, AssetJSON
from core.exceptions import ImageRefusalError
from modules.scene_illustrator.placeholder import create_placeholder_image

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
        Nhiệm vụ: Xây dựng GIÁM ĐỐC NGHỆ THUẬT (Art Direction) ĐỒNG NHẤT VÀ NGUYÊN BẢN cho một video YouTube.
        Dưới đây là một số hình ảnh xuất hiện trong video:
        {context}

        Yêu cầu:
        Bạn là Giám đốc Nghệ thuật (Art Director) chuyên nghiệp. Hãy định nghĩa MỘT phong cách hình ảnh (Visual Style) xuyên suốt bằng TIẾNG ANH (khoảng 30-45 từ) gồm: Style, Lighting, Color Palette, Mood.

        RÀNG BUỘC PHÒNG NGỪA BẢN QUYỀN BÊN THỨ BA (BẮT BUỘC):
        1. TUYỆT ĐỐI KHÔNG dùng tên studio, hãng phim (KHÔNG Pixar, Disney, Studio Ghibli, DreamWorks, Marvel).
        2. TUYỆT ĐỐI KHÔNG nhắc tên bất kỳ họa sĩ hay nghệ sĩ cụ thể nào.
        3. CHỈ DÙNG thuật ngữ nghệ thuật trung tính, nguyên bản (ví dụ: stylized 2.5D digital illustration, modern minimalist vector art).

        Chỉ trả về đoạn mô tả phong cách bằng tiếng Anh thuần túy.
        """
        return self.adapter.generate_text(prompt, expected_format='text').strip()

    def sanitize_prompt_via_ai(self, prompt: str, refusal_reason: str = "") -> str:
        sanitize_instruction = f"""
        Rewrite the following image prompt into an original, 100% unbranded Text-to-Image prompt in English.
        The previous prompt was REFUSED with reason: "{refusal_reason}".

        RULES:
        1. Strip all trademarked characters, celebrities, brand names, and copyrighted intellectual property.
        2. Replace them with generic descriptions, cute cartoon animals, or friendly robots.
        3. Maintain the artistic visual style, composition, lighting, and action.
        4. Output ONLY the sanitized English prompt (maximum 75 words), no explanations, no quotes.

        Original prompt:
        {prompt}
        """
        sanitized = self.adapter.generate_text(sanitize_instruction, expected_format='text').strip()
        if sanitized.startswith('"') and sanitized.endswith('"'):
            sanitized = sanitized[1:-1]
        return sanitized

    def sanitize_prompt_safe_mode(self, scene_number: int, visual_concept: str) -> str:
        return (
            f"A cheerful cute cartoon animal or friendly robot illustrating: {visual_concept}. "
            "Simple clean shapes, bright pleasant colors, friendly atmosphere, vector art style. "
            "No text, no words, no letters, no logos, no real people, completely original fictional artwork."
        )

    def generate_single_image(self, script_id: int, scene_number: int, prompt: str) -> str:
        project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'projects', str(script_id)))
        os.makedirs(project_dir, exist_ok=True)
        img_name = f"scene_{scene_number}.jpg"
        img_path = os.path.join(project_dir, img_name)
        logger.info(f"\n=> [Scene {scene_number}] Vẽ lại ảnh với Prompt: {prompt}")

        # Xóa file cũ nếu có để force lưu file mới (dù adapter.generate_image thường tự ghi đè)
        if os.path.exists(img_path):
            try:
                os.remove(img_path)
            except Exception:
                pass

        current_prompt = prompt
        image_success = False
        refusal_reason = None
        max_retries = 2

        for attempt in range(max_retries + 1):
            try:
                img_url = self.adapter.generate_image(current_prompt, save_path=img_path)
                if img_url and os.path.exists(img_path):
                    image_success = True
                    break
                break
            except ImageRefusalError as e:
                refusal_reason = e.reason
                logger.warning(f"  -> Gemini từ chối vẽ ảnh (lần {attempt + 1}): {e.reason}")
                if attempt == 0:
                    try:
                        current_prompt = self.sanitize_prompt_via_ai(current_prompt, e.reason)
                    except Exception as se:
                        logger.warning(f"  -> Lỗi gọi sanitize AI ({se}), chuyển sang safe-mode.")
                        current_prompt = self.sanitize_prompt_safe_mode(scene_number, prompt)
                elif attempt == 1:
                    current_prompt = self.sanitize_prompt_safe_mode(scene_number, prompt)
            except Exception as e:
                logger.error(f"  -> LỖI KHI VẼ ẢNH: {e}")
                break

        if image_success and os.path.exists(img_path):
            logger.info("  -> TẢI ẢNH THÀNH CÔNG!")
            return (f"data/projects/{script_id}/{img_name}", False, None)
        else:
            logger.warning("  -> Kích hoạt ảnh Placeholder an toàn bằng FFmpeg.")
            if create_placeholder_image(img_path, scene_number, refusal_reason or "AI Refusal"):
                return (f"data/projects/{script_id}/{img_name}", True, refusal_reason)
            return (None, False, None)

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

        logger.info(f"\n[Engine] BƯỚC 1: Xây dựng Giám đốc Nghệ thuật (Art Direction) cho toàn bộ video...")
        art_direction = self.develop_art_direction(all_scenes)
        logger.info(f"  -> Phong cách chủ đạo: {art_direction}")

        logger.info(f"\n[Engine] BƯỚC 2: Tối ưu hóa Image Prompts (Chuyển đổi ý tưởng thành cú pháp vẽ ảnh chuyên nghiệp) & Vẽ ảnh...")
        final_assets = []

        for sc in all_scenes:
            s_num = sc['scene_number']
            visual_concept = sc['visual_concept']
            spoken_text = voiceover_by_scene.get(s_num, '')

            # Sử dụng AI để Optimize Image Prompt cho scene này
            optimize_prompt = f"""
            Rewrite the following scene description into an original, highly detailed Text-to-Image prompt in English that strictly complies with third-party copyright policies.

            Visual Concept: {visual_concept}
            Narration happening in this scene: "{spoken_text}"
            Global Art Style for the video: {art_direction}

            RULES:
            - Combine visual concept and narration into one cohesive, dynamic visual scene.
            - Focus on composition, subject action, camera angle, and the exact art style provided.
            - THIRD-PARTY IP & BRAND NEUTRALIZATION (MANDATORY): Replace all brand/company names, trademarked products, celebrities, and copyrighted characters with generic unbranded objects, cute cartoon animals, or friendly robots.
            - STRICTLY NO text, NO words, NO logos, NO emblems, NO watermarks, NO real humans, NO violence.
            - Output ONLY the final image prompt text in English, maximum 85 words.
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

            logger.info(f"\n=> [Scene {s_num}] Original: {visual_concept}")
            logger.info(f"  -> AI Optimized Prompt: {optimized_concept}")

            if (
                os.path.exists(img_path)
                and os.path.getsize(img_path) > 0
                and (
                    existing_scene := existing_assets.get(s_num)
                ) is not None
                and existing_scene.get('image_prompt') == image_prompt
                and existing_scene.get('image_path') == f"data/projects/{script_id}/{img_name}"
                and not existing_scene.get('is_placeholder', False)
            ):
                logger.info("  -> Ảnh đã tồn tại với prompt hiện tại (Skip).")
                rel_path = f"data/projects/{script_id}/{img_name}"
                final_assets.append(AssetSceneJSON(scene_number=s_num, image_prompt=image_prompt, image_path=rel_path))
                continue

            current_prompt = image_prompt
            image_success = False
            is_placeholder = False
            refusal_reason_record = None
            max_retries = 2

            for attempt in range(max_retries + 1):
                try:
                    img_url = self.adapter.generate_image(current_prompt, save_path=img_path)
                    if img_url and os.path.exists(img_path):
                        image_success = True
                        break
                    break
                except ImageRefusalError as e:
                    refusal_reason_record = e.reason
                    logger.warning(f"  -> Gemini từ chối vẽ ảnh (lần {attempt + 1}): {e.reason}")
                    if attempt == 0:
                        try:
                            current_prompt = self.sanitize_prompt_via_ai(current_prompt, e.reason)
                        except Exception as se:
                            logger.warning(f"  -> Lỗi gọi sanitize AI ({se}), chuyển sang safe-mode.")
                            current_prompt = self.sanitize_prompt_safe_mode(s_num, visual_concept)
                    elif attempt == 1:
                        current_prompt = self.sanitize_prompt_safe_mode(s_num, visual_concept)
                except Exception as e:
                    logger.error(f"  -> LỖI KHI VẼ ẢNH: {e}")
                    break

            if image_success and os.path.exists(img_path):
                logger.info("  -> TẢI ẢNH THÀNH CÔNG!")
                rel_path = f"data/projects/{script_id}/{img_name}"
            else:
                logger.warning(f"  -> Scene {s_num}: Kích hoạt Fallback Placeholder bằng FFmpeg...")
                if create_placeholder_image(img_path, s_num, refusal_reason_record or "AI Refusal"):
                    rel_path = f"data/projects/{script_id}/{img_name}"
                    is_placeholder = True
                else:
                    logger.error(f"  -> Scene {s_num}: Không thể tạo ảnh placeholder.")
                    rel_path = ""
                    is_placeholder = False

            final_assets.append(AssetSceneJSON(
                scene_number=s_num,
                image_prompt=current_prompt,
                image_path=rel_path,
                is_placeholder=is_placeholder,
                refusal_reason=refusal_reason_record if is_placeholder else None
            ))

            time.sleep(5)

        return AssetJSON(script_id=script_id, assets=final_assets)
