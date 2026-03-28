# WeChat RSSHub Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `wechat` data sources crawl successfully through the existing RSS ingestion path while preserving `wechat` article classification end to end.

**Architecture:** Reuse the current `RSSParser` implementation instead of adding a new crawler. Extend `SpiderFactory` so `wechat` dispatches to `RSSParser`, and make `RSSParser` emit `source_type` from the incoming source config instead of hardcoding `rss`. Verify behavior with focused processor and factory regression tests.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy enums, pytest, unittest.mock, feedparser, requests

---

## File Structure

### Existing files to modify
- `backend/scrapers/spider_factory.py`
  - Keep factory ownership of source-type dispatch.
  - Change only the routing condition so `wechat` shares the RSS parser path.
- `backend/app/processors/rss_parser.py`
  - Keep feed fetching/parsing behavior unchanged.
  - Add a parser attribute for the configured source type and emit it in parsed article dicts.
- `backend/tests/processors/test_rss_parser.py`
  - Replace the current shallow parser tests with one real regression test that proves configured source type is preserved.
- `backend/tests/api/test_resources.py`
  - Add an API-level crawl regression proving a stored `wechat` source can be triggered and saved without unsupported-type behavior.

### Existing files to create/update for test coverage
- Create: `backend/tests/scrapers/test_spider_factory.py`
  - Add a focused factory-level regression test for `wechat` dispatch to `RSSParser`.

### Files explicitly out of scope
- `web/src/views/Sources.vue`
- `backend/app/api/resources.py`
- `backend/app/services/article_service.py`
- `backend/app/models/models.py`

These already support the approved design or are intentionally unchanged for this iteration.

---

### Task 1: Add factory regression coverage for `wechat`

**Files:**
- Create: `backend/tests/scrapers/test_spider_factory.py`
- Modify later: `backend/scrapers/spider_factory.py`
- Check reference: `backend/scrapers/spider_factory.py:1-95`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/scrapers/test_spider_factory.py` with this content:

```python
from unittest.mock import patch

from app.models.models import SourceTypeEnum
from scrapers.spider_factory import SpiderFactory


def test_crawl_source_routes_wechat_through_rss_parser():
    source_config = {
        "name": "微信公众号",
        "type": SourceTypeEnum.wechat,
        "url": "https://rsshub.example.com/wechat/mp/test-account",
    }
    expected_articles = [{"title": "微信文章", "source_type": "wechat"}]

    with patch("scrapers.spider_factory.RSSParser") as mock_parser_class:
        mock_parser = mock_parser_class.return_value
        mock_parser.fetch.return_value = expected_articles

        result = SpiderFactory.crawl_source(source_config)

    mock_parser_class.assert_called_once_with(source_config)
    mock_parser.fetch.assert_called_once_with()
    assert result == expected_articles
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/backend && pytest tests/scrapers/test_spider_factory.py::test_crawl_source_routes_wechat_through_rss_parser -v
```

Expected:
- `FAIL`
- Failure at `mock_parser_class.assert_called_once_with(source_config)` or `assert result == expected_articles`
- Current behavior returns `[]` because `SpiderFactory.crawl_source()` only routes `rss`

- [ ] **Step 3: Write minimal implementation**

In `backend/scrapers/spider_factory.py`, change the RSS branch from:

```python
            # RSS订阅
            elif source_type == "rss":
                parser = RSSParser(source_config)
                return parser.fetch()
```

To:

```python
            # RSS订阅 / 微信RSSHub
            elif source_type in {"rss", "wechat"}:
                parser = RSSParser(source_config)
                return parser.fetch()
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/backend && pytest tests/scrapers/test_spider_factory.py::test_crawl_source_routes_wechat_through_rss_parser -v
```

Expected:
- `PASS`
- `1 passed`

- [ ] **Step 5: Commit**

Run:

```bash
cd /Users/jarod/Dev/LeadMine && git add backend/tests/scrapers/test_spider_factory.py backend/scrapers/spider_factory.py && git commit -m "test: cover wechat spider dispatch"
```

Expected:
- New commit created containing only the factory test and routing change

---

### Task 2: Add parser regression coverage for source-type preservation

**Files:**
- Modify: `backend/tests/processors/test_rss_parser.py`
- Modify later: `backend/app/processors/rss_parser.py`
- Check reference: `backend/app/processors/rss_parser.py:16-119`

- [ ] **Step 1: Write the failing test**

Append this test to `backend/tests/processors/test_rss_parser.py`:

```python
def test_parse_entry_preserves_configured_wechat_source_type():
    from app.processors.rss_parser import RSSParser

    parser = RSSParser(
        {
            "url": "https://rsshub.example.com/wechat/mp/test-account",
            "name": "微信公众号",
            "type": "wechat",
        }
    )

    entry = MagicMock()
    entry.title = "微信文章"
    entry.summary = "<p>摘要</p>"
    entry.link = "https://mp.weixin.qq.com/s/test"
    entry.published = "2026-03-28T10:00:00Z"
    entry.author = "LeadMine"

    article = parser._parse_entry(entry)

    assert article is not None
    assert article["source_type"] == "wechat"
    assert article["source_name"] == "微信公众号"
    assert article["source_url"] == "https://mp.weixin.qq.com/s/test"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/backend && pytest tests/processors/test_rss_parser.py::test_parse_entry_preserves_configured_wechat_source_type -v
