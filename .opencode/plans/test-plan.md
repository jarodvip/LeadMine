# LeadMine 项目全面测试计划

## 📋 测试概述

**项目名称**: LeadMine 线索矿工  
**测试类型**: 全量测试（单元测试 + 集成测试 + API 测试）  
**测试框架**: pytest (后端) + Vitest/Vue Test Utils (前端)  
**测试覆盖率目标**: >80%

---

## 🎯 测试范围

### 1. 后端 API 测试 (优先级: P0)
- [ ] 认证模块 (auth)
- [ ] 线索管理 (leads)
- [ ] 数据处理 (processor)
- [ ] 数据源管理 (resources)

### 2. 核心业务逻辑测试 (优先级: P0)
- [ ] 线索提取算法 (lead_extractor)
- [ ] 数据清洗 (cleaner)
- [ ] 去重算法 (deduplicator)
- [ ] NLP 处理 (nlp_processor)

### 3. 爬虫模块测试 (优先级: P1)
- [ ] 爬虫工厂 (spider_factory)
- [ ] 36氪爬虫 (kr36)
- [ ] 虎嗅爬虫 (huxiu)
- [ ] RSS 解析器 (rss_parser)

### 4. 服务层测试 (优先级: P1)
- [ ] 调度器 (scheduler)
- [ ] 文章服务 (article_service)
- [ ] 数据处理器 (processor)

### 5. 安全测试 (优先级: P0)
- [ ] JWT 认证
- [ ] 权限控制
- [ ] 密码加密
- [ ] XSS 防护

---

## 📁 测试目录结构

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # pytest 配置和 fixtures
│   ├── test_config.py           # 配置测试
│   │
│   ├── api/                     # API 测试
│   │   ├── test_auth.py         # 认证接口测试
│   │   ├── test_leads.py        # 线索管理接口测试
│   │   ├── test_processor.py    # 处理器接口测试
│   │   └── test_resources.py    # 资源管理接口测试
│   │
│   ├── processors/              # 处理器单元测试
│   │   ├── test_lead_extractor.py
│   │   ├── test_cleaner.py
│   │   ├── test_deduplicator.py
│   │   ├── test_nlp_processor.py
│   │   └── test_enricher.py
│   │
│   ├── scrapers/                # 爬虫测试
│   │   ├── test_spider_factory.py
│   │   ├── test_kr36.py
│   │   └── test_huxiu.py
│   │
│   ├── services/                # 服务层测试
│   │   ├── test_scheduler.py
│   │   ├── test_article_service.py
│   │   └── test_processor.py
│   │
│   └── security/                # 安全测试
│       ├── test_jwt.py
│       ├── test_password_hash.py
│       └── test_cors.py
```

---

## 🧪 详细测试用例

### 1. API 测试

#### 1.1 认证接口测试 (`test_auth.py`)

```python
# 测试用例清单
- [x] test_login_success          # 正常登录
- [x] test_login_invalid_credentials  # 错误密码
- [x] test_login_disabled_user    # 禁用用户登录
- [x] test_register_success       # 正常注册
- [x] test_register_duplicate_username  # 重复用户名
- [x] test_register_role_enforcement    # 角色强制为 user
- [x] test_get_current_user       # 获取当前用户信息
- [x] test_token_expiration       # Token 过期
```

#### 1.2 线索管理接口测试 (`test_leads.py`)

```python
- [x] test_get_leads_list         # 获取线索列表
- [x] test_get_leads_with_filter  # 带筛选条件的列表
- [x] test_get_leads_pagination   # 分页测试
- [x] test_get_lead_detail        # 获取线索详情
- [x] test_get_lead_not_found     # 线索不存在
- [x] test_create_lead            # 创建线索
- [x] test_create_lead_invalid    # 创建线索-无效数据
- [x] test_update_lead            # 更新线索
- [x] test_update_lead_not_found  # 更新不存在的线索
- [x] test_delete_lead            # 删除线索
- [x] test_delete_lead_not_found  # 删除不存在的线索
- [x] test_get_dashboard_stats    # 获取仪表盘统计
- [x] test_export_leads_csv       # 导出线索 CSV
- [x] test_batch_update_status    # 批量更新状态
- [x] test_batch_assign           # 批量分配
- [x] test_batch_delete           # 批量删除
```

#### 1.3 处理器接口测试 (`test_processor.py`)

```python
- [x] test_process_article        # 处理单篇文章
- [x] test_process_articles_batch # 批量处理文章
- [x] test_enrich_lead            # 线索信息补充
- [x] test_get_pending_stats      # 获取待处理统计
```

#### 1.4 资源管理接口测试 (`test_resources.py`)

```python
- [x] test_get_sources_list       # 获取数据源列表
- [x] test_create_source          # 创建数据源
- [x] test_update_source          # 更新数据源
- [x] test_delete_source          # 删除数据源
- [x] test_trigger_crawl          # 手动触发爬取
```

### 2. 核心业务逻辑测试

#### 2.1 线索提取测试 (`test_lead_extractor.py`)

```python
- [x] test_extract_financing_lead         # 提取融资事件线索
- [x] test_extract_acquisition_lead       # 提取并购事件线索
- [x] test_extract_product_lead           # 提取产品发布线索
- [x] test_extract_expansion_lead         # 提取扩产线索
- [x] test_extract_procurement_lead       # 提取招标采购线索
- [x] test_extract_no_lead                # 无有效线索的文章
- [x] test_extract_amount_parsing         # 金额解析
- [x] test_extract_company_name           # 公司名称提取
- [x] test_lead_confidence_calculation    # 置信度计算
```

#### 2.2 数据清洗测试 (`test_cleaner.py`)

```python
- [x] test_clean_html_tags          # 清洗 HTML 标签
- [x] test_clean_whitespace         # 清洗多余空白
- [x] test_clean_special_chars      # 清洗特殊字符
- [x] test_normalize_text           # 文本规范化
```

#### 2.3 去重算法测试 (`test_deduplicator.py`)

```python
- [x] test_simhash_generation       # SimHash 生成
- [x] test_duplicate_detection      # 重复检测
- [x] test_hamming_distance         # 汉明距离计算
- [x] test_similarity_threshold     # 相似度阈值
- [x] test_redis_deduplication      # Redis 去重
```

#### 2.4 NLP 处理测试 (`test_nlp_processor.py`)

```python
- [x] test_tokenize_text            # 分词测试
- [x] test_extract_keywords         # 关键词提取
- [x] test_extract_entities         # 实体识别
- [x] test_sentiment_analysis       # 情感分析
```

### 3. 爬虫模块测试

#### 3.1 爬虫工厂测试 (`test_spider_factory.py`)

```python
- [x] test_get_spider_by_type       # 根据类型获取爬虫
- [x] test_spider_not_found         # 爬虫不存在
- [x] test_crawl_source             # 爬取数据源
```

#### 3.2 具体爬虫测试

```python
# test_kr36.py
- [x] test_kr36_fetch_api           # API 抓取模式
- [x] test_kr36_fetch_html          # HTML 抓取模式
- [x] test_kr36_parse_article       # 文章解析
- [x] test_kr36_error_handling      # 错误处理

