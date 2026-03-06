"""
小红书爬虫 - 主程序
用于爬取武汉夜市和跑山路线数据
"""

import asyncio
import sys
import os
from pathlib import Path

# 禁用代理
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['NO_PROXY'] = '*'

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent))

from playwright.async_api import async_playwright
from playwright_stealth import Stealth
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
            # 启动浏览器 - 使用更真实的配置
            print("\n[STEP 1] 启动浏览器...")
            browser = await p.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-infobars',
                    '--window-size=1920,1080',
                ]
            )
            
            # 创建上下文 - 模拟真实浏览器
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
            )
            
            # 尝试加载已有cookies
            login_manager = LoginManager(context, self.cookie_manager)
            
            if self.cookie_manager.is_logged_in():
                print("[OK] 发现已保存的登录状态，正在加载...")
                await login_manager.load_cookies()
            else:
                print("[WARN] 未找到登录状态")
            
            # 创建页面
            page = await context.new_page()
            
            # 应用stealth - 隐藏自动化特征
            stealth = Stealth()
            await stealth.apply_stealth_async(page)
            
            # 开始爬取
            for keyword in keywords:
                print(f"\n{'=' * 60}")
                print(f"[SEARCH] 开始爬取关键词: {keyword}")
                print(f"{'=' * 60}")
                
                try:
                    # 访问搜索页面
                    search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}"
                    print(f"[STEP] 访问搜索页面...")
                    await page.goto(search_url, wait_until='networkidle')
                    await page.wait_for_timeout(3000)
                    
                    # 检查是否需要登录
                    posts = await page.query_selector_all('a[href*="/explore/"]')
                    
                    if len(posts) == 0:
                        print("[WARN] 未找到搜索结果，可能需要登录")
                        print("\n" + "=" * 60)
                        print("  请在浏览器中扫码登录（搜索页面上的登录弹窗）")
                        print("  登录成功后，脚本会自动继续")
                        print("=" * 60)
                        
                        # 等待登录成功
                        max_wait = 300  # 5分钟
                        logged_in = False
                        
                        for i in range(max_wait):
                            await page.wait_for_timeout(1000)
                            
                            # 检查是否有搜索结果
                            posts = await page.query_selector_all('a[href*="/explore/"]')
                            if len(posts) > 0:
                                logged_in = True
                                print(f"\n[OK] 登录成功！找到 {len(posts)} 个帖子")
                                
                                # 保存cookies
                                cookies = await context.cookies()
                                self.cookie_manager.save_cookies(cookies)
                                print(f"[OK] Cookies已保存 ({len(cookies)} 个)")
                                break
                            
                            if (i + 1) % 30 == 0:
                                print(f"[INFO] 已等待 {i+1} 秒...")
                        
                        if not logged_in:
                            print("[ERROR] 登录超时，跳过此关键词")
                            continue
                    
                    # 提取帖子数据
                    print(f"[STEP] 提取帖子数据...")
                    
                    posts_data = await page.evaluate("""
                        () => {
                            const results = [];
                            const links = document.querySelectorAll('a[href*="/explore/"]');
                            
                            links.forEach(link => {
                                try {
                                    const href = link.href;
                                    const parent = link.closest('[class*="note"], [class*="card"], [class*="item"]');
                                    const text = parent ? parent.innerText : link.innerText;
                                    
                                    if (href && href.includes('/explore/')) {
                                        results.push({
                                            url: href,
                                            title: text ? text.split('\\n')[0] : ''
                                        });
                                    }
                                } catch (e) {}
                            });
                            
                            return results;
                        }
                    """)
                    
                    print(f"[OK] 提取到 {len(posts_data)} 条帖子")
                    
                    if not posts_data:
                        print(f"[WARN] 关键词 '{keyword}' 无搜索结果")
                        continue
                    
                    # 解析并保存
                    saved_count = 0
                    for i, post in enumerate(posts_data, 1):
                        title_preview = post.get('title', 'N/A')[:30] if post.get('title') else 'N/A'
                        print(f"\n[{i}/{len(posts_data)}] 处理: {title_preview}...")
                        
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
                    
                    print(f"\n[OK] 关键词 '{keyword}' 完成，保存 {saved_count} 条数据")
                    
                    # 关键词之间等待
                    await page.wait_for_timeout(2000)
                    
                except Exception as e:
                    print(f"[ERROR] 爬取失败: {e}")
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
            print("[STATS] 爬取统计:")
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
    
    # 创建爬虫（headless=False 显示浏览器界面，需要在搜索页面扫码登录）
    crawler = XHSCrawler(headless=False)
    
    # 运行（每个关键词爬取1页）
    await crawler.run(keywords, max_pages=1)


if __name__ == "__main__":
    asyncio.run(main())
