"""
解析模块
负责解析小红书帖子内容，提取结构化数据
"""

import re
import json
from typing import Dict, List, Optional


class PostParser:
    """帖子解析器"""
    
    def __init__(self):
        """初始化解析器"""
        # 常见的关键词模式
        self.address_patterns = [
            r'📍地址[：:]\s*(.+)',
            r'地址[：:]\s*(.+)',
            r'位置[：:]\s*(.+)',
            r'地点[：:]\s*(.+)',
        ]
        
        self.hours_patterns = [
            r'⏰?营业时间[：:]\s*(.+)',
            r'时间[：:]\s*(.+)',
            r'开放时间[：:]\s*(.+)',
        ]
        
        self.distance_patterns = [
            r'📏?距离[：:]\s*(.+)',
            r'里程[：:]\s*(.+)',
            r'全程[：:]\s*(.+)',
        ]
        
        self.duration_patterns = [
            r'⏱️?时长[：:]\s*(.+)',
            r'用时[：:]\s*(.+)',
            r'耗时[：:]\s*(.+)',
        ]
        
        self.difficulty_patterns = [
            r'⛰️?难度[：:]\s*(.+)',
            r'难度等级[：:]\s*(.+)',
        ]
    
    def parse_market(self, raw_post: Dict) -> Dict:
        """
        解析夜市帖子
        
        Args:
            raw_post: 原始帖子数据
            
        Returns:
            结构化的夜市数据
            
        Raises:
            ValueError: 帖子为空时抛出
        """
        if not raw_post:
            raise ValueError("帖子内容不能为空")
        
        title = raw_post.get("title", "")
        desc = raw_post.get("desc", "")
        content = f"{title}\n{desc}"
        
        return {
            "title": title,
            "content": desc,
            "address": self.extract_address(content),
            "open_hours": self.extract_open_hours(content),
            "images": self.parse_images(raw_post),
            "author": raw_post.get("author", ""),
            "likes": raw_post.get("likes", 0),
            "source_url": raw_post.get("url", ""),
            "rating": self._estimate_rating(raw_post.get("likes", 0))
        }
    
    def parse_route(self, raw_post: Dict) -> Dict:
        """
        解析跑山帖子
        
        Args:
            raw_post: 原始帖子数据
            
        Returns:
            结构化的跑山数据
        """
        if not raw_post:
            raise ValueError("帖子内容不能为空")
        
        title = raw_post.get("title", "")
        desc = raw_post.get("desc", "")
        content = f"{title}\n{desc}"
        
        # 提取路线信息
        route_info = self._extract_route_info(content)
        
        return {
            "title": title,
            "content": desc,
            "distance": self._extract_by_patterns(content, self.distance_patterns),
            "duration": self._extract_by_patterns(content, self.duration_patterns),
            "difficulty": self._extract_by_patterns(content, self.difficulty_patterns),
            "start_point": route_info.get("start", ""),
            "end_point": route_info.get("end", ""),
            "images": self.parse_images(raw_post),
            "author": raw_post.get("author", ""),
            "likes": raw_post.get("likes", 0),
            "source_url": raw_post.get("url", "")
        }
    
    def parse_images(self, post: Dict) -> List[str]:
        """
        解析图片URL
        
        Args:
            post: 帖子数据
            
        Returns:
            图片URL列表
        """
        images = post.get("images", [])
        if isinstance(images, str):
            try:
                images = json.loads(images)
            except:
                images = []
        
        # 过滤有效URL
        return [url for url in images if url and url.startswith("http")]
    
    def extract_address(self, text: str) -> str:
        """
        从文本中提取地址
        
        Args:
            text: 文本内容
            
        Returns:
            地址字符串
        """
        return self._extract_by_patterns(text, self.address_patterns)
    
    def extract_open_hours(self, text: str) -> str:
        """
        从文本中提取营业时间
        
        Args:
            text: 文本内容
            
        Returns:
            营业时间字符串
        """
        return self._extract_by_patterns(text, self.hours_patterns)
    
    def _extract_by_patterns(self, text: str, patterns: List[str]) -> str:
        """
        使用多个模式提取信息
        
        Args:
            text: 文本内容
            patterns: 正则模式列表
            
        Returns:
            提取的字符串
        """
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # 清理提取结果
                result = match.group(1).strip()
                # 移除后续的换行和其他标记
                result = re.split(r'[\n💰⏰📍📏⛰️⏱️]', result)[0].strip()
                return result
        return ""
    
    def _extract_route_info(self, text: str) -> Dict[str, str]:
        """
        提取路线起点终点信息
        
        Args:
            text: 文本内容
            
        Returns:
            包含start和end的字典
        """
        # 常见格式：武汉市区→木兰山→木兰天池
        route_pattern = r'路线[：:]\s*(.+?)(?:\n|$)'
        match = re.search(route_pattern, text)
        
        if match:
            route_text = match.group(1)
            # 分割路线点
            points = re.split(r'[→->]+', route_text)
            points = [p.strip() for p in points if p.strip()]
            
            if len(points) >= 2:
                return {
                    "start": points[0],
                    "end": points[-1]
                }
        
        return {"start": "", "end": ""}
    
    def _estimate_rating(self, likes: int) -> float:
        """
        根据点赞数估算评分
        
        Args:
            likes: 点赞数
            
        Returns:
            估算评分（0-5）
        """
        if likes >= 10000:
            return 4.8
        elif likes >= 5000:
            return 4.5
        elif likes >= 1000:
            return 4.2
        elif likes >= 500:
            return 4.0
        elif likes >= 100:
            return 3.8
        else:
            return 3.5