# test_huxiu.py
- [x] test_huxiu_fetch_api          # API 抓取模式
- [x] test_huxiu_fetch_html         # HTML 抓取模式
- [x] test_huxiu_parse_article      # 文章解析
- [x] test_huxiu_error_handling     # 错误处理
```

### 4. 服务层测试

#### 4.1 调度器测试 (`test_scheduler.py`)

```python
- [x] test_scheduler_start          # 启动调度器
- [x] test_scheduler_stop           # 停止调度器
- [x] test_add_crawl_task           # 添加爬取任务
- [x] test_remove_crawl_task        # 移除爬取任务
- [x] test_trigger_manual_crawl     # 手动触发爬取
```

### 5. 安全测试

#### 5.1 JWT 测试 (`test_jwt.py`)

```python
- [x] test_token_creation           # Token 创建
- [x] test_token_validation         # Token 验证
- [x] test_token_expiration         # Token 过期
- [x] test_invalid_token            # 无效 Token
- [x] test_tampered_token           # 篡改 Token
```

#### 5.2 密码加密测试 (`test_password_hash.py`)

```python
- [x] test_password_hash_generation # 密码哈希生成
- [x] test_password_verification    # 密码验证
- [x] test_password_hash_uniqueness # 哈希唯一性
- [x] test_weak_password_detection  # 弱密码检测
```

#### 5.3 CORS 测试 (`test_cors.py`)

```python
- [x] test_allowed_origins          # 允许的源
- [x] test_disallowed_origins       # 禁止的源
- [x] test_preflight_request        # 预检请求
```

---

## 📊 测试数据准备

### 测试数据库配置

```python
# conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base

# 使用 SQLite 内存数据库进行测试
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db):
    from app.main import app
    from app.core.database import get_db
    
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    from fastapi.testclient import TestClient
    return TestClient(app)

@pytest.fixture
def test_user(client):
    """创建测试用户"""
    response = client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!"
    })
    return response.json()

