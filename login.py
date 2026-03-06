"""
小红书登录脚本
扫码登录并保存cookies
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


async def login():
    print("=" * 60)
    print("  小红书登录")
    print("=" * 60)
    
    async with async_playwright() as p:
        # 启动浏览器（非无头模式，显示界面）
        print("\n[STEP 1] 启动浏览器...")
        browser = await p.chromium.launch(
            headless=False,  # 显示浏览器界面
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
        
        # 访问小红书首页
        print("[STEP 2] 访问小红书首页...")
        await page.goto("https://www.xiaohongshu.com/", wait_until='networkidle')
        await page.wait_for_timeout(2000)
        
        print("\n" + "=" * 60)
        print("  请在浏览器中扫码登录")
        print("  登录成功后，此脚本会自动保存cookies")
        print("  等待登录中...")
        print("=" * 60)
        
        # 等待登录成功（检测登录状态变化）
        max_wait = 600  # 最多等待10分钟
        logged_in = False
        
        print("\n[提示] 请在浏览器窗口中完成以下操作：")
        print("  1. 点击页面上的'登录'按钮")
        print("  2. 使用微信或小红书APP扫码")
        print("  3. 完成登录后，此窗口会自动继续")
        print("")
        
        for i in range(max_wait):
            await page.wait_for_timeout(1000)
            
            # 检查URL变化 - 登录后通常会跳转
            current_url = page.url
            
            # 检查cookies中是否有登录标识
            cookies = await context.cookies()
            has_session = any(c['name'] in ['web_session', 'a1', 'webId'] for c in cookies)
            
            if has_session:
                # 额外检查：访问搜索页面确认登录
                if (i + 1) % 30 == 0:  # 每30秒检查一次
                    try:
                        await page.goto("https://www.xiaohongshu.com/search_result?keyword=test", timeout=10000)
                        await page.wait_for_timeout(2000)
                        title = await page.title()
                        if "安全限制" not in title and "登录" not in title:
                            logged_in = True
                            print(f"\n[OK] 检测到登录成功！(等待了 {i+1} 秒)")
                            break
                    except:
                        pass
            
            # 每30秒提示一次
            if (i + 1) % 30 == 0:
                print(f"[INFO] 已等待 {i+1} 秒，继续等待登录...")
        
        if logged_in:
            # 保存cookies
            print("\n[STEP 3] 保存Cookies...")
            cookies = await context.cookies()
            
            # 确保目录存在
            Path("data").mkdir(exist_ok=True)
            
            # 保存到文件
            with open("data/cookies.json", 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            
            print(f"[OK] Cookies已保存到 data/cookies.json")
            print(f"[OK] 共保存 {len(cookies)} 个cookies")
            
            # 直接测试搜索 - 不关闭浏览器
            print("\n[STEP 4] 测试搜索功能...")
            await page.goto("https://www.xiaohongshu.com/search_result?keyword=武汉夜市", wait_until='networkidle')
            await page.wait_for_timeout(5000)
            
            title = await page.title()
            print(f"[OK] 搜索页标题: {title}")
            
            # 截图
            await page.screenshot(path="data/search_test.png")
            print("[OK] 搜索截图保存到 data/search_test.png")
            
            # 尝试提取搜索结果
            posts = await page.evaluate("""
                () => {
                    const results = [];
                    const links = document.querySelectorAll('a[href*="/explore/"]');
                    links.forEach(link => {
                        const href = link.href;
                        if (href && href.includes('/explore/')) {
                            results.push(href);
                        }
                    });
                    return results;
                }
            """)
            
            print(f"[INFO] 找到 {len(posts)} 个帖子链接")
            
            if len(posts) > 0:
                print("\n" + "=" * 60)
                print("  [SUCCESS] 爬虫可以正常工作！")
                print("=" * 60)
            else:
                print("\n[WARN] 未找到搜索结果，可能需要额外验证")
                print("[INFO] 保持浏览器打开30秒，您可以手动检查...")
                await page.wait_for_timeout(30000)
            
            print("\n" + "=" * 60)
            print("  登录成功！可以运行爬虫了")
            print("=" * 60)
        else:
            print("\n[ERROR] 登录超时，请重新运行脚本")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(login())
