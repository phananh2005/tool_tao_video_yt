from core.contracts import AIProviderContract
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
            print("\n[HỆ THỐNG] Đang mở Chrome Tự Động...")
            
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=False,
                channel="chrome",
                args=[
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled"
                ],
                no_viewport=True
            )
            
            page = context.pages[0] if context.pages else context.new_page()
            page.goto("https://gemini.google.com/app", timeout=90000)
            
            input_selector = "rich-textarea p, textarea, div[contenteditable='true']" 
            
            # KIỂM TRA ĐĂNG NHẬP HOẶC LOAD CHẬM
            print("[HỆ THỐNG] Đang chờ giao diện Gemini tải lên...")
            try:
                # Chờ tối đa 10 giây xem ô chat có xuất hiện không
                page.wait_for_selector(input_selector, state="visible", timeout=10000)
            except:
                # Nếu sau 10 giây không thấy ô chat, giả định là chưa đăng nhập
                print("\n" + "="*65)
                print("⚠️ YÊU CẦU ĐĂNG NHẬP / XÁC NHẬN ⚠️")
                print("Tool không tìm thấy ô nhập liệu (Có thể bạn cần đăng nhập).")
                print("1. Vui lòng bấm vào đăng nhập tài khoản Google trên Chrome.")
                print("2. Chờ màn hình load xong và nhìn thấy giao diện chat của Gemini.")
                print("=> SAU KHI THẤY Ô CHAT, HÃY QUAY LẠI ĐÂY VÀ NHẤN ENTER ĐỂ TIẾP TỤC...")
                print("="*65 + "\n")
                input() # Dừng lại chờ người dùng nhấn Enter
            
            if expected_format == 'json':
                prompt += "\n\nCRITICAL: Return ONLY valid JSON format. Do not use markdown `json ` blocks. No explanations. Return as an array of objects."

            try:
                print("[HỆ THỐNG] Đang gõ prompt vào Gemini...")
                # Lần này chờ ô chat với thời gian lâu hơn (60s) để chắc chắn sau khi user nhấn Enter
                page.wait_for_selector(input_selector, state="visible", timeout=60000)
                page.fill(input_selector, prompt)
                
                page.keyboard.press("Enter")
                time.sleep(4)
                
                print("[HỆ THỐNG] Đang chờ AI trả kết quả (Vui lòng không bấm chuột)...")
                response_selector = "message-content"
                page.wait_for_selector(response_selector, timeout=90000)
                
                try:
                    page.wait_for_selector("button[aria-label='Copy'], button[data-test-id='copy-button']", timeout=90000)
                except:
                    pass
                
                responses = page.query_selector_all(response_selector)
                latest_response = responses[-1].inner_text()
            except Exception as e:
                print(f"\n[LỖI KHI TƯƠNG TÁC GEMINI] {e}")
                latest_response = ""
            finally:
                context.close()
            
            if expected_format == 'json' and latest_response:
                return self._extract_json(latest_response)
                
            return latest_response

    def _extract_json(self, text):
        text = re.sub(r'`(?:json)?', '', text).strip()
        try:
            parsed = json.loads(text)
            return json.dumps(parsed)
        except json.JSONDecodeError:
            print("\n[CẢNH BÁO] Gemini không trả về JSON chuẩn, đang trả về raw text.")
            return text

    def generate_image(self, prompt: str) -> str:
        return ""
