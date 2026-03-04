"""
小红书爬虫 - 主程序
用于爬取武汉夜市和跑山路线数据
"""

import asyncio
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent))

from playwright.async_api import async_playwright
from src.login import CookieManager, LoginManager
from src.search import SearchEngine
from src.parser import PostParser
from src.storage import Database


class XHSCrawler:
    """小红书爬虫"""
    
    def __init__(self, headless: bool = False):
        """
        初始化爬虫
        
        Args:
            headless: 是否无头模式运行
        """
        self.headless = headless
        self.cookie_manager = CookieManager("data/cookies.json")
        self.db = Database("data/xiaohongshu.db")
        self.search_engine = SearchEngine()
        self.parser = PostParser()
    
    async def run(self, keywords: list, max_pages: int = 3):
        """
        运行爬虫
        
        Args:
            keywords: 搜索关键词列表
            max_pages: 每个关键词爬取的最大页数
        """
        print("=" * 60)
        print("  小红书爬虫 - 武汉夜市 & 跑山路线")
        print("=" * 60)
        
        # 初始化数据库
        self.db.init_tables()
        
        async with async_playwright() as p:
            # 启动浏览器
            print("\n🚀 启动浏览器...")
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context()
            
            # 尝试加载已有cookies
            login_manager = LoginManager(context, self.cookie_manager)
            
            if self.cookie_manager.is_logged_in():
                print("✅ 发现已保存的登录状态，正在加载...")
                await login_manager.load_cookies()
            else:
                print("⚠️ 未找到登录状态，需要扫码登录")
            
            # 创建页面
            page = await context.new_page()
            
            # 检查登录状态
            await page.goto("https://www.xiaohongshu.com/")
            await page.wait_for_timeout(2000)
            
            if not self.cookie_manager.is_logged_in():
                # 需要登录
                success = await login_manager.login_with_qrcode(page)
                if not success:
                    print("❌ 登录失败，退出程序")
                    await browser.close()
                    return
            
            # 开始爬取
            for keyword in keywords:
                print(f"\n{'=' * 60}")
                print(f"🔍 开始爬取关键词: {keyword}")
                print(f"{'=' * 60}")
                
                try:
                    # 搜索
                    posts = await self.search_engine.search(page, keyword, max_pages)
                    
                    if not posts:
                        print(f"⚠️ 关键词 '{keyword}' 无搜索结果")
                        continue
                    
                    print(f"✅ 找到 {len(posts)} 条帖子")
                    
                    # 解析并保存
                    saved_count = 0
                    for i, post in enumerate(posts, 1):
                        print(f"\n[{i}/{len(posts)}] 处理: {post.get('title', 'N/A')[:30]}...")
                        
                        # 判断是夜市还是跑山
                        if self._is_route_keyword(keyword):
                            parsed = self.parser.parse_route(post)
                            self.db.save_route(parsed)
                        else:
                            parsed = self.parser.parse_market(post)
                            self.db.save_market(parsed)
                        
                        saved_count += 1
                        
                        # 避免请求过快
                        await page.wait_for_timeout(500)
                    
                    # 保存日志
                    self.db.save_crawl_log({
                        "keyword": keyword,
                        "page": max_pages,
                        "posts_count": saved_count,
                        "status": "success",
                        "error": None
                    })
                    
                    print(f"\n✅ 关键词 '{keyword}' 完成，保存 {saved_count} 条数据")
                    
                except Exception as e:
                    print(f"❌ 爬取失败: {e}")
                    self.db.save_crawl_log({
                        "keyword": keyword,
                        "page": 0,
                        "posts_count": 0,
                        "status": "failed",
                        "error": str(e)
                    })
            
            # 显示统计
            stats = self.db.get_stats()
            print(f"\n{'=' * 60}")
            print("📊 爬取统计:")
            print(f"  夜市数据: {stats['markets_count']} 条")
            print(f"  跑山数据: {stats['routes_count']} 条")
            print(f"{'=' * 60}")
            
            await browser.close()
    
    def _is_route_keyword(self, keyword: str) -> bool:
        """判断是否为跑山关键词"""
        route_keywords = ["跑山", "骑行", "摩旅", "自驾", "路线", "环线"]
        return any(k in keyword for k in route_keywords)


async def main():
    """主函数"""
    # 配置搜索关键词
    keywords = [
        # 夜市关键词
        "武汉夜市",
        "武汉宵夜",
        "武汉夜市美食",
        "武汉万松园",
        "武汉江汉路夜市",
        
        # 跑山关键词
        "武汉跑山",
        "武汉周边骑行",
        "武汉摩旅",
        "黄陂跑山",
    ]
    
    # 创建爬虫（headless=False 显示浏览器界面，方便扫码登录）
    crawler = XHSCrawler(headless=False)
    
    # 运行（每个关键词爬取2页）
    await crawler.run(keywords, max_pages=2)


if __name__ == "__main__":
    asyncio.run(main())
