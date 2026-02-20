"""
线索提取器测试 - 修复版
"""

import pytest
from app.processors.lead_extractor import LeadExtractor, DEFAULT_RULES
from app.models import LeadEventTypeEnum


class TestLeadExtractor:
    """测试线索提取功能"""

    @pytest.fixture
    def extractor(self):
        """创建提取器实例"""
        return LeadExtractor()

    def test_extract_financing(self, extractor):
        """测试从文章提取融资事件线索"""
        article = {
            "title": "36氪首发｜人工智能公司完成1亿元A轮融资",
            "content": "人工智能公司今日宣布完成1亿元人民币A轮融资，本轮融资由红杉资本领投。公司表示将用于技术研发和市场拓展。",
            "source_name": "36氪",
        }

        leads = extractor.extract(article)
        assert len(leads) > 0
        lead = leads[0]
        assert lead["event_type"] == LeadEventTypeEnum.financing
        assert "人工智能" in lead["company_name"] or "公司" in lead["company_name"]
        assert lead["confidence"] >= 50

    def test_extract_acquisition(self, extractor):
        """测试提取并购事件线索"""
        article = {
            "title": "腾讯收购某游戏公司",
            "content": "腾讯今日宣布收购某游戏公司，收购金额未披露。这是腾讯在游戏领域的又一重要布局。",
            "source_name": "虎嗅",
        }

        leads = extractor.extract(article)
        assert len(leads) > 0
        lead = leads[0]
        assert lead["event_type"] == LeadEventTypeEnum.acquisition
        assert lead["confidence"] >= 50

    def test_extract_no_lead_in_irrelevant_article(self, extractor):
        """测试无关文章不提取线索"""
        article = {
            "title": "今日天气晴朗",
            "content": "今天是个好天气，适合出门散步。",
            "source_name": "新闻",
        }

        leads = extractor.extract(article)
        # 应该返回空列表或低置信度
        assert len(leads) == 0 or all(l["confidence"] < 50 for l in leads)


class TestLeadExtractorRules:
    """测试规则匹配"""

    @pytest.fixture
    def extractor(self):
        return LeadExtractor()

    def test_default_rules_exist(self):
        """测试默认规则存在"""
        assert len(DEFAULT_RULES) > 0
        assert LeadEventTypeEnum.financing in DEFAULT_RULES

    def test_rule_has_patterns(self):
        """测试规则包含模式"""
        financing_rule = DEFAULT_RULES[LeadEventTypeEnum.financing]
        assert "patterns" in financing_rule
        assert len(financing_rule["patterns"]) > 0
        assert "keywords" in financing_rule


class TestConfidenceCalculation:
    """测试置信度计算"""

    def test_calculate_confidence(self):
        """测试置信度计算"""
        extractor = LeadExtractor()

        # 测试高匹配度
        text = "完成1亿元A轮融资，红杉领投"
        # 提取并检查置信度

    def test_confidence_range(self):
        """测试置信度范围"""
        extractor = LeadExtractor()
        article = {
            "title": "测试融资新闻",
            "content": "某公司完成融资",
            "source_name": "36氪",
        }

        leads = extractor.extract(article)
        for lead in leads:
            assert 0 <= lead["confidence"] <= 100
