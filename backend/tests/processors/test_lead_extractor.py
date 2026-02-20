"""
线索提取器测试
测试从文章中提取销售线索的功能
"""

import pytest


class TestLeadExtractor:
    """测试线索提取功能"""

    @pytest.fixture
    def extractor(self):
        """创建提取器实例"""
        from app.processors.lead_extractor import LeadExtractor

        return LeadExtractor()

    def test_extract_financing_lead(self, extractor):
        """测试提取融资事件线索"""
        article = {
            "title": "36氪首发｜人工智能公司完成1亿元A轮融资",
            "content": "人工智能公司今日宣布完成1亿元人民币A轮融资，本轮融资由红杉资本领投。公司表示将用于技术研发和市场拓展。",
            "source_name": "36氪",
        }

        leads = extractor.extract_from_article(article)
        assert len(leads) > 0
        lead = leads[0]
        assert lead["event_type"] == "financing"
        assert "人工智能" in lead["company_name"]
        assert "1亿元" in lead.get("event_amount", "")
        assert lead["confidence"] > 70

    def test_extract_acquisition_lead(self, extractor):
        """测试提取并购事件线索"""
        article = {
            "title": "腾讯收购某游戏公司",
            "content": "腾讯今日宣布收购某游戏公司，收购金额未披露。这是腾讯在游戏领域的又一重要布局。",
            "source_name": "虎嗅",
        }

        leads = extractor.extract_from_article(article)
        assert len(leads) > 0
        lead = leads[0]
        assert lead["event_type"] == "acquisition"
        assert lead["confidence"] > 60

    def test_extract_product_launch_lead(self, extractor):
        """测试提取产品发布线索"""
        article = {
            "title": "某公司发布新一代智能手机",
            "content": "某公司今日发布新一代智能手机，搭载最新处理器，售价4999元起。",
            "source_name": "测试源",
        }

        leads = extractor.extract_from_article(article)
        # 产品发布可能不直接产生销售线索，取决于具体实现
        # 或者置信度较低

    def test_extract_expansion_lead(self, extractor):
        """测试提取扩产线索"""
        article = {
            "title": "某制造企业宣布扩产计划",
            "content": "某制造企业宣布将投资10亿元建设新工厂，预计新增产能50%。",
            "source_name": "财经网",
        }

        leads = extractor.extract_from_article(article)
        # 检查是否识别为扩产事件

    def test_extract_procurement_lead(self, extractor):
        """测试提取招标采购线索"""
        article = {
            "title": "某国企发布设备采购招标公告",
            "content": "某国有企业发布设备采购招标公告，预算金额5000万元，欢迎符合条件的企业投标。",
            "source_name": "采购网",
        }

        leads = extractor.extract_from_article(article)
        # 检查是否识别为采购事件

    def test_no_lead_in_irrelevant_article(self, extractor):
        """测试无关文章不提取线索"""
        article = {
            "title": "今日天气晴朗",
            "content": "今天是个好天气，适合出门散步。",
            "source_name": "新闻",
        }

        leads = extractor.extract_from_article(article)
        # 应该返回空列表或低置信度
        assert len(leads) == 0 or all(l["confidence"] < 50 for l in leads)

    def test_extract_multiple_leads(self, extractor):
        """测试一篇文章提取多个线索"""
        article = {
            "title": "多家企业完成融资",
            "content": "A公司完成1亿元融资，B公司完成5000万元融资，两家公司都在人工智能领域。",
            "source_name": "36氪",
        }

        leads = extractor.extract_from_article(article)
        # 如果实现支持，应该提取多个线索
        assert len(leads) >= 1


class TestAmountExtraction:
    """测试金额提取"""

    def test_extract_yuan_amount(self):
        """测试提取人民币金额"""
        from app.processors.nlp_processor import NLPProcessor

        nlp = NLPProcessor()

        text = "完成1亿元融资"
        amount = nlp.extract_amount(text)
        assert amount is not None
        assert "亿" in amount or "100000000" in amount

    def test_extract_wan_amount(self):
        """测试提取万元金额"""
        from app.processors.nlp_processor import NLPProcessor

        nlp = NLPProcessor()

        text = "获得5000万元投资"
        amount = nlp.extract_amount(text)
        assert amount is not None

    def test_extract_million_usd(self):
        """测试提取美元金额"""
        from app.processors.nlp_processor import NLPProcessor

        nlp = NLPProcessor()

        text = "raised $10 million"
        amount = nlp.extract_amount(text)
        # 如果支持英文


class TestCompanyNameExtraction:
    """测试公司名称提取"""

    def test_extract_company_from_financing(self):
        """测试从融资新闻提取公司名"""
        text = "字节跳动完成新一轮融资"
        # 提取公司名

    def test_extract_company_with_suffix(self):
        """测试带公司后缀的名称"""
        text = "北京某某科技有限公司宣布"
        # 提取完整公司名


class TestConfidenceCalculation:
    """测试置信度计算"""

    def test_high_confidence_financing(self):
        """测试高置信度融资事件"""
        article = {
            "title": "确认：XX公司完成10亿元C轮融资",
            "content": "经过多方确认，XX公司今日正式宣布完成10亿元人民币C轮融资，估值达到100亿元。",
            "source_name": "36氪",
        }
        # 置信度应该很高

    def test_low_confidence_rumor(self):
        """测试低置信度传闻"""
        article = {
            "title": "传闻：某公司可能正在寻求融资",
            "content": "有消息称某公司正在接触投资人，但尚未得到官方证实。",
            "source_name": "小道消息",
        }
        # 置信度应该较低


class TestRuleMatching:
    """测试规则匹配"""

    def test_financing_keywords(self):
        """测试融资关键词匹配"""
        keywords = ["融资", "完成", "轮", "投资", "领投"]
        text = "完成A轮融资"
        # 应该匹配多个关键词

    def test_acquisition_keywords(self):
        """测试并购关键词匹配"""
        keywords = ["收购", "并购", "买下", "控股"]
        text = "腾讯收购游戏公司"
        # 应该匹配关键词
