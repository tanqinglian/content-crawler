"""
解析模块测试用例
"""

import pytest


class TestParser:
    """解析模块测试类"""
    
    def test_parse_market_post(self):
        """测试解析夜市帖子"""
        # Arrange
        from src.parser import PostParser
        parser = PostParser()
        
        raw_post = {
            "title": "武汉万松园夜市探店｜人均50吃撑！",
            "desc": "📍地址：江汉区万松园路\n⏰营业时间：18:00-02:00\n💰人均：50元\n\n推荐：烤冷面、臭豆腐、烤生蚝...",
            "images": [
                "https://img1.jpg",
                "https://img2.jpg"
            ],
            "author": "吃货小王",
            "likes": 1200,
            "url": "https://www.xiaohongshu.com/explore/123"
        }
        
        # Act
        market = parser.parse_market(raw_post)
        
        # Assert
        assert market["title"] == "武汉万松园夜市探店｜人均50吃撑！"
        assert market["address"] == "江汉区万松园路"
        assert market["open_hours"] == "18:00-02:00"
        assert len(market["images"]) == 2
        assert market["author"] == "吃货小王"
        assert market["likes"] == 1200
    
    def test_parse_route_post(self):
        """测试解析跑山帖子"""
        # Arrange
        from src.parser import PostParser
        parser = PostParser()
        
        raw_post = {
            "title": "武汉周边跑山｜黄陂木兰山环线",
            "desc": "🚗路线：武汉市区→木兰山→木兰天池\n📏距离：往返150公里\n⏱️时长：4-5小时\n⛰️难度：中等\n\n路况很好，适合新手...",
            "images": ["https://img1.jpg"],
            "author": "骑行爱好者",
            "likes": 800,
            "url": "https://www.xiaohongshu.com/explore/456"
        }
        
        # Act
        route = parser.parse_route(raw_post)
        
        # Assert
        assert route["title"] == "武汉周边跑山｜黄陂木兰山环线"
        assert route["distance"] == "往返150公里"
        assert route["duration"] == "4-5小时"
        assert route["difficulty"] == "中等"
        assert route["start_point"] == "武汉市区"
        assert route["end_point"] == "木兰天池"
    
    def test_parse_images(self):
        """测试解析图片URL"""
        # Arrange
        from src.parser import PostParser
        parser = PostParser()
        
        post = {
            "images": [
                "https://img1.xiaohongshu.com/abc.jpg",
                "https://img2.xiaohongshu.com/def.jpg",
                "https://img3.xiaohongshu.com/ghi.jpg"
            ]
        }
        
        # Act
        images = parser.parse_images(post)
        
        # Assert
        assert len(images) == 3
        assert all(url.startswith("https://") for url in images)
    
    def test_parse_address_from_text(self):
        """测试从文本中提取地址"""
        # Arrange
        from src.parser import PostParser
        parser = PostParser()
        
        text = "📍地址：江汉区万松园路123号\n⏰营业时间：18:00-02:00"
        
        # Act
        address = parser.extract_address(text)
        
        # Assert
        assert address == "江汉区万松园路123号"
    
    def test_parse_open_hours_from_text(self):
        """测试从文本中提取营业时间"""
        # Arrange
        from src.parser import PostParser
        parser = PostParser()
        
        text = "📍地址：江汉区万松园路\n⏰营业时间：18:00-02:00\n💰人均：50元"
        
        # Act
        hours = parser.extract_open_hours(text)
        
        # Assert
        assert hours == "18:00-02:00"
    
    def test_parse_empty_post(self):
        """测试解析空帖子"""
        # Arrange
        from src.parser import PostParser
        parser = PostParser()
        
        # Act & Assert
        with pytest.raises(ValueError):
            parser.parse_market({})
