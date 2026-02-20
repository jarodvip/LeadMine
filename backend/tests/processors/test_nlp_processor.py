"""
NLP 处理器测试
测试分词、关键词提取、实体识别等功能
"""

import pytest


class TestNLPProcessor:
    """测试 NLP 处理器"""

    @pytest.fixture
    def nlp(self):
        """创建 NLP 处理器实例"""
        from app.processors.nlp_processor import NLPProcessor

        return NLPProcessor()

    def test_tokenize_chinese(self, nlp):
        """测试中文分词"""
        text = "人工智能公司完成融资"
        tokens = nlp.tokenize(text)

        assert len(tokens) > 0
        assert isinstance(tokens, list)
        assert "人工智能" in tokens or "公司" in tokens

    def test_extract_keywords(self, nlp):
        """测试关键词提取"""
        text = "人工智能公司完成1亿元A轮融资，本轮融资由红杉资本领投"
        keywords = nlp.extract_keywords(text, top_k=5)

        assert len(keywords) <= 5
        assert isinstance(keywords, list)
        # 应该包含重要词汇
        keyword_list = [k[0] for k in keywords]
        assert any(word in keyword_list for word in ["融资", "人工智能", "亿元"])

    def test_extract_keywords_empty(self, nlp):
        """测试空文本关键词提取"""
        keywords = nlp.extract_keywords("", top_k=5)
        assert keywords == [] or len(keywords) == 0

    def test_extract_company_names(self, nlp):
        """测试提取公司名称"""
        text = "腾讯收购某游戏公司，字节跳动也在考虑类似收购"
        companies = nlp.extract_companies(text)

        # 如果支持，应该提取到腾讯和字节跳动
        assert isinstance(companies, list)

    def test_extract_person_names(self, nlp):
        """测试提取人名"""
        text = "马云创立的阿里巴巴"
        persons = nlp.extract_persons(text)

        # 如果支持，应该提取到马云
        assert isinstance(persons, list)


class TestAmountExtraction:
    """测试金额提取"""

    @pytest.fixture
    def nlp(self):
        from app.processors.nlp_processor import NLPProcessor

        return NLPProcessor()

    def test_extract_yi_amount(self, nlp):
        """测试提取亿元"""
        text = "完成1亿元融资"
        amount = nlp.extract_amount(text)
        assert amount is not None
        assert "亿" in amount or "1" in amount

    def test_extract_wan_amount(self, nlp):
        """测试提取万元"""
        text = "获得5000万元投资"
        amount = nlp.extract_amount(text)
        assert amount is not None

    def test_extract_usd_amount(self, nlp):
        """测试提取美元"""
        text = "raised $10 million"
        amount = nlp.extract_amount(text)
        # 如果支持英文

    def test_extract_no_amount(self, nlp):
        """测试无金额的情况"""
        text = "今天天气很好"
        amount = nlp.extract_amount(text)
        assert amount is None or amount == ""

    def test_extract_large_amount(self, nlp):
        """测试大额数字"""
        text = "获得100亿元融资"
        amount = nlp.extract_amount(text)
        assert amount is not None


class TestTextCleaning:
    """测试文本清洗"""

    @pytest.fixture
    def cleaner(self):
        from app.processors.cleaner import TextCleaner

        return TextCleaner()

    def test_remove_html_tags(self, cleaner):
        """测试移除 HTML 标签"""
        text = "<p>这是一段文本</p><div>另一段</div>"
        cleaned = cleaner.clean(text)
        assert "<p>" not in cleaned
        assert "<div>" not in cleaned
        assert "这是一段文本" in cleaned

    def test_normalize_whitespace(self, cleaner):
        """测试规范化空白"""
        text = "这是   一段    有很多空格的   文本"
        cleaned = cleaner.clean(text)
        assert "   " not in cleaned

    def test_remove_special_chars(self, cleaner):
        """测试移除特殊字符"""
        text = "这是一些特殊字符：\n\t\r"
        cleaned = cleaner.clean(text)
        assert "\n" not in cleaned
        assert "\t" not in cleaned

    def test_clean_empty_text(self, cleaner):
        """测试空文本清洗"""
        cleaned = cleaner.clean("")
        assert cleaned == ""
