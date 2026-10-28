from core.contracts import AIProviderContract
from core.exceptions import ImageRefusalError, ImageTimeoutError
from core.logger import get_logger
logger = get_logger(__name__)
from playwright.sync_api import sync_playwright
import time
import json
import re
import os
import sys

REFUSAL_KEYWORDS = [
    'bên thứ ba',
    'nhà cung cấp nội dung',
    'không tạo được hình ảnh',
    'không thể tạo hình ảnh',
    'chỉnh sửa câu lệnh',
    'vi phạm chính sách',
    'tiêu chuẩn cộng đồng',
    'bản quyền',
    'không thể thực hiện',
    "can't generate",
    "cannot generate",
    "unable to generate",
    "can't fulfill",
    "cannot fulfill",
    "unable to fulfill",
    "third-party content",
    "third-party",
    "third party",
    "copyright",
    "safety guidelines",
    "content policy"
]

def is_refusal_text(text: str) -> bool:
    """Kiểm tra phản hồi của Gemini có chứa mẫu từ chối do bản quyền/chính sách."""
    if not isinstance(text, str) or not text.strip():
        return False
    lower_text = text.lower()
    return any(kw in lower_text for kw in REFUSAL_KEYWORDS)

class GeminiWebAdapter(AIProviderContract):
    def __init__(self):
        self.user_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'chrome_profile'))
        os.makedirs(self.user_data_dir, exist_ok=True)
        
    def generate_text(self, prompt: str, expected_format: str = 'json') -> str:
        with sync_playwright() as p:
            logger.info("\n[HỆ THỐNG] Đang mở Chrome Tự Động...")
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=False,
                channel="chrome",
                args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
                no_viewport=True
            )
            try:
                page = context.pages[0] if context.pages else context.new_page()
                page.goto("https://gemini.google.com/app", timeout=90000)
                input_selector = "rich-textarea p, textarea, div[contenteditable='true']" 
                
                logger.info("[HỆ THỐNG] Đang chờ giao diện Gemini tải lên...")
                try:
                    page.wait_for_selector(input_selector, state="visible", timeout=10000)
                except:
                    logger.info("\n" + "="*65)
                    logger.info("⚠️ YÊU CẦU ĐĂNG NHẬP / XÁC NHẬN ⚠️")
                    logger.info("Tool không tìm thấy ô nhập liệu (Có thể bạn cần đăng nhập).")
                    logger.info("1. Vui lòng đăng nhập Google trên Chrome.")
                    logger.info("2. Chờ màn hình load xong và nhìn thấy giao diện chat.")
                    logger.info("=> SAU KHI THẤY Ô CHAT, NHẤN ENTER TẠI ĐÂY ĐỂ TIẾP TỤC...")
                    logger.info("="*65 + "\n")
                    input()
                
                if expected_format == 'json':
                    prompt += "\n\nCRITICAL: Return ONLY valid JSON format. Do not use markdown ```json ``` blocks. No explanations. Return as an array of objects."

                logger.info("[HỆ THỐNG] Đang gõ prompt vào Gemini...")
                page.wait_for_selector(input_selector, state="visible", timeout=120000)
                page.fill(input_selector, prompt)
                page.keyboard.press("Enter")
                time.sleep(4)
                
                logger.info("[HỆ THỐNG] Đang chờ AI trả kết quả (Vui lòng không bấm chuột)...")
                response_selector = "message-content"
                page.wait_for_selector(response_selector, timeout=180000)
                
                try:
                    page.wait_for_selector("button[aria-label='Copy'], button[data-test-id='copy-button']", timeout=180000)
                except:
                    pass
                
                responses = page.query_selector_all(response_selector)
                latest_response = responses[-1].inner_text()
            except Exception as e:
                logger.error(f"\n[LỖI KHI TƯƠNG TÁC GEMINI] {e}")
                latest_response = ""
            finally:
                context.close()
            
            if expected_format == 'json' and latest_response:
                return self._extract_json(latest_response)
            return latest_response

    def _extract_json(self, text):
        text = re.sub(r'```(?:json)?', '', text).strip()
        try:
            parsed = json.loads(text)
            return json.dumps(parsed)
        except json.JSONDecodeError:
            logger.warning("\n[CẢNH BÁO] Gemini không trả về JSON chuẩn, đang trả về raw text.")
            return text

    def generate_image(self, prompt: str, save_path: str = None) -> str:
        with sync_playwright() as p:
            logger.info("\n[Adapter] Đang mở Chrome để yêu cầu AI vẽ ảnh...")
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=False,
                channel="chrome",
                args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
                no_viewport=True
            )
            
            try:
                page = context.pages[0] if context.pages else context.new_page()
                page.goto("https://gemini.google.com/app", timeout=90000)
                
                input_selector = "rich-textarea p, textarea, div[contenteditable='true']" 
                
                try:
                    page.wait_for_selector(input_selector, state="visible", timeout=10000)
                except:
                    logger.info("\n⚠️ YÊU CẦU ĐĂNG NHẬP ⚠️ Vui lòng đăng nhập Google. Sau đó nhấn Enter tại đây...")
                    input()

                page.wait_for_selector(input_selector, state="visible", timeout=120000)

                full_prompt = (
                    f"Hãy tạo 1 bức ảnh TỶ LỆ 16:9, phong cách HOẠT HÌNH NGUYÊN BẢN (Original Stylized Cartoon), "
                    f"nét vẽ rõ ràng, vui nhộn để minh họa: {prompt}. "
                    f"LƯU Ý BẮT BUỘC ĐỂ KHÔNG BỊ CHẶN BỞI BỘ LỌC BÊN THỨ BA VÀ BẢN QUYỀN: "
                    f"1. TUYỆT ĐỐI KHÔNG vẽ bất kỳ logo, thương hiệu, nhãn hiệu thương mại, hoặc nhân vật bên thứ ba nào. "
                    f"Mọi đồ vật công nghệ, xe cộ đều là hư cấu, trung tính, không nhãn mác (unbranded generic objects). "
                    f"2. TUYỆT ĐỐI KHÔNG vẽ người thật hoặc người nổi tiếng. BẮT BUỘC thay thế con người bằng ĐỘNG VẬT DỄ THƯƠNG (chó, mèo, thỏ...) hoặc ROBOT ĐÁNG YÊU. "
                    f"3. TUYỆT ĐỐI KHÔNG chứa chữ viết (no text, no letters), không watermark. "
                    f"4. Đây là tác phẩm nghệ thuật hư cấu 100% nguyên bản. CHỈ TẠO ẢNH, KHÔNG GIẢI THÍCH."
                )

                page.fill(input_selector, full_prompt)
                page.keyboard.press("Enter")
                time.sleep(4)

                logger.info("[Adapter] Đang chờ Gemini vẽ ảnh hoặc phản hồi...")

                keywords_json = json.dumps(REFUSAL_KEYWORDS, ensure_ascii=False)
                js_wait_function = f'''() => {{
                    const imgs = Array.from(document.querySelectorAll('img'));
                    for (let i = imgs.length - 1; i >= 0; i--) {{
                        const rect = imgs[i].getBoundingClientRect();
                        if (rect.width > 250 && rect.height > 150) {{
                            return {{ status: 'image_ready', index: i }};
                        }}
                    }}
                    const messages = Array.from(document.querySelectorAll('message-content, .message-content, [data-test-id="model-response"]'));
                    if (messages.length > 0) {{
                        const lastMsg = messages[messages.length - 1];
                        const text = (lastMsg.innerText || '').toLowerCase();
                        const refusalPhrases = {keywords_json};
                        for (const kw of refusalPhrases) {{
                            if (text.includes(kw)) {{
                                return {{ status: 'refusal', reason: lastMsg.innerText.trim() }};
                            }}
                        }}
                    }}
                    return null;
                }}'''

                try:
                    eval_result = page.wait_for_function(js_wait_function, timeout=120000)
                    result_data = eval_result.json_value() if eval_result else None

                    if isinstance(result_data, dict) and result_data.get('status') == 'refusal':
                        reason = result_data.get('reason') or "Bị từ chối bởi bộ lọc bên thứ ba"
                        logger.warning(f"[Adapter] Gemini từ chối vẽ ảnh: {reason}")
                        raise ImageRefusalError(message=f"Gemini từ chối vẽ ảnh: {reason}", reason=reason, prompt=prompt)

                    if isinstance(result_data, dict) and result_data.get('status') == 'image_ready' and save_path:
                        img_index = result_data.get('index', 0)
                        imgs = page.query_selector_all('img')
                        if 0 <= img_index < len(imgs):
                            element_handle = imgs[img_index]
                            element_handle.scroll_into_view_if_needed()
                            time.sleep(2)
                            element_handle.screenshot(path=save_path)
                            logger.info("[Adapter] => [THÀNH CÔNG] Đã lưu ảnh vào ổ cứng!")
                            return "saved_successfully"
                    return ""
                except ImageRefusalError:
                    raise
                except Exception as wait_err:
                    logger.error(f"[Adapter] Lỗi quá thời gian chờ hoặc phát hiện ảnh: {wait_err}")
                    return ""

            except ImageRefusalError:
                raise
            except Exception as e:
                logger.error(f"\n[LỖI VẼ ẢNH GEMINI] {e}")
                return ""
            finally:
                context.close()
