"""
线索识别规则引擎（优化版）
"""

import re
from typing import List, Dict, Optional
import logging

from app.processors.nlp_processor import nlp_processor, KNOWN_COMPANIES
from app.models import LeadEventTypeEnum

logger = logging.getLogger(__name__)


# 高质量来源（权重加成）
HIGH_QUALITY_SOURCES = {
    "36氪",
    "虎嗅",
    "钛媒体",
    "创业邦",
    "亿欧",
    "投资界",
    "36kr",
    "财新",
    "财经",
    "经济观察报",
    "21世纪经济报道",
    "第一财经",
}

# 默认线索识别规则
DEFAULT_RULES = {
    LeadEventTypeEnum.financing: {
        "name": "融资事件",
        "patterns": [
            r"完成([A-Za-z]+轮)[融资]?\s*(\d+(?:\.\d+)?(?:亿|万))?(?:人民币|美元)?",
            r"获得(\d+(?:\.\d+)?(?:亿|万))(?:人民币|美元)?[投资融资]",
            r"宣布完成(\d+(?:\.\d+)?(?:亿|万))?(?:人民币|美元)?融资",
            r"(\d+(?:\.\d+)?(?:亿|万))(?:元)?融资",
            r"融资(\d+(?:\.\d+)?(?:亿|万))",
            r"(天使轮|Pre-A|A轮|B轮|C轮|D轮|E轮|F轮|战略融资|种子轮)",
        ],
        "keywords": [
            "融资",
            "获得投资",
            "完成融资",
            "宣布融资",
            "募资",
            "领投",
            "跟投",
        ],
        "min_confidence": 50,
    },
    LeadEventTypeEnum.acquisition: {
        "name": "并购收购",
        "patterns": [
            r"收购([^\s，。]{2,15})(?:公司|股份|资产)?",
            r"并购([^\s，。]{2,15})(?:公司|企业)?",
            r"([^\s，。]{2,15})(?:被|已完成)收购",
            r"战略投资([^\s，。]{2,15})(?:公司|企业)?",
            r"完成对([^\s，。]{2,15})的收购",
            r"全资收购([^\s，。]{2,15})",
        ],
        "keywords": ["收购", "并购", "被收购", "战略投资", "整合", "全资"],
        "min_confidence": 55,
    },
    LeadEventTypeEnum.product: {
        "name": "产品发布",
        "patterns": [
            r"发布([^\s，。]{2,20}(?:产品|服务|平台|系统|应用|软件|APP|解决方案))",
            r"推出([^\s，。]{2,20}(?:产品|服务|平台|系统|功能))",
            r"上线([^\s，。]{2,20}(?:产品|服务|平台|功能))",
            r"发布新一代([^\s，。]{2,20})",
            r"发布全新([^\s，。]{2,20})",
            r"正式发布([^\s，。]{2,20})",
        ],
        "keywords": ["发布", "推出", "上线", "新品", "首发", "发布新品", "正式发布"],
        "min_confidence": 45,
    },
    LeadEventTypeEnum.expansion: {
        "name": "扩产扩张",
        "patterns": [
            r"投资(\d+(?:\.\d+)?(?:亿|万))",
            r"新建([^\s，。]{2,15})(?:工厂|产业园|基地|生产线)",
            r"扩建([^\s，。]{2,15})(?:工厂|产能|基地)?",
            r"落地([^\s，。]{2,15})(?:项目|产业园|基地)",
            r"开工([^\s，。]{2,15})(?:项目|工厂)",
        ],
        "keywords": ["投资", "新建", "扩建", "扩产", "落地", "产业园", "基地", "开工"],
        "min_confidence": 50,
    },
    LeadEventTypeEnum.procurement: {
        "name": "招标采购",
        "patterns": [
            r"招标([^\s，。]{2,15})(?:供应商|服务商|合作伙伴)?",
            r"采购([^\s，。]{2,15})(?:设备|服务|材料)?",
            r"寻求([^\s，。]{2,15})合作伙伴",
            r"招募([^\s，。]{2,15})供应商",
            r"(?:供应商|服务商)招募",
        ],
        "keywords": ["招标", "采购", "寻求合作", "招募供应商", "合作伙伴", "中标"],
        "min_confidence": 55,
    },
    LeadEventTypeEnum.executive: {
        "name": "高管动态",
        "patterns": [
            r"([^\s，。]{2,8})加盟([^\s，。]{2,15})(?:公司|企业)?",
            r"([^\s，。]{2,8})出任([^\s，。]{2,15})(?:CEO|总裁|副总裁|董事长|CTO|CFO)",
            r"挖角([^\s，。]{2,8})(?:来自|于)",
            r"([^\s，。]{2,8})(?:宣布)?离职",
            r"([^\s，。]{2,8})(?:正式)?创业",
            r"(?:前|原)([^\s，。]{2,8})(?:高管|负责人)加入",
        ],
        "keywords": ["加盟", "出任", "挖角", "离职", "创业", "加入", "履新", "卸任"],
        "min_confidence": 50,
    },
    LeadEventTypeEnum.policy: {
        "name": "政策利好",
        "patterns": [
            r"获得([^\s，。]{2,15})补贴",
            r"通过([^\s，。]{2,15})认定",
            r"获批([^\s，。]{2,15})(?:项目|资质)",
            r"获得([^\s，。]{2,15})扶持",
            r"([^\s，。]{2,15})专项资金",
            r"入选([^\s，。]{2,15})(?:名单|名录|计划)",
        ],
        "keywords": [
            "补贴",
            "认定",
            "获批",
            "扶持",
            "政策",
            "专项资金",
            "入选",
            "试点",
        ],
        "min_confidence": 50,
    },
}


