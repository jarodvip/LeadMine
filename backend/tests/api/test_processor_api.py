"""
Processor API 测试
"""

from unittest.mock import Mock

from app.api import processor as processor_api


def test_process_single_article_not_found_returns_404(client, auth_headers):
    resp = client.post("/api/v1/processor/articles/999999/process", headers=auth_headers)
    assert resp.status_code == 404


def test_process_pending_articles_limit_validation(client, auth_headers):
    resp_low = client.post("/api/v1/processor/articles/process?limit=0", headers=auth_headers)
    assert resp_low.status_code == 400

    resp_high = client.post(
        "/api/v1/processor/articles/process?limit=201", headers=auth_headers
    )
    assert resp_high.status_code == 400


def test_enrich_lead_not_found_returns_404(client, auth_headers, monkeypatch):
    mock_processor = Mock()
    mock_processor.enrich_lead.return_value = {"error": "线索不存在"}
    monkeypatch.setattr(processor_api, "data_processor", mock_processor)

    resp = client.post("/api/v1/processor/leads/999999/enrich", headers=auth_headers)

    assert resp.status_code == 404
    assert resp.json()["detail"] == "线索不存在"
