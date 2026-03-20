# Coverage Uplift (Targeted) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不改动业务行为的前提下，定向提升 `resources.py` 与 `processor.py` 相关覆盖率，并保持全量测试通过。

**Architecture:** 采用“测试先行 + 最小实现调整（仅必要时）”策略，优先补 API/service 层行为测试，覆盖成功路径、参数校验、错误分支与边界条件。通过新增独立测试文件承接覆盖率提升，避免修改无关模块。若出现行为与测试不一致，先修正测试假设，再做最小代码改动。

**Tech Stack:** Python 3.9/3.11, pytest, pytest-cov, FastAPI TestClient, SQLAlchemy

---

## File Structure & Responsibilities

- Modify: `backend/tests/conftest.py`
  - 责任：统一测试数据库隔离与会话策略，保证并发/全量执行稳定。
- Create: `backend/tests/api/test_resources.py`
  - 责任：覆盖 `app/api/resources.py` 的文章与数据源 API 行为。
- Create: `backend/tests/api/test_processor_api.py`
  - 责任：覆盖 `app/api/processor.py` 的 API 层分支与错误处理。
- Create: `backend/tests/services/test_data_processor_real.py`
  - 责任：覆盖 `app/services/processor.py` 的核心业务路径（process_article / process_pending_articles / enrich_lead）。
- (Optional, only if needed) Modify: `backend/app/services/processor.py`
  - 责任：仅在测试暴露真实缺陷时做最小修复，不做重构。

---

### Task 1: 固化测试基线与目标快照

**Files:**
- Modify: `backend/tests/conftest.py`
- Test: `backend/tests/performance/test_performance.py`

- [ ] **Step 1: 运行当前覆盖率并记录基线**

Run: `python3 -m pytest backend/tests --cov=app --cov-report=term-missing -q`
Expected: PASS，记录当前总覆盖率与低覆盖热点（`app/api/resources.py`, `app/services/processor.py`）。

- [ ] **Step 2: 运行并发回归测试（防止基线回退）**

Run: `python3 -m pytest backend/tests/performance/test_performance.py::TestConcurrentAccess::test_concurrent_create_lead -q`
Expected: PASS。

- [ ] **Step 3: 提交基线稳定化改动（若有）**

```bash
git add backend/tests/conftest.py
git commit -m "test: stabilize test db isolation for coverage run"
```

---

### Task 2: 提升 resources API 覆盖率

**Files:**
- Create: `backend/tests/api/test_resources.py`
- Modify (only if bug exposed): `backend/app/api/resources.py`
- Test: `backend/tests/api/test_resources.py`

- [ ] **Step 1: 写失败测试 - 文章列表过滤与分页**

```python
def test_get_articles_filters_and_pagination(client, auth_headers):
    # create sample articles in different categories/sources
    # call /api/v1/articles with source_name/category/keyword/page/page_size
    # assert total/page/page_size/data length and ordering
```

- [ ] **Step 2: 运行单测确认失败（RED）**

Run: `python3 -m pytest backend/tests/api/test_resources.py::test_get_articles_filters_and_pagination -q`
Expected: FAIL（断言失败或数据不匹配）。

- [ ] **Step 3: 写最小实现/调整测试数据使其通过（GREEN）**

优先只调整测试搭建；仅当暴露真实缺陷时，最小修改 `resources.py`。

- [ ] **Step 4: 运行单测确认通过**

Run: `python3 -m pytest backend/tests/api/test_resources.py::test_get_articles_filters_and_pagination -q`
Expected: PASS。

- [ ] **Step 5: 写失败测试 - 数据源列表筛选与统计字段**

```python
def test_get_sources_with_enabled_filter_and_stats(client, auth_headers):
    # create enabled/disabled sources and today articles
    # call /api/v1/sources?enabled=true
    # assert today_count/success_rate fields exist and values are expected
```

- [ ] **Step 6: 运行单测确认失败（RED）**

Run: `python3 -m pytest backend/tests/api/test_resources.py::test_get_sources_with_enabled_filter_and_stats -q`
Expected: FAIL。

- [ ] **Step 7: 写最小实现（如有必要）并通过（GREEN）**

Run: `python3 -m pytest backend/tests/api/test_resources.py::test_get_sources_with_enabled_filter_and_stats -q`
Expected: PASS。

- [ ] **Step 8: 写失败测试 - 手动触发抓取异常路径**

```python
def test_trigger_crawl_returns_404_or_400_when_invalid_source(client, auth_headers):
    # source not found -> 404
    # source disabled -> 400
```

- [ ] **Step 9: 运行并修复到通过**

Run: `python3 -m pytest backend/tests/api/test_resources.py -q`
Expected: 全 PASS。

- [ ] **Step 10: 提交**

```bash
git add backend/tests/api/test_resources.py backend/app/api/resources.py
git commit -m "test: add resources api coverage for list stats and crawl branches"
```

---

### Task 3: 提升 processor API 覆盖率

**Files:**
- Create: `backend/tests/api/test_processor_api.py`
- Modify (only if bug exposed): `backend/app/api/processor.py`
- Test: `backend/tests/api/test_processor_api.py`

- [ ] **Step 1: 写失败测试 - process_single_article 404 分支**

```python
def test_process_single_article_not_found_returns_404(client, auth_headers):
    resp = client.post("/api/v1/processor/articles/999999/process", headers=auth_headers)
    assert resp.status_code == 404
```

- [ ] **Step 2: 运行确认失败（RED）**

