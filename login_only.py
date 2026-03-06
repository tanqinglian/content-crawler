# -*- coding: utf-8 -*-
"""
小红书爬虫 - 带截图功能
"""

import asyncio
import sys
import os
from pathlib import Path

# 禁用代理
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['NO_PROXY'] = '*'

sys.path.insert(0, str(Path(__file__).parent))

from playwright.async_api import async_playwright
from src.login import CookieManager, LoginManager
from src.search import SearchEngine
from src.parser import PostParser
from src.storage import Database


async def main():
    """主函数 - 仅登录和截图"""
    
    print("=" * 60)
    print("  小红书爬虫 - 登录模式")
    print("=" * 60)
    
    cookie_manager = CookieManager("data/cookies.json")
    
    async with async_playwright() as p:
        # 启动浏览器（非headless，显示界面，禁用代理）
        print("\n启动浏览器...")
        browser = await p.chromium.launch(
            headless=False,
            proxy={"server": "direct://"}
        )
        context = await browser.new_context()
        page = await context.new_page()
        
        # 访问小红书
        print("访问小红书...")
        await page.goto("https://www.xiaohongshu.com/")
        await page.wait_for_timeout(3000)
        
        # 截图保存
        screenshot_path = "data/login_screenshot.png"
        await page.screenshot(path=screenshot_path)
        print(f"\n截图已保存: {screenshot_path}")
        
        # 等待用户扫码登录（最多5分钟）
        print("\n等待扫码登录...")
        print("请在浏览器窗口中扫码登录")
        print("登录成功后，程序会自动保存cookies")
        
        # 检测登录状态（每5秒检查一次）
        for i in range(60):  # 最多等待5分钟
            await page.wait_for_timeout(5000)
            
            # 尝试检测登录状态
            try:
                # 检查是否有用户信息元素
                user_info = await page.query_selector('[class*="user"], [class*="avatar"]')
                if user_info:
                    print("\n检测到登录成功！")
                    # 保存cookies
                    cookies = await context.cookies()
                    cookie_manager.save_cookies(cookies)
                    print("Cookies已保存")
                    break
            except:
                pass
            
            print(f"等待中... ({i+1}/60)")
        
        await browser.close()
        print("\n完成！")


if __name__ == "__main__":
    asyncio.run(main())
