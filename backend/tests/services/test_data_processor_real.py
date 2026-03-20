"""
DataProcessor Service 测试
"""

from unittest.mock import Mock

from app.services.processor import DataProcessor


def test_process_article_returns_error_when_not_found(monkeypatch):
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    monkeypatch.setattr("app.services.processor.SessionLocal", lambda: mock_db)

    result = DataProcessor().process_article(999999)

    assert result == {"error": "文章不存在"}


def test_process_article_returns_message_when_already_processed(monkeypatch):
    mock_db = Mock()
    article = Mock()
    article.status = "processed"
    mock_db.query.return_value.filter.return_value.first.return_value = article
    monkeypatch.setattr("app.services.processor.SessionLocal", lambda: mock_db)

    result = DataProcessor().process_article(1)

    assert result == {"message": "文章已处理"}


def test_process_pending_articles_aggregates_results(monkeypatch):
    mock_db = Mock()
    article1 = Mock(id=1)
    article2 = Mock(id=2)
    article3 = Mock(id=3)

    mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = [
        article1,
        article2,
        article3,
    ]
    monkeypatch.setattr("app.services.processor.SessionLocal", lambda: mock_db)

    processor = DataProcessor()
    process_article_mock = Mock(
        side_effect=[
            {"is_duplicate": True, "leads_count": 0},
            {"error": "处理失败"},
            {"is_duplicate": False, "leads_count": 2},
        ]
    )
    monkeypatch.setattr(processor, "process_article", process_article_mock)

    result = processor.process_pending_articles(limit=3)

    assert result["total"] == 3
    assert result["success"] == 2
    assert result["failed"] == 1
    assert result["duplicates"] == 1
    assert result["leads_extracted"] == 2


def test_enrich_lead_not_found(monkeypatch):
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    monkeypatch.setattr("app.services.processor.SessionLocal", lambda: mock_db)

    result = DataProcessor().enrich_lead(999999)

    assert result == {"error": "线索不存在"}


def test_enrich_lead_success_updates_score(monkeypatch):
    mock_db = Mock()
    lead = Mock()
    lead.company_name = "测试公司"
    lead.enrichment_data = None
    mock_db.query.return_value.filter.return_value.first.return_value = lead

    company_info = {"score": 88, "grade": "A", "follow_up_hint": "建议本周联系"}

    monkeypatch.setattr("app.services.processor.SessionLocal", lambda: mock_db)
    mock_enrich = Mock(return_value=company_info)
    monkeypatch.setattr("app.services.processor.enricher.enrich", mock_enrich)

    result = DataProcessor().enrich_lead(1)

    assert result["lead_id"] == 1
    assert result["enriched"] is True
    assert result["data"] == company_info
    assert lead.enrichment_data == company_info
    mock_db.commit.assert_called_once()
