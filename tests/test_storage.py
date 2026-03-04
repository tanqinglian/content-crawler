"""
存储模块测试用例
"""

import pytest
import sqlite3
import os
from pathlib import Path


class TestStorage:
    """存储模块测试类"""
    
    @pytest.fixture
    def temp_db(self, tmp_path):
        """临时数据库fixture"""
        db_path = str(tmp_path / "test.db")
        from src.storage import Database
        db = Database(db_path)
        db.init_tables()
        yield db
        # 清理
        if os.path.exists(db_path):
            os.remove(db_path)
    
    def test_save_market(self, temp_db):
        """测试保存夜市数据"""
        # Arrange
        market = {
            "title": "万松园夜市",
            "content": "推荐小吃很多",
            "address": "江汉区万松园路",
            "open_hours": "18:00-02:00",
            "images": '["img1.jpg", "img2.jpg"]',
            "author": "吃货小王",
            "likes": 1200,
            "source_url": "https://www.xiaohongshu.com/explore/123"
        }
        
        # Act
        market_id = temp_db.save_market(market)
        
        # Assert
        assert market_id > 0
        
        # 验证保存成功
        saved = temp_db.get_market(market_id)
        assert saved["title"] == "万松园夜市"
        assert saved["address"] == "江汉区万松园路"
    
    def test_save_route(self, temp_db):
        """测试保存跑山数据"""
        # Arrange
        route = {
            "title": "木兰山环线",
            "content": "路况很好",
            "distance": "150公里",
            "duration": "4-5小时",
            "difficulty": "中等",
            "start_point": "武汉市区",
            "end_point": "木兰天池",
            "images": '["img1.jpg"]',
            "author": "骑行爱好者",
            "likes": 800,
            "source_url": "https://www.xiaohongshu.com/explore/456"
        }
        
        # Act
        route_id = temp_db.save_route(route)
        
        # Assert
        assert route_id > 0
        
        saved = temp_db.get_route(route_id)
        assert saved["title"] == "木兰山环线"
        assert saved["distance"] == "150公里"
    
    def test_avoid_duplicates(self, temp_db):
        """测试去重：相同source_url应更新而非重复插入"""
        # Arrange
        market1 = {
            "title": "万松园夜市",
            "address": "江汉区万松园路",
            "source_url": "https://www.xiaohongshu.com/explore/123",
            "likes": 1000
        }
        
        market2 = {
            "title": "万松园夜市（更新）",
            "address": "江汉区万松园路123号",
            "source_url": "https://www.xiaohongshu.com/explore/123",  # 相同URL
            "likes": 1200
        }
        
        # Act
        id1 = temp_db.save_market(market1)
        id2 = temp_db.save_market(market2)
        
        # Assert
        assert id1 == id2  # 应该是同一条记录
        
        # 验证数据已更新
        saved = temp_db.get_market(id1)
        assert saved["title"] == "万松园夜市（更新）"
        assert saved["likes"] == 1200
    
    def test_query_markets(self, temp_db):
        """测试查询夜市数据"""
        # Arrange
        temp_db.save_market({
            "title": "夜市A",
            "address": "地址A",
            "source_url": "url1"
        })
        temp_db.save_market({
            "title": "夜市B",
            "address": "地址B",
            "source_url": "url2"
        })
        
        # Act
        markets = temp_db.query_markets()
        
        # Assert
        assert len(markets) == 2
        assert markets[0]["title"] in ["夜市A", "夜市B"]
    
    def test_query_routes(self, temp_db):
        """测试查询跑山数据"""
        # Arrange
        temp_db.save_route({
            "title": "路线A",
            "distance": "100公里",
            "source_url": "url1"
        })
        temp_db.save_route({
            "title": "路线B",
            "distance": "200公里",
            "source_url": "url2"
        })
        
        # Act
        routes = temp_db.query_routes()
        
        # Assert
        assert len(routes) == 2
    
    def test_save_crawl_log(self, temp_db):
        """测试保存爬取日志"""
        # Arrange
        log = {
            "keyword": "武汉夜市",
            "page": 1,
            "posts_count": 20,
            "status": "success",
            "error": None
        }
        
        # Act
        log_id = temp_db.save_crawl_log(log)
        
        # Assert
        assert log_id > 0
    
    def test_get_stats(self, temp_db):
        """测试获取统计信息"""
        # Arrange
        temp_db.save_market({"title": "M1", "source_url": "url1"})
        temp_db.save_market({"title": "M2", "source_url": "url2"})
        temp_db.save_route({"title": "R1", "source_url": "url3"})
        
        # Act
        stats = temp_db.get_stats()
        
        # Assert
        assert stats["markets_count"] == 2
        assert stats["routes_count"] == 1
