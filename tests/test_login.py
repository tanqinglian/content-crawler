"""
登录模块测试用例
TDD: 先写测试，再实现功能
"""

import pytest
import os
import json
from pathlib import Path


class TestLogin:
    """登录模块测试类"""
    
    def test_save_cookies(self, tmp_path):
        """测试保存cookies到文件"""
        # Arrange
        from src.login import CookieManager
        cookie_manager = CookieManager(str(tmp_path / "cookies.json"))
        test_cookies = [
            {"name": "session", "value": "test123", "domain": ".xiaohongshu.com"}
        ]
        
        # Act
        cookie_manager.save_cookies(test_cookies)
        
        # Assert
        cookie_file = tmp_path / "cookies.json"
        assert cookie_file.exists()
        
        with open(cookie_file, 'r') as f:
            saved_cookies = json.load(f)
        assert saved_cookies == test_cookies
    
    def test_load_cookies(self, tmp_path):
        """测试从文件加载cookies"""
        # Arrange
        from src.login import CookieManager
        cookie_manager = CookieManager(str(tmp_path / "cookies.json"))
        test_cookies = [
            {"name": "session", "value": "test123", "domain": ".xiaohongshu.com"}
        ]
        
        # 先保存
        cookie_manager.save_cookies(test_cookies)
        
        # Act
        loaded_cookies = cookie_manager.load_cookies()
        
        # Assert
        assert loaded_cookies == test_cookies
    
    def test_load_cookies_not_exist(self, tmp_path):
        """测试加载不存在的cookies文件"""
        # Arrange
        from src.login import CookieManager
        cookie_manager = CookieManager(str(tmp_path / "not_exist.json"))
        
        # Act
        loaded_cookies = cookie_manager.load_cookies()
        
        # Assert
        assert loaded_cookies is None
    
    def test_is_logged_in_with_valid_cookies(self, tmp_path):
        """测试有效cookies的登录状态检测"""
        # Arrange
        from src.login import CookieManager
        cookie_manager = CookieManager(str(tmp_path / "cookies.json"))
        valid_cookies = [
            {"name": "web_session", "value": "valid_token", "domain": ".xiaohongshu.com"}
        ]
        cookie_manager.save_cookies(valid_cookies)
        
        # Act
        is_logged = cookie_manager.is_logged_in()
        
        # Assert
        assert is_logged is True
    
    def test_is_logged_in_without_cookies(self, tmp_path):
        """测试无cookies的登录状态检测"""
        # Arrange
        from src.login import CookieManager
        cookie_manager = CookieManager(str(tmp_path / "not_exist.json"))
        
        # Act
        is_logged = cookie_manager.is_logged_in()
        
        # Assert
        assert is_logged is False
