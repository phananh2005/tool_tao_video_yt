import pytest
import sys
import os
import re
from html.parser import HTMLParser

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

HTML_PATH = os.path.join(os.path.dirname(__file__), '..', 'web', 'index.html')


@pytest.fixture
def html_content():
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        return f.read()


# ---------- HTML Tag Balance Check ----------

class TagBalanceChecker(HTMLParser):
    VOID_ELEMENTS = frozenset([
        'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
        'link', 'meta', 'param', 'source', 'track', 'wbr',
    ])

    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag not in self.VOID_ELEMENTS:
            self.stack.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in self.VOID_ELEMENTS:
            return
        if not self.stack:
            self.errors.append(f"Unexpected closing tag </{tag}> at line {self.getpos()[0]}")
            return
        expected_tag, pos = self.stack[-1]
        if expected_tag == tag:
            self.stack.pop()
        else:
            self.errors.append(
                f"Mismatched tag: expected </{expected_tag}> (opened at line {pos[0]}) "
                f"but got </{tag}> at line {self.getpos()[0]}"
            )


def test_html_tags_balanced(html_content):
    checker = TagBalanceChecker()
    checker.feed(html_content)
    unclosed = [f"<{t}> opened at line {p[0]}" for t, p in checker.stack]
    all_errors = checker.errors + [f"Unclosed: {u}" for u in unclosed]
    assert len(all_errors) == 0, f"HTML tag errors:\n" + "\n".join(all_errors)


# ---------- Vue Directives Smoke Test ----------

def test_vue_directives_present(html_content):
    directives = ['v-if', 'v-for', 'v-model', '@click']
    for directive in directives:
        assert directive in html_content, f"Vue directive '{directive}' not found in index.html"


# ---------- Fetch Error Handling ----------

def test_fetch_calls_have_error_handling(html_content):
    script_match = re.search(r'<script>(.*?)</script>', html_content, re.DOTALL)
    assert script_match, "No <script> block found in index.html"
    script_block = script_match.group(1)

    fetch_pattern = re.compile(r'\bfetch\s*\(')
    fetch_positions = [m.start() for m in fetch_pattern.finditer(script_block)]

    if not fetch_positions:
        pytest.skip("No fetch() calls found — nothing to check")

    for pos in fetch_positions:
        context_before = script_block[max(0, pos - 200):pos]
        context_after = script_block[pos:pos + 500]
        has_try = 'try' in context_before or 'try' in context_after[:50]
        has_catch = '.catch' in context_after or 'catch' in context_after
        has_error_handling = has_try or has_catch
        assert has_error_handling, (
            f"fetch() call at char {pos} appears to lack try/catch or .catch() error handling"
        )


# ---------- API Endpoints Consistency ----------

def test_api_endpoints_referenced(html_content):
    expected_endpoints = [
        '/api/dashboard',
        '/api/phase1/brainstorm',
        '/api/phase2/generate/',
        '/api/phase3/generate/',
        '/api/phase4/generate/',
        '/api/phase5/render/',
        '/api/phase6/generate/',
    ]
    for ep in expected_endpoints:
        assert ep in html_content, f"Expected API endpoint '{ep}' not referenced in frontend"