```

Expected:
- `FAIL`
- Assertion diff showing `rss != wechat`
- This proves the regression exists before changing production code

- [ ] **Step 3: Write minimal implementation**

In `backend/app/processors/rss_parser.py`, update `__init__` from:

```python
    def __init__(self, source_config: Dict):
        self.config = source_config
        self.url = source_config.get("url")
        self.source_name = source_config.get("name", "RSS")
```

To:

```python
    def __init__(self, source_config: Dict):
        self.config = source_config
        self.url = source_config.get("url")
        self.source_name = source_config.get("name", "RSS")

        source_type = source_config.get("type", "rss")
        if hasattr(source_type, "value"):
            source_type = source_type.value
        self.source_type = source_type or "rss"
```

Then update `_parse_entry()` from:

```python
            return {
                "title": self._clean_text(getattr(entry, "title", "无标题")),
                "content": self._clean_html(content),
                "summary": self._clean_text(getattr(entry, "summary", ""))[:500],
                "author": author,
                "source_name": self.source_name,
                "source_url": link,
                "published_at": published_at,
                "source_type": "rss",
            }
```

To:

```python
            return {
                "title": self._clean_text(getattr(entry, "title", "无标题")),
                "content": self._clean_html(content),
                "summary": self._clean_text(getattr(entry, "summary", ""))[:500],
                "author": author,
                "source_name": self.source_name,
                "source_url": link,
                "published_at": published_at,
                "source_type": self.source_type,
            }
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/backend && pytest tests/processors/test_rss_parser.py::test_parse_entry_preserves_configured_wechat_source_type -v
```

Expected:
- `PASS`
- `1 passed`

- [ ] **Step 5: Commit**

Run:

```bash
cd /Users/jarod/Dev/LeadMine && git add backend/tests/processors/test_rss_parser.py backend/app/processors/rss_parser.py && git commit -m "test: preserve rss parser source type"
```

Expected:
- New commit created containing only the parser regression test and minimal parser change

---

### Task 3: Add API-level regression for WeChat crawl behavior

**Files:**
- Modify: `backend/tests/api/test_resources.py`
- Check reference: `backend/app/api/resources.py:224-247`
- Check reference: `backend/app/services/scheduler.py:113-158`
- Check reference: `backend/app/services/article_service.py:16-85`

- [ ] **Step 1: Write the failing test**

Append this test to `backend/tests/api/test_resources.py`:

```python
from unittest.mock import patch


