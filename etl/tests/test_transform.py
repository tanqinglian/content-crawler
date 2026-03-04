# -*- coding: utf-8 -*-
"""
ETL测试用例 - TDD红灯阶段
"""

import unittest
import json
import os
import sys

# 添加etl目录到路径
etl_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, etl_dir)

# 直接导入transform模块
import transform
parse_market_info = transform.parse_market_info
parse_route_info = transform.parse_route_info
MYSQL_CONFIG = transform.MYSQL_CONFIG
connect_mysql = transform.connect_mysql


class TestMarketParser(unittest.TestCase):
    """夜市解析测试"""
    
    def test_parse_basic_market(self):
        """测试基本夜市信息解析"""
        title = "武汉万松园夜市探店"
        content = "📍地址：江汉区万松园路\n⏰营业时间：18:00-02:00"
        
        result = parse_market_info(title, content)
        
        self.assertEqual(result['name'], "武汉万松园夜市探店")
        self.assertEqual(result['address'], "江汉区万松园路")
        self.assertEqual(result['openHours'], "18:00-02:00")
    
    def test_parse_address_with_emoji(self):
        """测试带emoji的地址解析"""
        title = "保成路夜市"
        content = "📍江汉区保成路123号"
        
        result = parse_market_info(title, content)
        
        self.assertIn("保成路", result['address'])
    
    def test_parse_hours_various_formats(self):
        """测试多种营业时间格式"""
        test_cases = [
            ("夜市", "营业时间：18:00-02:00", "18:00-02:00"),
            ("夜市", "⏰19:00-24:00", "19:00-24:00"),
            ("夜市", "时间：17:30-凌晨2点", "17:30-凌晨2点"),
        ]
        
        for title, content, expected in test_cases:
            result = parse_market_info(title, content)
            self.assertIsNotNone(result['openHours'])
    
    def test_parse_empty_content(self):
        """测试空内容"""
        result = parse_market_info("测试夜市", "")
        
        self.assertEqual(result['name'], "测试夜市")
        self.assertEqual(result['address'], '')
        self.assertEqual(result['openHours'], '')


class TestRouteParser(unittest.TestCase):
    """跑山路线解析测试"""
    
    def test_parse_basic_route(self):
        """测试基本跑山信息解析"""
        title = "武汉周边跑山｜木兰山环线150公里"
        content = "路线：武汉市区→木兰山→木兰天池\n时长：4-5小时"
        
        result = parse_route_info(title, content)
        
        self.assertIn("木兰山", result['name'])
        self.assertEqual(result['distance'], 150)
        self.assertIn("4-5小时", result['duration'])
    
    def test_parse_distance_formats(self):
        """测试多种距离格式"""
        test_cases = [
            ("100公里路线", "", 100),
            ("50km短途", "", 50),
            ("距离200", "", 200),
        ]
        
        for title, content, expected in test_cases:
            result = parse_route_info(title, content)
            self.assertEqual(result['distance'], expected)
    
    def test_parse_difficulty(self):
        """测试难度识别"""
        # 简单路线
        result1 = parse_route_info("新手友好跑山路线", "")
        self.assertEqual(result1['difficulty'], 1)
        
        # 困难路线
        result2 = parse_route_info("挑战级山路", "")
        self.assertEqual(result2['difficulty'], 5)
        
        # 普通路线
        result3 = parse_route_info("普通跑山路线", "")
        self.assertEqual(result3['difficulty'], 3)
    
    def test_parse_start_end_points(self):
        """测试起终点解析"""
        title = "跑山路线"
        content = "路线：武汉市中心→黄陂木兰山→木兰天池"
        
        result = parse_route_info(title, content)
        
        self.assertIn("武汉市中心", result['startpoint'])
        self.assertIn("木兰天池", result['endpoint'])
    
    def test_parse_empty_route(self):
        """测试空内容"""
        result = parse_route_info("测试路线", "")
        
        self.assertEqual(result['name'], "测试路线")
        self.assertEqual(result['distance'], 0)
        self.assertEqual(result['difficulty'], 3)


class TestMySQLConnection(unittest.TestCase):
    """MySQL连接测试"""
    
    def test_connection_config(self):
        """测试连接配置"""
        # 直接使用已导入的配置
        self.assertIn('host', MYSQL_CONFIG)
        self.assertIn('user', MYSQL_CONFIG)
        self.assertIn('database', MYSQL_CONFIG)
        self.assertEqual(MYSQL_CONFIG['database'], 'wuhan_life')
    
    @unittest.skipIf(not os.environ.get('MYSQL_TEST'), "需要MySQL环境")
    def test_real_connection(self):
        """测试真实连接（需要MySQL）"""
        from etl.transform import connect_mysql
        
        conn = connect_mysql()
        self.assertIsNotNone(conn)
        conn.close()


class TestDataImport(unittest.TestCase):
    """数据导入测试"""
    
    def test_json_file_reading(self):
        """测试JSON文件读取"""
        test_file = "data/search_results.json"
        
        if os.path.exists(test_file):
            with open(test_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.assertIsInstance(data, list)
            self.assertGreater(len(data), 0)
            
            # 验证数据结构
            item = data[0]
            self.assertIn('title', item)
            self.assertIn('url', item)
        else:
            self.skipTest("测试数据文件不存在")
    
    def test_data_structure(self):
        """测试数据结构"""
        test_data = [
            {
                "title": "测试夜市",
                "url": "https://test.com",
                "author": "测试用户",
                "likes": 100
            }
        ]
        
        # 验证必要字段
        for item in test_data:
            self.assertIn('title', item)
            self.assertIn('url', item)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
