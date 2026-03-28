"""
Resources API 测试
"""

from datetime import datetime, timedelta

from app.models.models import Article, DataSource, SourceTypeEnum


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
