"""
登录模块
负责管理小红书的登录状态和cookies
"""

import json
import os
from pathlib import Path
from typing import Optional, List, Dict


class CookieManager:
    """Cookies管理器"""
    
    def __init__(self, cookie_file: str = "data/cookies.json"):
        """
        初始化
        
        Args:
            cookie_file: cookies存储文件路径
        """
        self.cookie_file = Path(cookie_file)
        self.cookie_file.parent.mkdir(parents=True, exist_ok=True)
    
    def save_cookies(self, cookies: List[Dict]) -> None:
        """
        保存cookies到文件
        
        Args:
            cookies: cookies列表
        """
        with open(self.cookie_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
    
    def load_cookies(self) -> Optional[List[Dict]]:
        """
        从文件加载cookies
        
        Returns:
            cookies列表，如果文件不存在则返回None
        """
        if not self.cookie_file.exists():
            return None
        
        with open(self.cookie_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def is_logged_in(self) -> bool:
        """
        检查是否已登录
        
        Returns:
            是否已登录
        """
        cookies = self.load_cookies()
        if not cookies:
            return False
        
        # 检查是否有关键的登录cookie
        required_cookies = ["web_session", "webId", "a1"]
        cookie_names = [c.get("name") for c in cookies]
        
        return any(name in cookie_names for name in required_cookies)
    
    def clear_cookies(self) -> None:
        """清除cookies文件"""
        if self.cookie_file.exists():
            self.cookie_file.unlink()


class LoginManager:
    """登录管理器"""
    
    def __init__(self, browser_context, cookie_manager: CookieManager):
        """
        初始化
        
        Args:
            browser_context: Playwright浏览器上下文
            cookie_manager: cookies管理器
        """
        self.context = browser_context
        self.cookie_manager = cookie_manager
    
    async def login_with_qrcode(self, page) -> bool:
        """
        扫码登录
        
        Args:
            page: Playwright页面对象
            
        Returns:
            是否登录成功
        """
        # 访问小红书登录页
        await page.goto("https://www.xiaohongshu.com/")
        
        # 检查是否已登录
        if await self._check_login_status(page):
            print("✅ 已登录")
            await self._save_cookies()
            return True
        
        # 等待用户扫码登录
        print("📱 请在小红书页面扫码登录...")
        
        # 等待登录成功（检测登录状态变化）
        max_wait = 120  # 最多等待2分钟
        for i in range(max_wait):
            await page.wait_for_timeout(1000)
            if await self._check_login_status(page):
                print("✅ 登录成功")
                await self._save_cookies()
                return True
        
        print("❌ 登录超时")
        return False
    
    async def _check_login_status(self, page) -> bool:
        """
        检查页面登录状态
        
        Args:
            page: Playwright页面对象
            
        Returns:
            是否已登录
        """
        try:
            # 检查是否有用户头像或用户名元素
            user_element = await page.query_selector('.user-info, .avatar, [class*="user"]')
            return user_element is not None
        except:
            return False
    
    async def _save_cookies(self) -> None:
        """保存当前上下文的cookies"""
        cookies = await self.context.cookies()
        self.cookie_manager.save_cookies(cookies)
    
    async def load_cookies(self) -> bool:
        """
        加载cookies到浏览器上下文
        
        Returns:
            是否加载成功
        """
        cookies = self.cookie_manager.load_cookies()
        if cookies:
            await self.context.add_cookies(cookies)
            return True
        return False
