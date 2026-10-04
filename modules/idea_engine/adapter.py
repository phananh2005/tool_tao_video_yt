from core.contracts import AIProviderContract
from playwright.sync_api import sync_playwright
import time
import json
import re
import os

class GeminiWebAdapter(AIProviderContract):
    def __init__(self, user_data_dir="./data/chrome_profile"):
        self.user_data_dir = os.path.abspath(user_data_dir)
        
    def generate_text(self, prompt: str, expected_format: str = 'json') -> str:
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=False,
                channel="chrome"
            )
            
            page = browser.new_page()
            page.goto("https://gemini.google.com/app", timeout=60000)
            
            if expected_format == 'json':
                prompt += "\n\nCRITICAL: Return ONLY valid JSON. Do not use markdown `json ` blocks. No explanations."

            input_selector = "rich-textarea p, textarea" 
            page.wait_for_selector(input_selector, state="visible")
            page.fill(input_selector, prompt)
            
            page.keyboard.press("Enter")
            
            time.sleep(3)
            
            response_selector = "message-content"
            page.wait_for_selector(response_selector, timeout=90000)
            
            try:
                page.wait_for_selector("button[aria-label='Copy']", timeout=60000)
            except:
                pass # Fallback if Copy button takes too long or UI changes
            
            responses = page.query_selector_all(response_selector)
            latest_response = responses[-1].inner_text()
            
            browser.close()
            
            if expected_format == 'json':
                return self._extract_json(latest_response)
                
            return latest_response

    def _extract_json(self, text):
        text = re.sub(r'`(?:json)?', '', text).strip()
        try:
            parsed = json.loads(text)
            return json.dumps(parsed)
        except json.JSONDecodeError:
            return text

    def generate_image(self, prompt: str) -> str:
        return ""
