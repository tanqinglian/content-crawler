# 小红书爬虫

爬取武汉夜市和跑山路线数据，持久化到本地SQLite数据库。

## 功能特性

- ✅ 扫码登录（自动保存cookies）
- ✅ 关键词搜索
- ✅ 自动解析夜市/跑山信息
- ✅ SQLite本地持久化
- ✅ 去重处理
- ✅ 爬取日志

## 安装

```bash
# 安装依赖
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install chromium
```

## 使用方法

### 1. 首次运行（需要扫码登录）

```bash
python main.py
```

程序会打开浏览器，等待你扫码登录小红书。登录成功后，cookies会自动保存。

### 2. 后续运行（自动登录）

再次运行时，程序会自动加载已保存的cookies，无需重复登录。

### 3. 自定义关键词

编辑 `main.py` 中的 `keywords` 列表：

```python
keywords = [
    "武汉夜市",
    "武汉跑山",
    # 添加更多关键词...
]
```

## 项目结构

```
xiaohongshu-crawler/
├── main.py              # 主程序
├── requirements.txt     # 依赖
├── src/
│   ├── login.py        # 登录模块
│   ├── search.py       # 搜索模块
│   ├── parser.py       # 解析模块
│   └── storage.py      # 存储模块
├── tests/              # 测试用例
│   ├── test_login.py
│   ├── test_search.py
│   ├── test_parser.py
│   └── test_storage.py
└── data/               # 数据存储
    ├── xiaohongshu.db  # SQLite数据库
    └── cookies.json    # 登录cookies
```

## 数据库结构

### markets 表（夜市）

| 字段 | 说明 |
|------|------|
| id | 主键 |
| title | 帖子标题 |
| content | 内容 |
| address | 地址 |
| open_hours | 营业时间 |
| images | 图片URL（JSON） |
| rating | 评分 |
| author | 作者 |
| likes | 点赞数 |
| source_url | 原帖链接 |

### routes 表（跑山）

| 字段 | 说明 |
|------|------|
| id | 主键 |
| title | 帖子标题 |
| content | 内容 |
| distance | 里程 |
| duration | 时长 |
| difficulty | 难度 |
| start_point | 起点 |
| end_point | 终点 |
| images | 图片URL（JSON） |
| author | 作者 |
| likes | 点赞数 |
| source_url | 原帖链接 |

## 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_storage.py -v
```

## 注意事项

1. **频率控制** - 程序已内置请求间隔，避免触发反爬
2. **登录状态** - cookies有效期约7天，过期需重新登录
3. **数据去重** - 相同URL的帖子会更新而非重复插入
4. **仅用于学习** - 请遵守小红书用户协议，合理使用

## 开发信息

- **开发模式：** TDD（测试驱动开发）
- **技术栈：** Python + Playwright + SQLite
- **开发时间：** 2026-03-04
