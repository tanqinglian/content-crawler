"""
测试搜索 - 非无头模式
"""
import asyncio
import sys
import os
from pathlib import Path

os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['NO_PROXY'] = '*'

sys.path.insert(0, str(Path(__file__).parent))

from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import json

async def test():
    print("=" * 60)
    print("  搜索测试 (非无头模式)")
    print("=" * 60)
    
    # 加载cookies
    cookies_path = Path("data/cookies.json")
    cookies_list = None
    if cookies_path.exists():
        with open(cookies_path, 'r', encoding='utf-8') as f:
            cookies_data = json.load(f)
        if isinstance(cookies_data, dict) and 'value' in cookies_data:
            cookies_list = cookies_data['value']
        elif isinstance(cookies_data, list):
            cookies_list = cookies_data
        print(f"[OK] Cookies数量: {len(cookies_list) if cookies_list else 0}")
    
    async with async_playwright() as p:
        print("\n[STEP] 启动浏览器 (非无头模式)...")
        browser = await p.chromium.launch(
            headless=False,  # 显示浏览器
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            locale='zh-CN',
        )
        
        if cookies_list:
            await context.add_cookies(cookies_list)
        
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        # 先访问首页
        print("[STEP] 访问首页...")
        await page.goto("https://www.xiaohongshu.com/", wait_until='networkidle')
        await page.wait_for_timeout(3000)
        print(f"[OK] 首页标题: {await page.title()}")
        
        # 访问搜索页面
        print("\n[STEP] 访问搜索页面...")
        search_url = "https://www.xiaohongshu.com/search_result?keyword=武汉夜市"
        await page.goto(search_url, wait_until='networkidle')
        await page.wait_for_timeout(5000)
        
        title = await page.title()
        print(f"[OK] 搜索页标题: {title}")
        
        # 截图
        await page.screenshot(path="data/search_visible.png", full_page=True)
        print("[OK] 截图保存: data/search_visible.png")
        
        # 检查是否有搜索结果
        print("\n[STEP] 检查搜索结果...")
        
        # 等待更长时间让页面加载
        await page.wait_for_timeout(5000)
        
        # 尝试滚动页面触发加载
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(3000)
        
        # 检查各种选择器
        selectors = [
            'a[href*="/explore/"]',
            '[class*="note"]',
            '[class*="card"]',
            '[class*="item"]',
        ]
        
        for selector in selectors:
            elements = await page.query_selector_all(selector)
            if elements:
                print(f"[INFO] 选择器 '{selector}': {len(elements)} 个元素")
        
        # 获取页面内容
        html = await page.content()
        print(f"[INFO] HTML长度: {len(html)}")
        
        print("\n[INFO] 请在浏览器中查看搜索结果...")
        print("[INFO] 等待30秒后关闭...")
        await page.wait_for_timeout(30000)
        
        await browser.close()
        print("\n" + "=" * 60)
        print("  测试完成")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test())