@pytest.fixture
def auth_headers(client, test_user):
    """获取认证头"""
    response = client.post("/api/v1/auth/login", data={
        "username": "testuser",
        "password": "TestPass123!"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

### 测试样本数据

```python
# test_data.py

# 测试文章样本
SAMPLE_ARTICLES = [
    {
        "title": "36氪首发｜人工智能公司完成1亿元A轮融资",
        "content": "人工智能公司今日宣布完成1亿元人民币A轮融资，本轮融资由红杉资本领投。公司表示将用于技术研发和市场拓展。",
        "url": "https://36kr.com/p/test1",
        "source_name": "36氪"
    },
    {
        "title": "腾讯收购某游戏公司",
        "content": "腾讯今日宣布收购某游戏公司，收购金额未披露。这是腾讯在游戏领域的又一重要布局。",
        "url": "https://example.com/news2",
        "source_name": "虎嗅"
    },
    {
        "title": "某公司发布新一代智能手机",
        "content": "某公司今日发布新一代智能手机，搭载最新处理器，售价4999元起。",
        "url": "https://example.com/news3",
        "source_name": "测试源"
    }
]

# 预期提取结果
EXPECTED_LEADS = [
    {
        "event_type": "financing",
        "company_name": "人工智能公司",
        "event_amount": "1亿元",
        "confidence": 85
    },
    {
        "event_type": "acquisition",
        "company_name": "某游戏公司",
        "event_amount": None,
        "confidence": 75
    }
]
```

---

## 🚀 测试执行计划

### 阶段 1: 基础配置 (Day 1)
- [ ] 创建 tests/ 目录结构
- [ ] 配置 pytest 和 conftest.py
- [ ] 创建测试数据库配置
- [ ] 创建常用 fixtures

### 阶段 2: API 测试 (Day 2-3)
- [ ] 认证接口测试
- [ ] 线索管理接口测试
- [ ] 处理器接口测试
- [ ] 资源管理接口测试

### 阶段 3: 业务逻辑测试 (Day 4-5)
- [ ] 线索提取测试
- [ ] 数据清洗测试
- [ ] 去重算法测试
- [ ] NLP 处理测试

### 阶段 4: 爬虫测试 (Day 6)
- [ ] 爬虫工厂测试
- [ ] 36氪爬虫测试
- [ ] 虎嗅爬虫测试

### 阶段 5: 服务层和安全测试 (Day 7)
- [ ] 调度器测试
- [ ] JWT 测试
- [ ] 密码加密测试
- [ ] CORS 测试

### 阶段 6: 集成测试和覆盖率检查 (Day 8)
- [ ] 端到端流程测试
- [ ] 生成覆盖率报告
- [ ] 补充缺失的测试用例

---

## 📈 测试覆盖率目标

| 模块 | 目标覆盖率 | 当前覆盖率 |
|------|-----------|-----------|
| API 层 | 90% | 0% |
| 业务逻辑 | 85% | 0% |
| 爬虫模块 | 70% | 0% |
| 服务层 | 80% | 0% |
| 安全模块 | 95% | 0% |
| **总体** | **80%** | **0%** |

---

## ⚠️ 测试注意事项

### 1. 外部服务依赖
- 使用 mock 处理 Elasticsearch 调用
- 使用 mock 处理 Redis 调用
- 使用 mock 处理外部 API（如爱企查）
- 使用测试数据库而非生产数据库

### 2. 异步测试
- 使用 pytest-asyncio 处理异步函数
- 使用 AsyncClient 测试异步接口

### 3. 爬虫测试
- 使用 responses 库 mock HTTP 请求
- 使用本地 HTML 文件作为测试数据
- 避免在测试中实际访问目标网站

### 4. 性能测试
- 添加性能基准测试
- 测试大数据量下的响应时间
- 测试并发请求处理能力

---

## 🔧 测试工具配置

### pytest 配置

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    security: marks tests as security tests
```

### 覆盖率配置

```ini
# .coveragerc
[run]
source = app
omit = 
    */tests/*
    */test_*
    */venv/*
    */migrations/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
    class .*\bProtocol\):
    @(abc\.)?abstractmethod

[html]
directory = htmlcov
```

---

## 📋 测试执行命令

```bash
# 运行所有测试
pytest

# 运行特定模块
pytest tests/api/test_auth.py
pytest tests/processors/

# 运行带标记的测试
pytest -m "not slow"
pytest -m security

# 生成覆盖率报告
pytest --cov=app --cov-report=html

# 调试模式
pytest -v --pdb

# 并行测试
pytest -n auto
```

---

## 🎯 验收标准

- [ ] 所有 P0 级别功能都有对应的测试用例
- [ ] 测试通过率达到 100%
- [ ] 代码覆盖率达到 80% 以上
- [ ] 安全测试全部通过
- [ ] 性能测试满足性能要求
- [ ] CI/CD 集成测试通过

---

**计划创建日期**: 2026-02-19  
**测试工程师**: Claude (Test Engineer Mode)  
**预计完成时间**: 8 个工作日
