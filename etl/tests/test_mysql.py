# -*- coding: utf-8 -*-
"""
ETL完整测试脚本（包含MySQL真实连接测试）
"""

import unittest
import json
import os
import sys

# 添加etl目录到路径
etl_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, etl_dir)

import transform
parse_market_info = transform.parse_market_info
parse_route_info = transform.parse_route_info
MYSQL_CONFIG = transform.MYSQL_CONFIG
connect_mysql = transform.connect_mysql


class TestMySQLConnection(unittest.TestCase):
    """MySQL真实连接测试"""

    def test_real_connection(self):
        """测试真实连接"""
        conn = connect_mysql()
        if conn:
            print("\n[OK] MySQL连接成功")
            conn.close()
            self.assertTrue(True)
        else:
            self.fail("MySQL连接失败")

    def test_create_database(self):
        """测试创建数据库"""
        conn = connect_mysql()
        if not conn:
            self.skipTest("MySQL连接失败")

        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS wuhan_life_test")
        cursor.execute("SHOW DATABASES LIKE 'wuhan_life_test'")
        result = cursor.fetchone()

        conn.close()
        self.assertIsNotNone(result)

    def test_create_tables(self):
        """测试创建表"""
        conn = connect_mysql()
        if not conn:
            self.skipTest("MySQL连接失败")

        cursor = conn.cursor()
        cursor.execute("USE wuhan_life_test")

        # 创建测试表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_markets (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100),
                address VARCHAR(200)
            )
        """)

        # 验证表存在
        cursor.execute("SHOW TABLES LIKE 'test_markets'")
        result = cursor.fetchone()

        conn.close()
        self.assertIsNotNone(result)


class TestDataImport(unittest.TestCase):
    """数据导入测试"""

    def test_import_market_data(self):
        """测试导入夜市数据"""
        conn = connect_mysql()
        if not conn:
            self.skipTest("MySQL连接失败")

        cursor = conn.cursor()
        cursor.execute("USE wuhan_life_test")

        # 插入测试数据
        test_data = {
            'name': '测试夜市',
            'address': '测试地址',
            'openHours': '18:00-02:00'
        }

        cursor.execute(
            "INSERT INTO test_markets (name, address) VALUES (%s, %s)",
            (test_data['name'], test_data['address'])
        )

        # 验证插入
        cursor.execute("SELECT * FROM test_markets WHERE name = '测试夜市'")
        result = cursor.fetchone()

        conn.commit()
        conn.close()

        self.assertIsNotNone(result)
        self.assertEqual(result[1], '测试夜市')


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
