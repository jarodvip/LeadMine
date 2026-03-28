# RSSHub WeChat Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `wechat` data sources crawl successfully through the existing RSSHub/RSS pipeline while preserving `wechat` classification on stored articles.

**Architecture:** Keep `wechat` as a first-class source type in storage and APIs, but treat it as a dispatch alias to the existing `RSSParser` crawl path. Preserve the configured source type through parsing and persistence, then lock the behavior in with focused crawler/parser tests and one API smoke test.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy, pytest, requests, feedparser

---

## File map

### Existing files to modify
- `backend/scrapers/spider_factory.py`
  - Add `wechat` to the supported RSS-backed source types in crawler dispatch.
- `backend/app/processors/rss_parser.py`
  - Derive emitted `source_type` from input config instead of hardcoding `rss`.
- `backend/tests/scrapers/test_spider_factory.py`
  - Add targeted regression coverage for `wechat` dispatch.
- `backend/tests/processors/test_rss_parser.py`
  - Add focused parsing coverage for preserved `source_type` and empty-URL behavior.
- `backend/tests/api/test_resources.py`
  - Add API/service-level smoke coverage showing a `wechat` source can be triggered through the normal source crawl path.

### Existing files to inspect while implementing
- `backend/app/services/scheduler.py`
  - Confirms source crawling always enters `SpiderFactory.crawl_source()`.
- `backend/app/services/article_service.py`
  - Confirms saved article rows already inherit `source.type` from the `DataSource`; do not add duplicate persistence logic unless a failing test proves it is needed.
- `docs/superpowers/specs/2026-03-28-wechat-rsshub-ingestion-design.md`
  - Approved design spec this plan implements.

### No new files required
The design is intentionally small. Do not add new crawler classes, new models, or new UI files.

---

### Task 1: Route `wechat` sources through the RSS parser

**Files:**
- Modify: `backend/scrapers/spider_factory.py`
- Test: `backend/tests/scrapers/test_spider_factory.py`

- [ ] **Step 1: Write the failing dispatch test**

Add this test to `backend/tests/scrapers/test_spider_factory.py`:

```python
from unittest.mock import patch


def test_crawl_source_wechat_uses_rss_parser():
    from scrapers.spider_factory import SpiderFactory

    source = {
        "type": "wechat",
        "url": "https://rsshub.app/wechat/mp/example",
        "name": "微信公众号测试源",
        "config": {},
    }

    with patch("scrapers.spider_factory.RSSParser") as mock_parser:
        parser_instance = mock_parser.return_value
        parser_instance.fetch.return_value = [{"title": "A"}]

        result = SpiderFactory.crawl_source(source)

    mock_parser.assert_called_once_with(source)
    parser_instance.fetch.assert_called_once_with()
    assert result == [{"title": "A"}]
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/backend && pytest tests/scrapers/test_spider_factory.py::test_crawl_source_wechat_uses_rss_parser -v
```

Expected: FAIL because `SpiderFactory.crawl_source()` currently only routes `rss` to `RSSParser`.

- [ ] **Step 3: Write the minimal dispatch change**

Update `backend/scrapers/spider_factory.py` so the RSS-backed branch accepts both `rss` and `wechat`:

```python
    @classmethod
    def crawl_source(cls, source_config: Dict) -> List[Dict]:
        source_type = source_config.get("type")
        if hasattr(source_type, "value"):
            source_type = source_type.value
        source_name = source_config.get("name", "")

        try:
            if source_type == "news":
                spider = cls.get_spider(source_name)
                if spider:
                    return spider.fetch_articles()

            elif source_type in {"rss", "wechat"}:
                parser = RSSParser(source_config)
                return parser.fetch()

            logger.warning(f"不支持的数据源类型: {source_type}")
            return []

        except Exception as e:
            logger.error(f"爬取失败 {source_name}: {e}")
            return []
```

- [ ] **Step 4: Run the focused test to verify it passes**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/backend && pytest tests/scrapers/test_spider_factory.py::test_crawl_source_wechat_uses_rss_parser -v
```

Expected: PASS.

- [ ] **Step 5: Run the nearby spider-factory tests**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/backend && pytest tests/scrapers/test_spider_factory.py -v
```

Expected: PASS with the new `wechat` dispatch regression covered.

- [ ] **Step 6: Commit the dispatch slice**

```bash
git -C /Users/jarod/Dev/LeadMine add backend/scrapers/spider_factory.py backend/tests/scrapers/test_spider_factory.py && git -C /Users/jarod/Dev/LeadMine commit -m "$(cat <<'EOF'
feat: route wechat sources through RSS parser
EOF
)"
```

---

### Task 2: Preserve configured source type inside parsed RSS articles

**Files:**
- Modify: `backend/app/processors/rss_parser.py`
- Test: `backend/tests/processors/test_rss_parser.py`

