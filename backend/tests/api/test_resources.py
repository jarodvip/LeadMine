"""
Resources API 测试
"""

from datetime import datetime, timedelta
import importlib

from sqlalchemy.orm import sessionmaker

from app.models.models import Article, DataSource, SourceTypeEnum

scheduler_module = importlib.import_module("app.services.scheduler")
article_service_module = importlib.import_module("app.services.article_service")
processor_module = importlib.import_module("app.services.processor")


def test_get_articles_filters_and_pagination(client, auth_headers, db):
    now = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)

    db.add_all(
        [
            Article(
                title="Alpha SaaS 融资快讯",
                content="A",
                source_name="36氪",
                source_url="https://example.com/a1",
                source_type=SourceTypeEnum.news,
                category="tech",
                crawled_at=now - timedelta(minutes=10),
            ),
            Article(
                title="Alpha SaaS 融资进展",
                content="B",
                source_name="36氪",
                source_url="https://example.com/a2",
                source_type=SourceTypeEnum.news,
                category="tech",
                crawled_at=now,
            ),
            Article(
                title="Beta 电商融资消息",
                content="C",
                source_name="虎嗅",
                source_url="https://example.com/b1",
                source_type=SourceTypeEnum.news,
                category="retail",
                crawled_at=now - timedelta(minutes=5),
            ),
        ]
    )
    db.commit()

    response = client.get(
        "/api/v1/articles?source_name=36氪&category=tech&keyword=融资&page=1&page_size=1",
        headers=auth_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert payload["page"] == 1
    assert payload["page_size"] == 1
    assert len(payload["data"]) == 1
    assert payload["data"][0]["title"] == "Alpha SaaS 融资进展"


def test_get_sources_with_enabled_filter_and_stats(client, auth_headers, db):
    now = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)

    enabled_source = DataSource(
        name="启用源",
        type=SourceTypeEnum.rss,
        url="https://example.com/rss-enabled",
        enabled=True,
    )
    disabled_source = DataSource(
        name="停用源",
        type=SourceTypeEnum.rss,
        url="https://example.com/rss-disabled",
        enabled=False,
    )
    db.add_all([enabled_source, disabled_source])
    db.flush()

    db.add(
        Article(
            title="今日文章",
            content="content",
            source_name="启用源",
            source_url="https://example.com/article-today",
            source_type=SourceTypeEnum.rss,
            category="rss",
            crawled_at=now,
        )
    )
    db.commit()

    response = client.get("/api/v1/sources?enabled=true", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "启用源"
    assert "today_count" in data[0]
    assert "success_rate" in data[0]
    assert data[0]["today_count"] == 1
    assert data[0]["success_rate"] == 100


def test_trigger_crawl_returns_404_or_400_when_invalid_source(client, auth_headers, db):
    response_not_found = client.post("/api/v1/sources/999999/crawl", headers=auth_headers)
    assert response_not_found.status_code == 404

    disabled_source = DataSource(
        name="crawl-disabled",
        type=SourceTypeEnum.rss,
        url="https://example.com/crawl-disabled",
        enabled=False,
    )
    db.add(disabled_source)
    db.commit()
    db.refresh(disabled_source)

    response_disabled = client.post(
        f"/api/v1/sources/{disabled_source.id}/crawl", headers=auth_headers
    )
    assert response_disabled.status_code == 400


def test_trigger_crawl_supports_wechat_sources_via_scheduler(client, auth_headers, db, monkeypatch):
    source = DataSource(
        name="微信源",
        type=SourceTypeEnum.wechat,
        url="https://rsshub.example/wechat/mp/channel",
        enabled=True,
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    SessionLocal = sessionmaker(bind=db.bind)
    source_id = source.id
    source_name = source.name

    fetched_articles = [
        {
            "title": "微信公众号文章",
            "content": "内容",
            "summary": "摘要",
            "author": "作者",
            "source_url": "https://example.com/wechat-article",
            "published_at": datetime.now(),
        }
    ]

    monkeypatch.setattr(scheduler_module.DistributedLock, "acquire", lambda self: True)
    monkeypatch.setattr(scheduler_module.DistributedLock, "release", lambda self: None)
    monkeypatch.setattr("app.processors.rss_parser.RSSParser.fetch", lambda self: fetched_articles)
    monkeypatch.setattr(scheduler_module, "SessionLocal", lambda: SessionLocal())
    monkeypatch.setattr(article_service_module, "SessionLocal", lambda: SessionLocal())
    monkeypatch.setattr(
        processor_module.data_processor,
        "process_pending_articles",
        lambda limit=50: {
            "total": 1,
            "success": 1,
            "failed": 0,
            "duplicates": 0,
            "leads_extracted": 0,
        },
    )

    response = client.post(f"/api/v1/sources/{source_id}/crawl", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_id"] == source_id
    assert payload["result"]["status"] == "success"
    assert payload["result"]["source_name"] == source_name
    assert payload["result"]["fetched_count"] == 1
    assert payload["result"]["saved_count"] == 1
    assert payload["result"]["process_result"] == {
        "total": 1,
        "success": 1,
        "failed": 0,
        "duplicates": 0,
        "leads_extracted": 0,
    }


def test_update_source_allows_changing_type(client, auth_headers, db):
    source = DataSource(
        name="类型可编辑源",
        type=SourceTypeEnum.rss,
        url="https://example.com/source",
        enabled=True,
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    response = client.patch(
        f"/api/v1/sources/{source.id}",
        json={"type": "wechat"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "wechat"

    db.refresh(source)
    assert source.type == SourceTypeEnum.wechat
