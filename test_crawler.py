"""
测试爬虫诊断脚本
"""
import asyncio
import sys
import os
from pathlib import Path

# 禁用代理
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['NO_PROXY'] = '*'

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent))

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def test_login():
    """测试登录状态"""
    print("=" * 60)
    print("  爬虫诊断测试 (带Stealth)")
    print("=" * 60)
    
    # 检查cookies文件
    cookies_path = Path("data/cookies.json")
    cookies_list = None
    if cookies_path.exists():
        print(f"[OK] Cookies文件存在: {cookies_path}")
        import json
        with open(cookies_path, 'r', encoding='utf-8') as f:
            cookies_data = json.load(f)
        # 兼容两种格式
        if isinstance(cookies_data, dict) and 'value' in cookies_data:
            cookies_list = cookies_data['value']
        elif isinstance(cookies_data, list):
            cookies_list = cookies_data
        else:
            cookies_list = []
        print(f"[OK] Cookies数量: {len(cookies_list)}")
    else:
        print(f"[ERROR] Cookies文件不存在")
        return
    
    async with async_playwright() as p:
        print("\n[STEP 1] 启动浏览器 (带Stealth)...")
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
            ]
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            locale='zh-CN',
        )
        
        # 加载cookies
        print("[STEP 2] 加载Cookies...")
        if cookies_list:
            await context.add_cookies(cookies_list)
        
        page = await context.new_page()
        
        # 应用stealth
        print("[STEP 2.5] 应用Stealth...")
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        # 访问小红书
        print("[STEP 3] 访问小红书首页...")
        try:
            await page.goto("https://www.xiaohongshu.com/", timeout=30000, wait_until='networkidle')
            await page.wait_for_timeout(3000)
            title = await page.title()
            print(f"[OK] 页面标题: {title}")
            
            if "安全限制" in title:
                print("[ERROR] 仍然被安全限制！")
            else:
                print("[OK] 未检测到安全限制")
        except Exception as e:
            print(f"[ERROR] 访问失败: {e}")
            await browser.close()
            return
        
        # 检查登录状态
        print("[STEP 4] 检查登录状态...")
        try:
            # 检查是否有登录按钮（未登录状态）
            login_btn = await page.query_selector('text=登录')
            if login_btn:
                print("[WARN] 检测到登录按钮，可能未登录")
            else:
                print("[OK] 未检测到登录按钮，可能已登录")
            
            # 检查用户头像（已登录状态）
            avatar = await page.query_selector('.user-info, .avatar, [class*="avatar"]')
            if avatar:
                print("[OK] 检测到用户头像，已登录")
            else:
                print("[WARN] 未检测到用户头像")
                
        except Exception as e:
            print(f"[ERROR] 检查登录状态失败: {e}")
        
        # 测试搜索
        print("\n[STEP 5] 测试搜索功能...")
        try:
            # 访问搜索页面
            search_url = "https://www.xiaohongshu.com/search_result?keyword=武汉夜市"
            await page.goto(search_url, timeout=30000, wait_until='networkidle')
            await page.wait_for_timeout(3000)
            print(f"[OK] 搜索页面标题: {await page.title()}")
            
            # 等待搜索结果
            await page.wait_for_selector('.note-item, [class*="note"]', timeout=10000)
            notes = await page.query_selector_all('.note-item, [class*="note"]')
            print(f"[OK] 找到 {len(notes)} 条搜索结果")
            
        except Exception as e:
            print(f"[ERROR] 搜索测试失败: {e}")
        
        await browser.close()
        print("\n" + "=" * 60)
        print("  诊断完成")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_login())
