"""
搜索模块测试用例
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock


class TestSearch:
    """搜索模块测试类"""
    
    @pytest.mark.asyncio
    async def test_search_keyword_success(self):
        """测试关键词搜索成功"""
        # Arrange
        from src.search import SearchEngine
        engine = SearchEngine()
        
        # Mock 浏览器上下文
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.wait_for_selector = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value=[
            {
                "title": "武汉夜市推荐",
                "url": "https://www.xiaohongshu.com/explore/123",
                "author": "测试用户",
                "likes": 100
            }
        ])
        
        # Act
        results = await engine.search(mock_page, "武汉夜市", max_pages=1)
        
        # Assert
        assert len(results) > 0
        assert results[0]["title"] == "武汉夜市推荐"
    
    @pytest.mark.asyncio
    async def test_search_pagination(self):
        """测试分页搜索"""
        # Arrange
        from src.search import SearchEngine
        engine = SearchEngine()
        
        mock_page = AsyncMock()
        
        # 模拟两页数据
        mock_page.evaluate = AsyncMock(side_effect=[
            [{"title": f"帖子{i}"} for i in range(20)],  # 第一页
            [{"title": f"帖子{i}"} for i in range(20, 40)],  # 第二页
        ])
        
        # Act
        results = await engine.search(mock_page, "武汉夜市", max_pages=2)
        
        # Assert
        assert len(results) == 40
    
    @pytest.mark.asyncio
    async def test_search_empty_keyword(self):
        """测试空关键词抛出异常"""
        # Arrange
        from src.search import SearchEngine
        engine = SearchEngine()
        mock_page = AsyncMock()
        
        # Act & Assert
        with pytest.raises(ValueError, match="关键词不能为空"):
            await engine.search(mock_page, "", max_pages=1)
    
    @pytest.mark.asyncio
    async def test_search_no_results(self):
        """测试无搜索结果"""
        # Arrange
        from src.search import SearchEngine
        engine = SearchEngine()
        
        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value=[])
        
        # Act
        results = await engine.search(mock_page, "不存在的关键词xyz123", max_pages=1)
        
        # Assert
        assert len(results) == 0