def test_trigger_crawl_wechat_source_uses_rss_parser_path(client, auth_headers, db):
    source = DataSource(
        name="微信公众号测试",
        type=SourceTypeEnum.wechat,
        url="https://rsshub.example.com/wechat/mp/test-account",
        enabled=True,
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    with patch(
        "app.services.scheduler.SpiderFactory.crawl_source",
        return_value=[
            {
                "title": "微信文章",
                "content": "公众号内容",
                "summary": "摘要",
                "author": "LeadMine",
                "source_name": source.name,
                "source_url": "https://mp.weixin.qq.com/s/test",
                "published_at": datetime.now(),
                "source_type": "wechat",
            }
        ],
    ):
        response = client.post(
            f"/api/v1/sources/{source.id}/crawl",
            headers=auth_headers,
        )

    assert response.status_code == 200
    payload = response.json()["result"]
    assert payload["status"] == "success"

    article = db.query(Article).filter(Article.source_name == source.name).first()
    assert article is not None
    assert article.source_type == SourceTypeEnum.wechat
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/backend && pytest tests/api/test_resources.py::test_trigger_crawl_wechat_source_uses_rss_parser_path -v
```

Expected:
- `FAIL`
- Failure before implementation if the crawl path still treats `wechat` as unsupported or if persisted article type does not remain `wechat`

- [ ] **Step 3: Keep implementation minimal**

Do not add new API branches, scheduler branches, or WeChat-only storage code. The only production changes for this plan should remain:

```python
# backend/scrapers/spider_factory.py
elif source_type in {"rss", "wechat"}:
    parser = RSSParser(source_config)
    return parser.fetch()

# backend/app/processors/rss_parser.py
source_type = source_config.get("type", "rss")
if hasattr(source_type, "value"):
    source_type = source_type.value
self.source_type = source_type or "rss"

# in _parse_entry()
"source_type": self.source_type,
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/backend && pytest tests/api/test_resources.py::test_trigger_crawl_wechat_source_uses_rss_parser_path -v
```

Expected:
- `PASS`
- `1 passed`

- [ ] **Step 5: Commit**

Run:

```bash
cd /Users/jarod/Dev/LeadMine && git add backend/tests/api/test_resources.py backend/scrapers/spider_factory.py backend/app/processors/rss_parser.py && git commit -m "test: cover wechat rsshub crawl behavior"
```

Expected:
- New commit created containing the API regression and minimal production support already defined in earlier tasks

---

### Task 4: Run integrated verification for the approved scope

**Files:**
- Verify: `backend/tests/scrapers/test_spider_factory.py`
- Verify: `backend/tests/processors/test_rss_parser.py`
- Verify: `backend/tests/api/test_resources.py`
- Verify existing code path: `backend/scrapers/spider_factory.py`, `backend/app/processors/rss_parser.py`

- [ ] **Step 1: Run the focused regression suite**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/backend && pytest tests/scrapers/test_spider_factory.py tests/processors/test_rss_parser.py tests/api/test_resources.py -v
```

Expected:
- `PASS`
- New factory regression, parser regression, and API regression all green
- No import or fixture failures

- [ ] **Step 2: Run the existing source API regression file**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/backend && pytest tests/api/test_resources.py -v
```

Expected:
- `PASS`
- Existing source update regressions still green
- Confirms the new `wechat` path did not break source CRUD-related behavior

- [ ] **Step 3: Verify manual smoke-test procedure in local environment**

Run the app stack, then exercise the API with an existing auth token or local Swagger session.

Manual verification checklist:

```text
1. Create a data source:
   - name: 微信公众号测试
   - type: wechat
   - url: a valid RSSHub wechat feed URL
   - enabled: true
2. Trigger POST /api/v1/sources/{id}/crawl
3. Confirm the crawl no longer returns the unsupported-type path
4. Query GET /api/v1/articles?source_name=微信公众号测试
5. Confirm returned articles show source_type = wechat in API payload or persisted DB row
```

Expected:
- Crawl completes through the RSS parser path
- Created articles remain classified as `wechat`

- [ ] **Step 4: Commit final verification-only checkpoint if needed**

If verification did not require code changes, do not create another commit.

If manual verification required a tiny test-only adjustment, run:

```bash
cd /Users/jarod/Dev/LeadMine && git add <exact files changed> && git commit -m "test: finalize wechat rsshub ingestion coverage"
```

Expected:
- Either no commit because verification was clean, or one small final commit containing only verification-related test edits

---

## Spec Coverage Check

- `wechat` remains first-class source type:
  - Covered by Task 1 because routing changes without changing model/API semantics.
  - Covered by Task 3 because API-triggered crawl persists `wechat`-typed articles.
- Reuse `RSSParser` for `wechat`:
  - Covered by Task 1.
- Preserve article `source_type = wechat` when configured source type is `wechat`:
  - Covered by Task 2 and Task 3.
- Keep full RSSHub URL contract with no new validation/generator:
  - Covered by omission of any API/schema/UI changes in all tasks.
- Reuse current RSS-style error handling:
  - Covered by minimal implementation in Task 2, which changes only emitted `source_type` and leaves fetch/parse error handling untouched.
- Manual smoke test from spec:
  - Covered by Task 4.

## Placeholder Scan

- No `TODO`, `TBD`, or “implement later” markers remain.
- Every production code step includes an exact replacement snippet.
- Every test step includes the exact test code and exact pytest command.

## Type Consistency Check

- `source_type` is consistently referenced as `wechat` / `rss` string values in parser output.
- Factory routing accepts enum-backed `type` values because `crawl_source()` already normalizes `.value` before branching.
- Test names and commands match the functions defined in the plan.
