"""
在搜索页面直接登录
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


async def login_and_search():
    print("=" * 60)
    print("  小红书搜索页面登录")
    print("=" * 60)
    
    async with async_playwright() as p:
        print("\n[STEP 1] 启动浏览器...")
        browser = await p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            locale='zh-CN',
        )
        
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        # 直接访问搜索页面
        print("[STEP 2] 访问搜索页面...")
        await page.goto("https://www.xiaohongshu.com/search_result?keyword=武汉夜市", wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        print(f"[OK] 页面标题: {await page.title()}")
        
        print("\n" + "=" * 60)
        print("  请在浏览器中扫码登录（搜索页面上的登录弹窗）")
        print("  登录成功后，此脚本会自动检测并开始爬取")
        print("=" * 60)
        
        # 等待登录成功
        max_wait = 300  # 5分钟
        logged_in = False
        
        for i in range(max_wait):
            await page.wait_for_timeout(1000)
            
            # 检查是否还有登录弹窗
            login_modal = await page.query_selector('[class*="login-modal"], [class*="loginModal"]')
            login_btn = await page.query_selector('text=登录后查看')
            
            if not login_modal and not login_btn:
                # 尝试提取搜索结果
                posts = await page.query_selector_all('a[href*="/explore/"]')
                if len(posts) > 0:
                    logged_in = True
                    print(f"\n[OK] 登录成功！找到 {len(posts)} 个帖子 (等待了 {i+1} 秒)")
                    break
            
            if (i + 1) % 30 == 0:
                print(f"[INFO] 已等待 {i+1} 秒...")
        
        if logged_in:
            # 保存cookies
            print("\n[STEP 3] 保存Cookies...")
            cookies = await context.cookies()
            
            Path("data").mkdir(exist_ok=True)
            with open("data/cookies.json", 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            
            print(f"[OK] Cookies已保存 ({len(cookies)} 个)")
            
            # 提取帖子数据
            print("\n[STEP 4] 提取帖子数据...")
            
            posts_data = await page.evaluate("""
                () => {
                    const results = [];
                    const links = document.querySelectorAll('a[href*="/explore/"]');
                    
                    links.forEach(link => {
                        try {
                            const href = link.href;
                            const parent = link.closest('[class*="note"], [class*="card"], [class*="item"]');
                            const title = parent ? parent.innerText : link.innerText;
                            
                            if (href && href.includes('/explore/')) {
                                results.push({
                                    url: href,
                                    title: title ? title.substring(0, 100) : ''
                                });
                            }
                        } catch (e) {}
                    });
                    
                    return results;
                }
            """)
            
            print(f"[OK] 提取到 {len(posts_data)} 条帖子")
            
            # 保存数据
            with open("data/search_results_new.json", 'w', encoding='utf-8') as f:
                json.dump(posts_data, f, ensure_ascii=False, indent=2)
            print("[OK] 数据保存到 data/search_results_new.json")
            
            # 截图
            await page.screenshot(path="data/search_success.png", full_page=True)
            print("[OK] 截图保存到 data/search_success.png")
            
            print("\n" + "=" * 60)
            print("  [SUCCESS] 爬虫可以正常工作！")
            print("  现在可以运行 main.py 进行完整爬取")
            print("=" * 60)
        else:
            print("\n[ERROR] 登录超时")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(login_and_search())
