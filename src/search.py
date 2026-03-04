"""
搜索模块
负责在小红书搜索内容
"""

import asyncio
from typing import List, Dict, Optional
from urllib.parse import quote


class SearchEngine:
    """小红书搜索引擎"""
    
    def __init__(self):
        """初始化搜索引擎"""
        self.base_url = "https://www.xiaohongshu.com"
    
    async def search(
        self, 
        page, 
        keyword: str, 
        max_pages: int = 1
    ) -> List[Dict]:
        """
        搜索关键词
        
        Args:
            page: Playwright页面对象
            keyword: 搜索关键词
            max_pages: 最大爬取页数
            
        Returns:
            帖子列表
            
        Raises:
            ValueError: 关键词为空时抛出
        """
        if not keyword or not keyword.strip():
            raise ValueError("关键词不能为空")
        
        keyword = keyword.strip()
        all_results = []
        
        # 构建搜索URL
        search_url = f"{self.base_url}/search_result?keyword={quote(keyword)}"
        
        for page_num in range(1, max_pages + 1):
            print(f"🔍 正在搜索第 {page_num} 页...")
            
            # 访问搜索页
            await page.goto(f"{search_url}&page={page_num}")
            await page.wait_for_timeout(2000)  # 等待页面加载
            
            # 提取帖子数据
            posts = await self._extract_posts(page)
            
            if not posts:
                print(f"⚠️ 第 {page_num} 页无结果，停止搜索")
                break
            
            all_results.extend(posts)
            print(f"✅ 第 {page_num} 页获取 {len(posts)} 条帖子")
            
            # 避免请求过快
            await page.wait_for_timeout(1000)
        
        return all_results
    
    async def _extract_posts(self, page) -> List[Dict]:
        """
        从页面提取帖子数据
        
        Args:
            page: Playwright页面对象
            
        Returns:
            帖子列表
        """
        # 使用JavaScript提取数据
        posts = await page.evaluate("""
            () => {
                const results = [];
                
                // 尝试多种选择器（小红书页面结构可能变化）
                const selectors = [
                    '.note-item',
                    '[class*="note-item"]',
                    '[class*="search-result"] a',
                    'section a[href*="/explore/"]'
                ];
                
                let elements = [];
                for (const selector of selectors) {
                    elements = document.querySelectorAll(selector);
                    if (elements.length > 0) break;
                }
                
                elements.forEach(el => {
                    try {
                        // 提取标题
                        const titleEl = el.querySelector('[class*="title"], h3, h4');
                        const title = titleEl ? titleEl.textContent.trim() : '';
                        
                        // 提取链接
                        const link = el.href || el.querySelector('a')?.href || '';
                        
                        // 提取作者
                        const authorEl = el.querySelector('[class*="author"], [class*="name"]');
                        const author = authorEl ? authorEl.textContent.trim() : '';
                        
                        // 提取点赞数
                        const likesEl = el.querySelector('[class*="like"], [class*="count"]');
                        const likesText = likesEl ? likesEl.textContent.trim() : '0';
                        const likes = parseInt(likesText) || 0;
                        
                        // 提取封面图
                        const imgEl = el.querySelector('img');
                        const cover = imgEl ? imgEl.src : '';
                        
                        if (title && link) {
                            results.push({
                                title: title,
                                url: link,
                                author: author,
                                likes: likes,
                                cover: cover
                            });
                        }
                    } catch (e) {
                        // 忽略解析错误
                    }
                });
                
                return results;
            }
        """)
        
        return posts or []
    
    async def get_post_detail(self, page, post_url: str) -> Optional[Dict]:
        """
        获取帖子详情
        
        Args:
            page: Playwright页面对象
            post_url: 帖子URL
            
        Returns:
            帖子详情
        """
        try:
            await page.goto(post_url)
            await page.wait_for_timeout(2000)
            
            detail = await page.evaluate("""
                () => {
                    // 提取标题
                    const titleEl = document.querySelector('h1, [class*="title"]');
                    const title = titleEl ? titleEl.textContent.trim() : '';
                    
                    // 提取正文
                    const descEl = document.querySelector('[class*="desc"], [class*="content"]');
                    const desc = descEl ? descEl.textContent.trim() : '';
                    
                    // 提取图片
                    const images = [];
                    document.querySelectorAll('img').forEach(img => {
                        if (img.src && img.src.includes('xiaohongshu')) {
                            images.push(img.src);
                        }
                    });
                    
                    // 提取作者
                    const authorEl = document.querySelector('[class*="author"], [class*="username"]');
                    const author = authorEl ? authorEl.textContent.trim() : '';
                    
                    // 提取点赞数
                    const likesEl = document.querySelector('[class*="like"]');
                    const likesText = likesEl ? likesEl.textContent.trim() : '0';
                    const likes = parseInt(likesText) || 0;
                    
                    return {
                        title: title,
                        desc: desc,
                        images: images.slice(0, 9),  // 最多9张图
                        author: author,
                        likes: likes,
                        url: window.location.href
                    };
                }
            """)
            
            return detail
            
        except Exception as e:
            print(f"❌ 获取帖子详情失败: {e}")
            return None