class LeadExtractor:
    """线索提取器（优化版）"""

    def __init__(self, rules: Dict = None):
        self.rules = rules or DEFAULT_RULES
        self._compile_patterns()

    def _compile_patterns(self):
        """预编译正则表达式"""
        self.compiled_rules = {}

        for event_type, rule_config in self.rules.items():
            patterns = []
            for pattern in rule_config.get("patterns", []):
                try:
                    compiled = re.compile(pattern, re.IGNORECASE)
                    patterns.append(compiled)
                except re.error as e:
                    logger.warning(f"正则表达式编译失败: {pattern}, {e}")

            self.compiled_rules[event_type] = {
                "name": rule_config.get("name", event_type.value),
                "patterns": patterns,
                "keywords": rule_config.get("keywords", []),
                "min_confidence": rule_config.get("min_confidence", 40),
            }

    def extract(self, article: Dict) -> List[Dict]:
        """从文章中提取线索"""
        leads = []

        title = article.get("title", "")
        content = article.get("content", "")
        text = f"{title} {content}"

        if not text or len(text) < 10:
            return leads

        # 遍历各类型规则进行匹配
        for event_type, rule_config in self.compiled_rules.items():
            matches = self._match_rules(text, rule_config["patterns"])

            for match in matches:
                lead = self._create_lead(article, event_type, match, title)
                if lead:
                    leads.append(lead)

        # 如果没有匹配到规则，使用关键词匹配
        if not leads:
            leads = self._keyword_match(text, article, title)

        # 去重：同一企业同一类型只保留置信度最高的
        leads = self._deduplicate_leads(leads)

        return leads

    def _match_rules(self, text: str, patterns: List) -> List[re.Match]:
        """正则匹配"""
        matches = []
        for pattern in patterns:
            try:
                found = pattern.finditer(text)
                matches.extend(found)
            except Exception as e:
                logger.debug(f"匹配失败: {e}")
        return matches

    def _create_lead(
        self,
        article: Dict,
        event_type: LeadEventTypeEnum,
        match: re.Match,
        title: str = "",
    ) -> Optional[Dict]:
        """创建线索对象"""
        try:
            matched_text = match.group(0)

            # 提取企业名称（传入标题优先）
            company_name = self._extract_company(
                text=article.get("content", ""),
                title=title,
                match=match,
            )

            # 提取金额
            amount = nlp_processor.extract_amount(matched_text)

            # 计算置信度
            confidence = self._calculate_confidence(
                match=match,
                event_type=event_type,
                company_name=company_name,
                amount=amount,
                source_name=article.get("source_name", ""),
            )

            # 检查最小置信度
            min_conf = self.compiled_rules[event_type].get("min_confidence", 40)
            if confidence < min_conf:
                return None

            return {
                "company_name": company_name,
                "event_type": event_type,
                "event_detail": matched_text[:500],
                "event_amount": amount,
                "source_article_id": article.get("id"),
                "source_title": title,
                "source_url": article.get("source_url", ""),
                "source_name": article.get("source_name", ""),
                "published_at": article.get("published_at"),
                "confidence": confidence,
            }

        except Exception as e:
            logger.debug(f"创建线索失败: {e}")
            return None

    def _extract_company(self, text: str, title: str, match: re.Match) -> str:
        """从匹配结果中提取企业名称"""
        # 1. 先从标题提取（优先级最高）
        if title:
            companies = nlp_processor.extract_companies(title, title)
            if companies:
                return companies[0]

        # 2. 从匹配上下文提取
        start = max(0, match.start() - 50)
        end = min(len(text), match.end() + 50)
        context = text[start:end]

        companies = nlp_processor.extract_companies(context, title)
        if companies:
            return companies[0]

        # 3. 从全文提取
        companies = nlp_processor.extract_companies(text, title)
        if companies:
            return companies[0]

        return "未知"

    def _calculate_confidence(
        self,
        match: re.Match,
        event_type: LeadEventTypeEnum,
        company_name: str,
        amount: Optional[str],
        source_name: str,
    ) -> int:
        """
        计算置信度（优化版）

        基础分：40
        匹配质量：+0~25
        企业名称：+0~20
        来源质量：+0~15
        """
        base_score = 40
        matched_text = match.group(0)

        # === 匹配质量评分 (0-25) ===
        match_score = 0

        # 匹配长度
        match_len = len(matched_text)
        if match_len > 40:
            match_score += 10
        elif match_len > 25:
            match_score += 7
        elif match_len > 15:
            match_score += 5
        else:
            match_score += 2

        # 包含具体金额
        if amount:
            match_score += 8

        # 包含轮次信息（融资）
        if event_type == LeadEventTypeEnum.financing:
            if re.search(r"[A-F]轮|天使|Pre-|种子|战略", matched_text, re.I):
                match_score += 7

        # === 企业名称评分 (0-20) ===
        company_score = 0

        if company_name and company_name != "未知":
            # 有效企业名
            company_score += 10

            # 知名企业
            if company_name in KNOWN_COMPANIES:
                company_score += 10
            # 完整公司名（带后缀）
            elif re.search(r"(公司|集团|企业)$", company_name):
                company_score += 5

        # === 来源质量评分 (0-15) ===
        source_score = 0

        if source_name in HIGH_QUALITY_SOURCES:
            source_score += 15
        elif source_name:
            source_score += 5

        # 总分计算
        total = base_score + match_score + company_score + source_score

        return min(100, max(0, total))

    def _keyword_match(self, text: str, article: Dict, title: str = "") -> List[Dict]:
        """关键词匹配（备用方案）"""
        leads = []
        text_lower = text.lower()

        for event_type, rule_config in self.rules.items():
            keywords = rule_config.get("keywords", [])
            min_confidence = rule_config.get("min_confidence", 40)

            matched_keywords = []
            for keyword in keywords:
                if keyword in text_lower:
                    matched_keywords.append(keyword)

            if not matched_keywords:
                continue

            # 提取企业名称
            companies = nlp_processor.extract_companies(text, title)

            if not companies:
                # 尝试从标题提取
                if title:
                    companies = nlp_processor.extract_companies(title, title)

            company = companies[0] if companies else "未知"

            # 关键词匹配的置信度计算
            confidence = self._calculate_keyword_confidence(
                matched_keywords=matched_keywords,
                company_name=company,
                source_name=article.get("source_name", ""),
                text=text,
            )

            # 过滤低置信度
            if confidence < min_confidence:
                continue

            leads.append(
                {
                    "company_name": company,
                    "event_type": event_type,
                    "event_detail": f"关键词匹配: {', '.join(matched_keywords[:3])}",
                    "event_amount": nlp_processor.extract_amount(text),
                    "source_article_id": article.get("id"),
                    "source_title": title,
                    "source_url": article.get("source_url", ""),
                    "source_name": article.get("source_name", ""),
                    "published_at": article.get("published_at"),
                    "confidence": confidence,
                }
            )

        return leads

    def _calculate_keyword_confidence(
        self,
        matched_keywords: List[str],
        company_name: str,
        source_name: str,
        text: str,
    ) -> int:
        """计算关键词匹配的置信度"""
        base_score = 30  # 关键词匹配基础分较低

        # 关键词数量加分
        keyword_score = min(15, len(matched_keywords) * 5)

        # 企业名称加分
        company_score = 0
        if company_name and company_name != "未知":
            company_score = 10
            if company_name in KNOWN_COMPANIES:
                company_score = 20

        # 来源加分
        source_score = 15 if source_name in HIGH_QUALITY_SOURCES else 5

        # 金额加分
        amount_score = 10 if nlp_processor.extract_amount(text) else 0

        total = base_score + keyword_score + company_score + source_score + amount_score

        return min(100, max(0, total))

    def _deduplicate_leads(self, leads: List[Dict]) -> List[Dict]:
        """去重：同一企业同一类型只保留置信度最高的"""
        if not leads:
            return leads

        seen = {}  # key: (company_name, event_type), value: lead
        for lead in leads:
            key = (lead["company_name"], lead["event_type"])
            if key not in seen or lead["confidence"] > seen[key]["confidence"]:
                seen[key] = lead

        return list(seen.values())


# 全局提取器实例
lead_extractor = LeadExtractor()


def extract_leads(article: Dict) -> List[Dict]:
    """从文章中提取线索"""
    return lead_extractor.extract(article)
