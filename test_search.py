"""
测试搜索页面结构
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

async def test_search():
    print("=" * 60)
    print("  搜索页面结构测试")
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
        browser = await p.chromium.launch(
            headless=True,
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
        
        # 访问搜索页面
        print("\n[STEP] 访问搜索页面...")
        search_url = "https://www.xiaohongshu.com/search_result?keyword=武汉夜市"
        await page.goto(search_url, timeout=30000, wait_until='networkidle')
        await page.wait_for_timeout(5000)  # 等待更长时间
        
        print(f"[OK] 页面标题: {await page.title()}")
        
        # 截图
        await page.screenshot(path="data/search_screenshot.png")
        print("[OK] 截图保存: data/search_screenshot.png")
        
        # 检查页面结构
        print("\n[STEP] 检查页面结构...")
        
        # 获取页面HTML
        html = await page.content()
        print(f"[INFO] HTML长度: {len(html)} 字符")
        
        # 尝试多种选择器
        selectors = [
            '.note-item',
            '[class*="note-item"]',
            '[class*="search-result"]',
            'section a[href*="/explore/"]',
            'a[href*="/explore/"]',
            '[class*="feeds"] a',
            '[class*="card"]',
        ]
        
        for selector in selectors:
            elements = await page.query_selector_all(selector)
            print(f"[INFO] 选择器 '{selector}': {len(elements)} 个元素")
        
        # 使用JavaScript提取
        print("\n[STEP] JavaScript提取...")
        posts = await page.evaluate("""
            () => {
                const results = [];
                
                // 尝试找到所有链接
                const links = document.querySelectorAll('a[href*="/explore/"]');
                console.log('Found ' + links.length + ' explore links');
                
                links.forEach((link, i) => {
                    const parent = link.closest('[class*="note"], [class*="card"], [class*="item"]');
                    const text = parent ? parent.innerText : link.innerText;
                    const href = link.href;
                    
                    if (href && href.includes('/explore/')) {
                        results.push({
                            index: i,
                            href: href,
                            text: text ? text.substring(0, 100) : ''
                        });
                    }
                });
                
                return results;
            }
        """)
        
        print(f"[OK] 找到 {len(posts)} 个帖子链接")
        for post in posts[:5]:
            print(f"  - {post['href']}: {post['text'][:50]}...")
        
        await browser.close()
        print("\n" + "=" * 60)
        print("  测试完成")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_search())