- [ ] **Step 1: Replace the weak parser test with a failing behavior test**

Add these tests to `backend/tests/processors/test_rss_parser.py`:

```python
from types import SimpleNamespace


def test_parse_entry_preserves_wechat_source_type():
    from app.processors.rss_parser import RSSParser

    parser = RSSParser(
        {
            "type": "wechat",
            "url": "https://rsshub.app/wechat/mp/example",
            "name": "微信公众号测试源",
        }
    )

    entry = SimpleNamespace(
        title="测试标题",
        summary="测试摘要",
        link="https://example.com/post",
        author="测试作者",
        published="2026-03-28T10:00:00Z",
    )

    article = parser._parse_entry(entry)

    assert article is not None
    assert article["source_type"] == "wechat"
    assert article["source_name"] == "微信公众号测试源"


def test_fetch_without_url_returns_empty_list():
    from app.processors.rss_parser import RSSParser

    parser = RSSParser({"type": "wechat", "name": "空链接源", "url": ""})

    assert parser.fetch() == []
```

- [ ] **Step 2: Run the first parser test to verify it fails**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/backend && pytest tests/processors/test_rss_parser.py::test_parse_entry_preserves_wechat_source_type -v
```

Expected: FAIL because `_parse_entry()` currently returns `"source_type": "rss"` unconditionally.

- [ ] **Step 3: Implement the minimal parser change**

Update `backend/app/processors/rss_parser.py` to store the configured type once and reuse it when building article payloads:

```python
class RSSParser:
    """RSS/Atom解析器"""

    def __init__(self, source_config: Dict):
        self.config = source_config
        self.url = source_config.get("url")
        self.source_name = source_config.get("name", "RSS")
        source_type = source_config.get("type", "rss")
        self.source_type = source_type.value if hasattr(source_type, "value") else source_type

    def _parse_entry(self, entry) -> Optional[Dict]:
        try:
            published_at = None
            if hasattr(entry, "published"):
                published_at = self._parse_date(entry.published)
            elif hasattr(entry, "updated"):
                published_at = self._parse_date(entry.updated)

            content = ""
            if hasattr(entry, "content"):
                content = entry.content[0].value if entry.content else ""
            elif hasattr(entry, "summary"):
                content = entry.summary

            link = ""
            if hasattr(entry, "link"):
                link = entry.link
            elif hasattr(entry, "links") and entry.links:
                link = entry.links[0].href

            author = ""
            if hasattr(entry, "author"):
                author = entry.author

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

        except Exception as e:
            logger.warning(f"解析条目失败: {e}")
            return None
```

- [ ] **Step 4: Run the focused parser tests**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/backend && pytest tests/processors/test_rss_parser.py::test_parse_entry_preserves_wechat_source_type tests/processors/test_rss_parser.py::test_fetch_without_url_returns_empty_list -v
```

Expected: PASS.

- [ ] **Step 5: Run the full RSS parser test file**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/backend && pytest tests/processors/test_rss_parser.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit the parser slice**

```bash
git -C /Users/jarod/Dev/LeadMine add backend/app/processors/rss_parser.py backend/tests/processors/test_rss_parser.py && git -C /Users/jarod/Dev/LeadMine commit -m "$(cat <<'EOF'
fix: preserve wechat source type in rss parsing
EOF
)"
```

---

### Task 3: Prove the normal source crawl workflow works for `wechat`

**Files:**
- Modify: `backend/tests/api/test_resources.py`
- Inspect: `backend/app/api/resources.py`
- Inspect: `backend/app/services/scheduler.py`
- Inspect: `backend/app/services/article_service.py`

- [ ] **Step 1: Add a failing API smoke test for manual crawl**

Append this test to `backend/tests/api/test_resources.py`:

```python
from unittest.mock import patch


def test_trigger_crawl_wechat_source(client, admin_token, db_session, test_source):
    from app.models import SourceTypeEnum

    test_source.type = SourceTypeEnum.wechat
    test_source.url = "https://rsshub.app/wechat/mp/example"
    db_session.commit()

    mocked_result = {
        "source_id": test_source.id,
        "source_name": test_source.name,
        "status": "success",
        "message": "抓取完成",
        "fetched_count": 1,
        "saved_count": 1,
        "process_result": {
            "total": 1,
            "success": 1,
            "failed": 0,
            "duplicates": 0,
            "leads_extracted": 0,
        },
    }

    with patch("app.api.resources.scheduler.trigger_manual_crawl", return_value=mocked_result) as mock_trigger:
        response = client.post(
            f"/api/v1/sources/{test_source.id}/crawl",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    assert response.status_code == 200
    assert response.json()["result"]["status"] == "success"
    mock_trigger.assert_called_once_with(test_source.id)
```

