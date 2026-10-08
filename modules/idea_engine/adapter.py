from core.contracts import AIProviderContract
from core.logger import get_logger
logger = get_logger(__name__)
from playwright.sync_api import sync_playwright
import time
import json
import re
import os
import sys

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

                full_prompt = f"Hãy tạo 1 bức ảnh TỶ LỆ 16:9, phong cách HOẠT HÌNH 2D (2D cartoon), nét vẽ đơn giản, dễ nhìn, vui nhộn để minh họa cho cảnh: {prompt}. LƯU Ý BẮT BUỘC ĐỂ KHÔNG BỊ CHẶN: TUYỆT ĐỐI KHÔNG vẽ người thật, KHÔNG bạo lực, KHÔNG nhạy cảm. Nếu kịch bản có con người, BẮT BUỘC thay thế bằng ĐỘNG VẬT DỄ THƯƠNG (chó, mèo, thỏ...) hoặc ROBOT ĐÁNG YÊU. CHỈ TẠO ẢNH, KHÔNG GIẢI THÍCH."

                page.fill(input_selector, full_prompt)
                page.keyboard.press("Enter")
                time.sleep(4)
                
                logger.info("[Adapter] Đang chờ Gemini vẽ ảnh (Có thể mất đến 3 phút)...")
                
                # GIẢI PHÁP TỐI THƯỢNG (LÀM 1 LẦN DỨT ĐIỂM): 
                # Không tìm the class hay URL nữa. Dùng JS soi toàn bộ trang web liên tục trong 3 phút.
                # Cứ thấy thẻ <img> nào render to hơn 250px (chắc chắn là ảnh AI vẽ ra, icon/avatar không bao giờ to thế này)
                # thì tóm ngay lấy cái Element đó và CHỤP ẢNH MÀN HÌNH cắt đúng cái thẻ đó lưu về.
                
                js_wait_function = '''() => {
                    const imgs = Array.from(document.querySelectorAll('img'));
                    // Đi ngược từ dưới lên để lấy bức ảnh mới nhất vừa vẽ
                    for (let i = imgs.length - 1; i >= 0; i--) {
                        const rect = imgs[i].getBoundingClientRect();
                        if (rect.width > 250 && rect.height > 150) {
                            return imgs[i];
                        }
                    }
                    return null;
                }'''
                
                try:
                    # Trình duyệt sẽ liên tục chạy hàm JS trên cho đến khi trả về Element (Tối đa 180 giây)
                    element_handle = page.wait_for_function(js_wait_function, timeout=180000)
                    
                    if element_handle and save_path:
                        logger.info("[Adapter] => AI đã vẽ xong! Đang đóng gói và lưu ảnh...")
                        element_handle.scroll_into_view_if_needed()
                        time.sleep(2) # Chờ 2 giây cho ảnh load độ phân giải cao nhất
                        
                        # Chụp đúng tọa độ của bức ảnh đó
                        element_handle.screenshot(path=save_path)
                        logger.info("[Adapter] => [THÀNH CÔNG] Đã lưu ảnh vào ổ cứng!")
                        return "saved_successfully"
                    else:
                        return ""
                except Exception as wait_err:
                    logger.error(f"[Adapter] Lỗi quá thời gian chờ ảnh xuất hiện: {wait_err}")
                    return ""
                    
            except Exception as e:
                logger.error(f"\n[LỖI VẼ ẢNH GEMINI] {e}")
                return ""
            finally:
                context.close()
