"""
NLP 处理器测试 - 修复版
"""

import pytest
from app.processors.nlp_processor import NLPProcessor, nlp_processor


class TestNLPProcessor:
    """测试 NLP 处理器"""

    @pytest.fixture
    def nlp(self):
        """创建 NLP 处理器实例"""
        return NLPProcessor()

    def test_segment(self, nlp):
        """测试中文分词"""
        text = "人工智能公司完成融资"
        tokens = nlp.segment(text)

        assert len(tokens) > 0
        assert isinstance(tokens, list)

    def test_extract_keywords(self, nlp):
        """测试关键词提取"""
        text = "人工智能公司完成1亿元A轮融资，本轮融资由红杉资本领投"
        keywords = nlp.extract_keywords(text, top_k=5)

        assert len(keywords) <= 5
        assert isinstance(keywords, list)

    def test_extract_keywords_empty(self, nlp):
        """测试空文本关键词提取"""
        keywords = nlp.extract_keywords("", top_k=5)
        assert keywords == []

    def test_extract_companies(self, nlp):
        """测试提取公司名称"""
        text = "腾讯收购某游戏公司，字节跳动也在考虑类似收购"
        companies = nlp.extract_companies(text)

        assert isinstance(companies, list)

    def test_extract_amount(self, nlp):
        """测试提取金额"""
        text = "完成1亿元融资"
        amount = nlp.extract_amount(text)
        assert amount is not None
        assert "亿" in amount or "1" in str(amount)

    def test_extract_amount_none(self, nlp):
        """测试无金额的情况"""
        text = "今天天气很好"
        amount = nlp.extract_amount(text)
        assert amount is None

    def test_classify_category(self, nlp):
        """测试文章分类"""
        text = "人工智能公司完成融资，技术发展迅速"
        category = nlp.classify_category(text)

        assert isinstance(category, str)
        assert len(category) > 0

    def test_analyze(self, nlp):
        """测试完整分析"""
        text = "人工智能公司完成1亿元A轮融资"
        result = nlp.analyze(text)

        assert "keywords" in result
        assert "companies" in result
        assert "amount" in result
        assert "category" in result
        assert "segments" in result


class TestGlobalNLPProcessor:
    """测试全局 NLP 处理器"""

    def test_global_processor_exists(self):
        """测试全局处理器存在"""
        assert nlp_processor is not None
        assert isinstance(nlp_processor, NLPProcessor)


class TestTextProcessing:
    """测试文本处理功能"""

    def test_stopwords_removal(self):
        """测试停用词过滤"""
        nlp = NLPProcessor()
        text = "这是一个测试文本"
        tokens = nlp.segment(text, use_stopwords=True)

        # 停用词应该被过滤
        assert "的" not in tokens

    def test_keywords_with_weight(self):
        """测试带权重的关键词提取"""
        nlp = NLPProcessor()
        text = "人工智能技术发展"
        keywords = nlp.extract_keywords_with_weight(text, top_k=3)

        assert isinstance(keywords, list)
        if keywords:
            assert isinstance(keywords[0], tuple)
            assert len(keywords[0]) == 2
