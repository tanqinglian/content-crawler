"""
存储模块
负责数据的持久化存储
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class Database:
    """数据库管理器"""
    
    def __init__(self, db_path: str = "data/xiaohongshu.db"):
        """
        初始化数据库
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
    
    def init_tables(self):
        """初始化数据库表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 夜市表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS markets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                address TEXT,
                open_hours TEXT,
                images TEXT,
                rating REAL DEFAULT 0,
                author TEXT,
                likes INTEGER DEFAULT 0,
                source_url TEXT UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 跑山路线表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                distance TEXT,
                duration TEXT,
                difficulty TEXT,
                start_point TEXT,
                end_point TEXT,
                images TEXT,
                author TEXT,
                likes INTEGER DEFAULT 0,
                source_url TEXT UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 爬取日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crawl_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                page INTEGER,
                posts_count INTEGER,
                status TEXT,
                error TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_markets_source ON markets(source_url)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_routes_source ON routes(source_url)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_keyword ON crawl_logs(keyword)")
        
        conn.commit()
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def save_market(self, market: Dict) -> int:
        """
        保存夜市数据
        
        Args:
            market: 夜市数据字典
            
        Returns:
            记录ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 检查是否已存在
        cursor.execute(
            "SELECT id FROM markets WHERE source_url = ?",
            (market.get("source_url"),)
        )
        existing = cursor.fetchone()
        
        if existing:
            # 更新
            cursor.execute("""
                UPDATE markets SET
                    title = ?,
                    content = ?,
                    address = ?,
                    open_hours = ?,
                    images = ?,
                    rating = ?,
                    author = ?,
                    likes = ?,
                    updated_at = ?
                WHERE source_url = ?
            """, (
                market.get("title"),
                market.get("content"),
                market.get("address"),
                market.get("open_hours"),
                self._serialize_images(market.get("images")),
                market.get("rating", 0),
                market.get("author"),
                market.get("likes", 0),
                datetime.now(),
                market.get("source_url")
            ))
            return existing["id"]
        else:
            # 插入
            cursor.execute("""
                INSERT INTO markets (
                    title, content, address, open_hours, images,
                    rating, author, likes, source_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                market.get("title"),
                market.get("content"),
                market.get("address"),
                market.get("open_hours"),
                self._serialize_images(market.get("images")),
                market.get("rating", 0),
                market.get("author"),
                market.get("likes", 0),
                market.get("source_url")
            ))
            return cursor.lastrowid
    
    def save_route(self, route: Dict) -> int:
        """
        保存跑山数据
        
        Args:
            route: 跑山数据字典
            
        Returns:
            记录ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 检查是否已存在
        cursor.execute(
            "SELECT id FROM routes WHERE source_url = ?",
            (route.get("source_url"),)
        )
        existing = cursor.fetchone()
        
        if existing:
            # 更新
            cursor.execute("""
                UPDATE routes SET
                    title = ?,
                    content = ?,
                    distance = ?,
                    duration = ?,
                    difficulty = ?,
                    start_point = ?,
                    end_point = ?,
                    images = ?,
                    author = ?,
                    likes = ?,
                    updated_at = ?
                WHERE source_url = ?
            """, (
                route.get("title"),
                route.get("content"),
                route.get("distance"),
                route.get("duration"),
                route.get("difficulty"),
                route.get("start_point"),
                route.get("end_point"),
                self._serialize_images(route.get("images")),
                route.get("author"),
                route.get("likes", 0),
                datetime.now(),
                route.get("source_url")
            ))
            return existing["id"]
        else:
            # 插入
            cursor.execute("""
                INSERT INTO routes (
                    title, content, distance, duration, difficulty,
                    start_point, end_point, images, author, likes, source_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                route.get("title"),
                route.get("content"),
                route.get("distance"),
                route.get("duration"),
                route.get("difficulty"),
                route.get("start_point"),
                route.get("end_point"),
                self._serialize_images(route.get("images")),
                route.get("author"),
                route.get("likes", 0),
                route.get("source_url")
            ))
            return cursor.lastrowid
    
    def get_market(self, market_id: int) -> Optional[Dict]:
        """获取夜市数据"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM markets WHERE id = ?", (market_id,))
        row = cursor.fetchone()
        
        return dict(row) if row else None
    
    def get_route(self, route_id: int) -> Optional[Dict]:
        """获取跑山数据"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM routes WHERE id = ?", (route_id,))
        row = cursor.fetchone()
        
        return dict(row) if row else None
    
    def query_markets(self, limit: int = 100) -> List[Dict]:
        """查询夜市列表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM markets ORDER BY likes DESC LIMIT ?",
            (limit,)
        )
        
        return [dict(row) for row in cursor.fetchall()]
    
    def query_routes(self, limit: int = 100) -> List[Dict]:
        """查询跑山列表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM routes ORDER BY likes DESC LIMIT ?",
            (limit,)
        )
        
        return [dict(row) for row in cursor.fetchall()]
    
    def save_crawl_log(self, log: Dict) -> int:
        """保存爬取日志"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO crawl_logs (keyword, page, posts_count, status, error)
            VALUES (?, ?, ?, ?, ?)
        """, (
            log.get("keyword"),
            log.get("page"),
            log.get("posts_count"),
            log.get("status"),
            log.get("error")
        ))
        
        return cursor.lastrowid
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM markets")
        markets_count = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM routes")
        routes_count = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM crawl_logs WHERE status = 'success'")
        success_count = cursor.fetchone()["count"]
        
        return {
            "markets_count": markets_count,
            "routes_count": routes_count,
            "crawl_success_count": success_count
        }
    
    def _serialize_images(self, images) -> str:
        """序列化图片列表"""
        if isinstance(images, list):
            return json.dumps(images, ensure_ascii=False)
        return images or "[]"
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
