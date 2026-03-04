# ETL测试说明

## 运行测试

### 1. 运行所有测试
```bash
cd xiaohongshu-crawler/etl
python -m pytest tests/ -v
```

### 2. 运行单个测试文件
```bash
python -m pytest tests/test_transform.py -v
```

### 3. 运行带MySQL的测试
```bash
MYSQL_TEST=1 python -m pytest tests/ -v
```

## 测试覆盖

- ✅ 夜市信息解析
- ✅ 跑山路线解析
- ✅ MySQL连接
- ✅ 数据导入

## TDD流程

1. **红灯**：运行测试 → 失败 ❌
2. **绿灯**：修改代码 → 通过 ✅
3. **重构**：优化代码 → 仍通过 ✅
