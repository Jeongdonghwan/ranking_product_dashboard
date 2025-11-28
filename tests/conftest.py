"""
Pytest configuration for ad dashboard tests
"""

import pytest
import os
import sys
import json
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 환경 변수에서 BASE_URL 가져오기 (기본값: 8080 포트)
BASE_URL = os.environ.get("TEST_BASE_URL", "http://127.0.0.1:8080")


@pytest.fixture(scope="session")
def base_url():
    """테스트 서버 URL"""
    return BASE_URL


@pytest.fixture(scope="session")
def dashboard_url(base_url):
    """대시보드 URL"""
    return f"{base_url}/ad-dashboard"


@pytest.fixture(scope="session")
def test_data():
    """14일치 테스트 데이터 로드"""
    fixtures_path = Path(__file__).parent / "fixtures" / "test_data_14days.json"
    if fixtures_path.exists():
        with open(fixtures_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


@pytest.fixture(scope="session")
def browser_context():
    """Playwright 브라우저 컨텍스트"""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='ko-KR'
        )
        yield context
        context.close()
        browser.close()


@pytest.fixture
def page(browser_context):
    """새 페이지 생성"""
    page = browser_context.new_page()
    yield page
    page.close()


@pytest.fixture
def page_with_data(page, test_data, dashboard_url):
    """테스트 데이터가 localStorage에 주입된 페이지"""
    page.goto(dashboard_url)
    page.wait_for_load_state('networkidle')

    # localStorage에 테스트 데이터 주입
    page.evaluate(f"""
        localStorage.setItem('ad_dashboard_accumulated_data',
            JSON.stringify({json.dumps(test_data)}));
    """)

    # 페이지 리로드하여 데이터 적용
    page.reload()
    page.wait_for_load_state('networkidle')

    return page


@pytest.fixture
def clean_page(page, dashboard_url):
    """localStorage가 비워진 깨끗한 페이지"""
    page.goto(dashboard_url)
    page.wait_for_load_state('networkidle')

    # localStorage 비우기
    page.evaluate("localStorage.removeItem('ad_dashboard_accumulated_data');")
    page.reload()
    page.wait_for_load_state('networkidle')

    return page