Run: `python3 -m pytest backend/tests/api/test_processor_api.py::test_process_single_article_not_found_returns_404 -q`
Expected: FAIL。

- [ ] **Step 3: 最小实现后通过（GREEN）**

Run: `python3 -m pytest backend/tests/api/test_processor_api.py::test_process_single_article_not_found_returns_404 -q`
Expected: PASS。

- [ ] **Step 4: 写失败测试 - process_pending_articles limit 校验**

```python
def test_process_pending_articles_limit_validation(client, auth_headers):
    assert client.post("/api/v1/processor/articles/process?limit=0", headers=auth_headers).status_code == 400
    assert client.post("/api/v1/processor/articles/process?limit=201", headers=auth_headers).status_code == 400
```

- [ ] **Step 5: 运行并修复到通过（GREEN）**

Run: `python3 -m pytest backend/tests/api/test_processor_api.py::test_process_pending_articles_limit_validation -q`
Expected: PASS。

- [ ] **Step 6: 写失败测试 - enrich_lead 错误映射**

```python
def test_enrich_lead_not_found_returns_404(client, auth_headers, monkeypatch):
    # monkeypatch data_processor.enrich_lead -> {"error": "线索不存在"}
    # assert 404 and detail
```

- [ ] **Step 7: 运行并修复到通过**

Run: `python3 -m pytest backend/tests/api/test_processor_api.py -q`
Expected: 全 PASS。

- [ ] **Step 8: 提交**

```bash
git add backend/tests/api/test_processor_api.py backend/app/api/processor.py
git commit -m "test: increase processor api coverage for validation and error branches"
```

---

### Task 4: 提升 data processor service 覆盖率

**Files:**
- Create: `backend/tests/services/test_data_processor_real.py`
- Modify (only if bug exposed): `backend/app/services/processor.py`
- Test: `backend/tests/services/test_data_processor_real.py`

- [ ] **Step 1: 写失败测试 - process_article 文章不存在**

```python
def test_process_article_returns_error_when_not_found(monkeypatch):
    # mock SessionLocal/query().first() -> None
    # assert result == {"error": "文章不存在"}
```

- [ ] **Step 2: 运行确认失败（RED）**

Run: `python3 -m pytest backend/tests/services/test_data_processor_real.py::test_process_article_returns_error_when_not_found -q`
Expected: FAIL。

- [ ] **Step 3: 最小实现后通过（GREEN）**

Run: `python3 -m pytest backend/tests/services/test_data_processor_real.py::test_process_article_returns_error_when_not_found -q`
Expected: PASS。

- [ ] **Step 4: 写失败测试 - process_article 已处理分支**

```python
def test_process_article_returns_message_when_already_processed(monkeypatch):
    # mock article.status == "processed"
    # assert {"message": "文章已处理"}
```

- [ ] **Step 5: 运行并修复到通过**

Run: `python3 -m pytest backend/tests/services/test_data_processor_real.py::test_process_article_returns_message_when_already_processed -q`
Expected: PASS。

- [ ] **Step 6: 写失败测试 - process_pending_articles 统计聚合**

```python
def test_process_pending_articles_aggregates_results(monkeypatch):
    # mock 3 pending articles and mock process_article returns one duplicate, one fail, one success
    # assert total/success/failed/duplicates/leads_extracted
```

- [ ] **Step 7: 运行并修复到通过**

Run: `python3 -m pytest backend/tests/services/test_data_processor_real.py::test_process_pending_articles_aggregates_results -q`
Expected: PASS。

- [ ] **Step 8: 写失败测试 - enrich_lead 不存在与 enrich 成功路径**

```python
def test_enrich_lead_not_found(monkeypatch):
    # assert {"error": "线索不存在"}

def test_enrich_lead_success_updates_score(monkeypatch):
    # mock enricher.enrich returns company info, verify enriched=True and score/grade/follow_up_hint returned
```

- [ ] **Step 9: 运行并修复到通过**

Run: `python3 -m pytest backend/tests/services/test_data_processor_real.py -q`
Expected: 全 PASS。

- [ ] **Step 10: 提交**

```bash
git add backend/tests/services/test_data_processor_real.py backend/app/services/processor.py
git commit -m "test: add data processor service branch coverage"
```

---

### Task 5: 全量回归与覆盖率验收

**Files:**
- Test: `backend/tests/**`

- [ ] **Step 1: 运行全量测试+覆盖率**

Run: `python3 -m pytest backend/tests --cov=app --cov-report=term-missing -q`
Expected: 全 PASS，输出 coverage。

- [ ] **Step 2: 运行关键回归测试**

Run: `python3 -m pytest backend/tests/integration/test_integration.py backend/tests/performance/test_performance.py -q`
Expected: PASS。

- [ ] **Step 3: 记录覆盖率结果并确认目标达成**

目标：
- `app/api/resources.py` 覆盖率较基线显著提升
- `app/services/processor.py` 覆盖率较基线显著提升
- 总覆盖率不下降

- [ ] **Step 4: 最终提交**

```bash
git add backend/tests backend/app
git commit -m "test: targeted coverage uplift for resources and processor"
```

---

## Validation Commands (Final Checklist)

- `python3 -m pytest backend/tests/api/test_resources.py -q`
- `python3 -m pytest backend/tests/api/test_processor_api.py -q`
- `python3 -m pytest backend/tests/services/test_data_processor_real.py -q`
- `python3 -m pytest backend/tests --cov=app --cov-report=term-missing -q`

All must pass before declaring completion.
