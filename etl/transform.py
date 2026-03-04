# -*- coding: utf-8 -*-
"""
ETL脚本：从小红书JSON数据导入到MySQL
"""

import json
import os
import re
import mysql.connector
from datetime import datetime

# MySQL配置
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',
    'database': 'wuhan_life',
    'charset': 'utf8mb4'
}

def connect_mysql():
    """连接MySQL数据库"""
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        print("[OK] MySQL连接成功")
        return conn
    except Exception as e:
        print(f"[ERROR] MySQL连接失败: {e}")
        return None

def parse_market_info(title, content=""):
    """从标题和内容中解析夜市信息"""
    info = {
        'name': title,
        'address': '',
        'openHours': '',
        'description': content
    }
    
    # 提取地址
    address_patterns = [
        r'地址[：:]\s*([^\n]+)',
        r'📍\s*([^\n]+)',
        r'位于\s*([^\n]+)',
    ]
    
    for pattern in address_patterns:
        match = re.search(pattern, title + content)
        if match:
            info['address'] = match.group(1).strip()
            break
    
    # 提取营业时间
    hours_patterns = [
        r'营业时间[：:]\s*([^\n]+)',
        r'⏰\s*([^\n]+)',
        r'时间[：:]\s*([0-9:]+-[0-9:]+)',
    ]
    
    for pattern in hours_patterns:
        match = re.search(pattern, title + content)
        if match:
            info['openHours'] = match.group(1).strip()
            break
    
    return info

def parse_route_info(title, content=""):
    """从标题和内容中解析跑山路线信息"""
    info = {
        'name': title,
        'distance': 0,
        'duration': '',
        'difficulty': 3,
        'startpoint': '',
        'endpoint': '',
        'description': content
    }
    
    # 提取距离
    distance_patterns = [
        r'(\d+)\s*公里',
        r'(\d+)\s*km',
        r'距离[：:]\s*(\d+)',
    ]
    
    for pattern in distance_patterns:
        match = re.search(pattern, title + content)
        if match:
            info['distance'] = int(match.group(1))
            break
    
    # 提取时长
    duration_patterns = [
        r'时长[：:]\s*([^\n]+)',
        r'用时[：:]\s*([^\n]+)',
        r'(\d+[-~]\d+小时)',
    ]
    
    for pattern in duration_patterns:
        match = re.search(pattern, title + content)
        if match:
            info['duration'] = match.group(1).strip()
            break
    
    # 提取起点终点
    route_patterns = [
        r'路线[：:]\s*([^\n→]+)→([^\n]+)',
        r'从\s*([^\n]+)\s*到\s*([^\n]+)',
    ]
    
    for pattern in route_patterns:
        match = re.search(pattern, title + content)
        if match:
            info['startpoint'] = match.group(1).strip()
            info['endpoint'] = match.group(2).strip()
            break
    
    # 提取难度
    if '简单' in title or '新手' in title:
        info['difficulty'] = 1
    elif '困难' in title or '挑战' in title:
        info['difficulty'] = 5
    
    return info

def import_markets(conn, json_file):
    """导入夜市数据"""
    cursor = conn.cursor()
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    inserted = 0
    for item in data:
        info = parse_market_info(item['title'], item.get('content', ''))
        
        # 检查是否已存在
        cursor.execute("SELECT id FROM markets WHERE name = %s", (info['name'],))
        if cursor.fetchone():
            print(f"  [SKIP] 已存在: {info['name']}")
            continue
        
        # 插入数据
        sql = """
        INSERT INTO markets (name, address, openHours, description, images, rating, createdAt, updatedAt)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            info['name'],
            info['address'] or '武汉',
            info['openHours'],
            info['description'],
            json.dumps([]),
            item.get('likes', 0) / 100,  # 简单归一化
            datetime.now(),
            datetime.now()
        )
        
        try:
            cursor.execute(sql, values)
            inserted += 1
            print(f"  [OK] 插入: {info['name']}")
        except Exception as e:
            print(f"  [ERROR] 插入失败 {info['name']}: {e}")
    
    conn.commit()
    cursor.close()
    print(f"\n[完成] 夜市数据导入完成，共插入 {inserted} 条")
    return inserted

def import_routes(conn, json_file):
    """导入跑山路线数据"""
    cursor = conn.cursor()
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    inserted = 0
    for item in data:
        info = parse_route_info(item['title'], item.get('content', ''))
        
        # 判断方向
        direction = '周边'
        if '东' in info['name'] or '东' in item.get('content', ''):
            direction = '东'
        elif '南' in info['name'] or '南' in item.get('content', ''):
            direction = '南'
        elif '西' in info['name'] or '西' in item.get('content', ''):
            direction = '西'
        elif '北' in info['name'] or '北' in item.get('content', ''):
            direction = '北'
        
        # 检查是否已存在
        cursor.execute("SELECT id FROM routes WHERE name = %s", (info['name'],))
        if cursor.fetchone():
            print(f"  [SKIP] 已存在: {info['name']}")
            continue
        
        # 插入数据
        sql = """
        INSERT INTO routes (name, direction, distance, duration, difficulty, startpoint, endpoint, description, images, rating, createdAt, updatedAt)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            info['name'],
            direction,
            info['distance'],
            info['duration'],
            info['difficulty'],
            info['startpoint'] or '武汉市区',
            info['endpoint'] or '武汉周边',
            info['description'],
            json.dumps([]),
            item.get('likes', 0) / 100,
            datetime.now(),
            datetime.now()
        )
        
        try:
            cursor.execute(sql, values)
            inserted += 1
            print(f"  [OK] 插入: {info['name']}")
        except Exception as e:
            print(f"  [ERROR] 插入失败 {info['name']}: {e}")
    
    conn.commit()
    cursor.close()
    print(f"\n[完成] 跑山路线数据导入完成，共插入 {inserted} 条")
    return inserted

def main():
    """主函数"""
    print("=" * 60)
    print("  ETL脚本 - 小红书数据导入MySQL")
    print("=" * 60)
    
    # 连接MySQL
    conn = connect_mysql()
    if not conn:
        return
    
    # 导入夜市数据
    markets_file = "data/search_results.json"
    if os.path.exists(markets_file):
        print(f"\n[1/2] 导入夜市数据: {markets_file}")
        import_markets(conn, markets_file)
    else:
        print(f"[WARN] 文件不存在: {markets_file}")
    
    # 导入跑山数据
    routes_file = "data/search_results_routes.json"
    if os.path.exists(routes_file):
        print(f"\n[2/2] 导入跑山数据: {routes_file}")
        import_routes(conn, routes_file)
    else:
        print(f"[WARN] 文件不存在: {routes_file}")
    
    # 关闭连接
    conn.close()
    print("\n" + "=" * 60)
    print("  ETL完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