- [ ] **Step 2: Run the API smoke test**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/backend && pytest tests/api/test_resources.py::test_trigger_crawl_wechat_source -v
```

Expected: PASS or FAIL only if the current resources test scaffolding differs. If it fails because fixture names differ, adapt the test to the existing fixture names in `tests/api/test_resources.py` without changing the intended assertion: a `wechat` source must travel through the existing manual crawl endpoint successfully.

- [ ] **Step 3: If the test failed due to fixture mismatch, align it to existing fixtures only**

Use the existing fixture style already present in `backend/tests/api/test_resources.py`. Do not change application code in this step unless a real behavior failure appears. The target behavior to preserve is:

```python
assert response.status_code == 200
assert response.json()["result"]["status"] == "success"
mock_trigger.assert_called_once_with(test_source.id)
```

- [ ] **Step 4: Run the full resources API test file**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/backend && pytest tests/api/test_resources.py -v
```

Expected: PASS, proving the standard source crawl endpoint still works with the new `wechat` alias.

- [ ] **Step 5: Run the full targeted regression set**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/backend && pytest tests/scrapers/test_spider_factory.py tests/processors/test_rss_parser.py tests/api/test_resources.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit the workflow verification slice**

```bash
git -C /Users/jarod/Dev/LeadMine add backend/tests/api/test_resources.py && git -C /Users/jarod/Dev/LeadMine commit -m "$(cat <<'EOF'
test: cover wechat source crawl workflow
EOF
)"
```

---

### Task 4: Final manual verification and handoff

**Files:**
- Inspect: `backend/app/api/resources.py`
- Inspect: `backend/app/services/scheduler.py`
- Inspect: `backend/app/services/article_service.py`
- Inspect: `web/src/views/Sources.vue`

- [ ] **Step 1: Start the backend locally**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected: FastAPI starts successfully and exposes `http://localhost:8000/docs`.

- [ ] **Step 2: Create a WeChat source through the normal UI or API**

Use this payload if testing via API:

```bash
curl -X POST "http://localhost:8000/api/v1/sources" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "微信公众号测试源",
    "type": "wechat",
    "url": "https://rsshub.app/wechat/mp/example",
    "crawl_interval": 30,
    "enabled": true
  }'
```

Expected: `201 Created` with returned source JSON containing `"type": "wechat"`.

- [ ] **Step 3: Trigger the crawl through the existing source endpoint**

Run:

```bash
curl -X POST "http://localhost:8000/api/v1/sources/<SOURCE_ID>/crawl" \
  -H "Authorization: Bearer <TOKEN>"
```

Expected: `200 OK` with a JSON result containing a non-error crawl status. The response must not hit the unsupported-type path.

- [ ] **Step 4: Verify stored articles keep WeChat classification**

Check through the application database or an authenticated articles endpoint. The key invariant is that stored `Article.source_type` for newly ingested rows is `wechat`, not `rss`.

SQL check:

```sql
SELECT title, source_name, source_type, source_url
FROM articles
WHERE source_name = '微信公众号测试源'
ORDER BY id DESC
LIMIT 5;
```

Expected: `source_type` column shows `wechat`.

- [ ] **Step 5: Run the final targeted suite one last time**

Run:

```bash
cd /Users/jarod/Dev/LeadMine/backend && pytest tests/scrapers/test_spider_factory.py tests/processors/test_rss_parser.py tests/api/test_resources.py -v
```

Expected: PASS.

- [ ] **Step 6: Create the final implementation commit**

```bash
git -C /Users/jarod/Dev/LeadMine add backend/scrapers/spider_factory.py backend/app/processors/rss_parser.py backend/tests/scrapers/test_spider_factory.py backend/tests/processors/test_rss_parser.py backend/tests/api/test_resources.py && git -C /Users/jarod/Dev/LeadMine commit -m "$(cat <<'EOF'
feat: support rsshub-backed wechat source ingestion
EOF
)"
```

---

## Self-review

### Spec coverage
- Preserve `wechat` as a first-class type: covered by Tasks 1, 2, and 4.
- Reuse `RSSParser` rather than adding a new crawler: covered by Task 1.
- Preserve `source_type = wechat` in parsed output: covered by Task 2.
- Keep the existing source crawl workflow and error surface: covered by Task 3 and Task 4.
- Manual validation through the existing source endpoint: covered by Task 4.

### Placeholder scan
- No `TODO`/`TBD` placeholders.
- Each code-changing step includes concrete code blocks.
- Each verification step includes exact commands and expected outcomes.

### Type consistency
- The plan consistently uses `wechat` as the configured `DataSource.type`.
- The parser change consistently emits `self.source_type`.
- All tests assert the same behavior: `wechat` routes through RSS parsing and remains classified as `wechat`.
