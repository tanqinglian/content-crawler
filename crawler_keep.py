"""
小红书爬虫 - 持久化版本
登录后保持浏览器打开，可以重复爬取
"""
import asyncio
import sys
import os
from pathlib import Path

os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['NO_PROXY'] = '*'

sys.path.insert(0, str(Path(__file__).parent))

from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from src.storage import Database
import json


class XHSCrawler:
    """小红书爬虫 - 持久化版本"""
    
    def __init__(self):
        self.db = Database("data/xiaohongshu.db")
        self.browser = None
        self.context = None
        self.page = None
        self.logged_in = False
    
    async def start(self):
        """启动浏览器"""
        print("[STEP] 启动浏览器...")
        
        p = await async_playwright().start()
        self.browser = await p.chromium.launch(
            headless=False,  # 保持可见
            args=['--disable-blink-features=AutomationControlled']
        )
        
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            locale='zh-CN',
        )
        
        # 尝试加载已保存的cookies
        cookies_path = Path("data/cookies.json")
        if cookies_path.exists():
            with open(cookies_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            await self.context.add_cookies(cookies)
            print(f"[OK] 已加载 {len(cookies)} 个cookies")
        
        self.page = await self.context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(self.page)
        
        print("[OK] 浏览器已启动")
    
    async def ensure_login(self):
        """确保已登录"""
        if self.logged_in:
            return True
        
        # 访问搜索页面检查
        await self.page.goto("https://www.xiaohongshu.com/search_result?keyword=武汉夜市", wait_until='networkidle')
        await self.page.wait_for_timeout(3000)
        
        # 检查是否有搜索结果
        posts = await self.page.query_selector_all('a[href*="/explore/"]')
        
        if len(posts) > 0:
            self.logged_in = True
            print(f"[OK] 已登录，找到 {len(posts)} 个帖子")
            return True
        
        # 需要登录
        print("\n" + "=" * 60)
        print("  请在浏览器中扫码登录")
        print("  登录成功后脚本会自动继续")
        print("=" * 60)
        
        max_wait = 300
        for i in range(max_wait):
            await self.page.wait_for_timeout(1000)
            posts = await self.page.query_selector_all('a[href*="/explore/"]')
            
            if len(posts) > 0:
                self.logged_in = True
                print(f"\n[OK] 登录成功！")
                
                # 保存cookies
                cookies = await self.context.cookies()
                Path("data").mkdir(exist_ok=True)
                with open("data/cookies.json", 'w', encoding='utf-8') as f:
                    json.dump(cookies, f, ensure_ascii=False, indent=2)
                print(f"[OK] Cookies已保存")
                return True
            
            if (i + 1) % 30 == 0:
                print(f"[INFO] 等待登录中... {i+1}秒")
        
        print("[ERROR] 登录超时")
        return False
    
    async def crawl(self, keyword: str, max_count: int = 50):
        """爬取单个关键词"""
        if not self.page:
            await self.start()
        
        if not await self.ensure_login():
            return []
        
        print(f"\n[SEARCH] 爬取: {keyword}")
        
        # 访问搜索页面
        search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}"
        await self.page.goto(search_url, wait_until='networkidle')
        await self.page.wait_for_timeout(3000)
        
        # 提取数据
        posts = await self.page.evaluate("""
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
        
        print(f"[OK] 找到 {len(posts)} 条帖子")
        
        # 保存到数据库
        is_route = any(k in keyword for k in ["跑山", "骑行", "摩旅", "自驾", "路线"])
        
        saved = 0
        for post in posts[:max_count]:
            if is_route:
                self.db.save_route(post)
            else:
                self.db.save_market(post)
            saved += 1
        
        print(f"[OK] 保存 {saved} 条到数据库")
        
        return posts[:max_count]
    
    async def crawl_all(self, keywords: list):
        """爬取所有关键词"""
        self.db.init_tables()
        
        if not self.page:
            await self.start()
        
        total = 0
        for keyword in keywords:
            posts = await self.crawl(keyword)
            total += len(posts)
            await self.page.wait_for_timeout(2000)
        
        # 显示统计
        stats = self.db.get_stats()
        print(f"\n{'=' * 60}")
        print(f"[STATS] 夜市: {stats['markets_count']} 条, 跑山: {stats['routes_count']} 条")
        print(f"{'=' * 60}")
        
        return total
    
    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.page = None


async def main():
    """交互式爬取"""
    crawler = XHSCrawler()
    await crawler.start()
    
    print("\n" + "=" * 60)
    print("  小红书爬虫 - 交互模式")
    print("  浏览器将保持打开，可以多次爬取")
    print("=" * 60)
    
    keywords = [
        "武汉夜市", "武汉宵夜", "武汉夜市美食",
        "武汉跑山", "武汉周边骑行", "武汉摩旅",
    ]
    
    await crawler.crawl_all(keywords)
    
    print("\n[INFO] 爬取完成，浏览器保持打开")
    print("[INFO] 可以继续执行其他操作，或关闭此窗口退出")


if __name__ == "__main__":
    asyncio.run(main())
