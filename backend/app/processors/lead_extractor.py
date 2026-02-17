"""
线索识别规则引擎
"""

import re
from typing import List, Dict, Optional
from datetime import datetime
import logging

from app.processors.nlp_processor import nlp_processor
from app.models import LeadEventTypeEnum

logger = logging.getLogger(__name__)


# 默认线索识别规则
DEFAULT_RULES = {
    LeadEventTypeEnum.financing: {
        "name": "融资事件",
        "patterns": [
            r"完成[A-Z]轮(\d+(?:\.\d+)?(?:亿|万))?(?:人民币|美元)?融资",
            r"获得(\d+(?:\.\d+)?(?:亿|万))?(?:人民币|美元)?投资",
            r"宣布完成(\d+(?:\.\d+)?(?:亿|万))?(?:人民币|美元)?融资",
            r"(\d+(?:\.\d+)?(?:亿|万))元融资",
            r"融资(\d+(?:\.\d+)?(?:亿|万))",
            r"天使轮|Pre-A|A轮|B轮|C轮|D轮|E轮|战略融资",
        ],
        "keywords": ["融资", "获得投资", "完成融资", "宣布融资", "募资"],
    },
    LeadEventTypeEnum.acquisition: {
        "name": "并购收购",
        "patterns": [
            r"收购(\S+?)(?:公司|股份|资产)",
            r"并购(\S+?)(?:公司|企业)",
            r"(\S+?)(?:被|已完成)收购",
            r"战略投资(\S+?)(?:公司|企业)",
            r"完成对(\S+?)的收购",
        ],
        "keywords": ["收购", "并购", "被收购", "战略投资", "整合"],
    },
    LeadEventTypeEnum.product: {
        "name": "产品发布",
        "patterns": [
            r"发布(?!新产品|新版本|新产品|新服务)(.+)",
            r"推出(.+?)(?:产品|服务|平台|系统)",
            r"上线(.+?)(?:产品|服务|平台|功能)",
            r"发布新一代(.+)",
            r"发布全新(.+)",
        ],
        "keywords": ["发布", "推出", "上线", "新品", "首发", "发布新品"],
    },
    LeadEventTypeEnum.expansion: {
        "name": "扩产扩张",
        "patterns": [
            r"投资(\d+(?:\.\d+)?(?:亿|万))",
            r"新建(.+?)(?:工厂|产业园|基地|生产线)",
            r"扩建(.+?)(?:工厂|产能|基地)",
            r"(?:投资|投入)(\d+(?:\.\d+)?(?:亿|万))",
            r"落地(.+?)(?:项目|产业园|基地)",
        ],
        "keywords": ["投资", "新建", "扩建", "扩产", "落地", "产业园", "基地"],
    },
    LeadEventTypeEnum.procurement: {
        "name": "招标采购",
        "patterns": [
            r"招标(.+?)(?:供应商|服务商|合作伙伴)",
            r"采购(.+?)(?:设备|服务|材料)",
            r"寻求(.+?)合作伙伴",
            r"招募(.+?)供应商",
            r"(?:供应商|服务商)招募",
        ],
        "keywords": ["招标", "采购", "寻求合作", "招募供应商", "合作伙伴"],
    },
    LeadEventTypeEnum.executive: {
        "name": "高管动态",
        "patterns": [
            r"(\S+?)加盟(\S+?)(?:公司|企业)",
            r"(\S+?)出任(\S+?)(?:CEO|总裁|副总裁|董事长)",
            r"挖角(\S+?)(?:来自|于)",
            r"(\S+?)离职",
            r"(\S+?)创业",
            r"(?:前|原)(\S+?)(?:高管|负责人)加入",
        ],
        "keywords": ["加盟", "出任", "挖角", "离职", "创业", "加入"],
    },
    LeadEventTypeEnum.policy: {
        "name": "政策利好",
        "patterns": [
            r"获得(\S+?)补贴",
            r"通过(\S+?)认定",
            r"获批(\S+?)(?:项目|资质)",
            r"获得(\S+?)扶持",
            r"(\S+?)专项资金",
        ],
        "keywords": ["补贴", "认定", "获批", "扶持", "政策", "专项资金"],
    },
}


class LeadExtractor:
    """线索提取器"""

    def __init__(self, rules: Dict = None):
        """
        初始化提取器
        Args:
            rules: 自定义规则，为None时使用默认规则
        """
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
            }

    def extract(self, article: Dict) -> List[Dict]:
        """
        从文章中提取线索
        Args:
            article: 文章数据字典
        Returns:
            线索列表
        """
        leads = []

        # 合并标题和正文进行匹配
        text = f"{article.get('title', '')} {article.get('content', '')}"

        if not text or len(text) < 10:
            return leads

        # 遍历各类型规则进行匹配
        for event_type, rule_config in self.compiled_rules.items():
            matches = self._match_rules(text, rule_config["patterns"])

            for match in matches:
                lead = self._create_lead(article, event_type, match)
                if lead:
                    leads.append(lead)

        # 使用关键词辅助匹配
        if not leads:
            leads = self._keyword_match(text, article)

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
        self, article: Dict, event_type: LeadEventTypeEnum, match: re.Match
    ) -> Dict:
        """创建线索对象"""
        try:
            # 提取企业名称
            company_name = self._extract_company(
                text=article.get("title", "") + " " + article.get("content", ""),
                match=match,
            )

            # 提取金额
            amount = nlp_processor.extract_amount(match.group(0))

            # 计算置信度
            confidence = self._calculate_confidence(match, event_type)

            return {
                "company_name": company_name,
                "event_type": event_type,
                "event_detail": match.group(0)[:500],
                "event_amount": amount,
                "source_article_id": article.get("id"),
                "source_title": article.get("title", ""),
                "source_url": article.get("source_url", ""),
                "source_name": article.get("source_name", ""),
                "published_at": article.get("published_at"),
                "confidence": confidence,
            }

        except Exception as e:
            logger.debug(f"创建线索失败: {e}")
            return None

    def _extract_company(self, text: str, match: re.Match) -> str:
        """从匹配结果中提取企业名称"""
        # 获取匹配位置前后50个字符
        start = max(0, match.start() - 50)
        end = min(len(text), match.end() + 50)
        context = text[start:end]

        # 使用NLP提取
        companies = nlp_processor.extract_companies(context)

        if companies:
            return companies[0]

        # 备用：使用简单模式匹配
        patterns = [
            r"([^\s]{2,15}公司)",
            r"([^\s]{2,10}科技)",
            r"([^\s]{2,10}集团)",
        ]

        for pattern in patterns:
            m = re.search(pattern, context)
            if m:
                return m.group(1)

        return "未知"

    def _calculate_confidence(
        self, match: re.Match, event_type: LeadEventTypeEnum
    ) -> int:
        """计算置信度"""
        base_score = 50

        # 匹配长度越长，置信度越高
        match_len = len(match.group(0))
        if match_len > 30:
            base_score += 15
        elif match_len > 15:
            base_score += 10
        else:
            base_score += 5

        # 包含数字（金额）置信度更高
        if re.search(r"\d+", match.group(0)):
            base_score += 10

        # 包含具体公司名称
        if re.search(r"[^\s]{4,15}(?:公司|集团|科技)", match.group(0)):
            base_score += 10

        return min(100, base_score)

    def _keyword_match(self, text: str, article: Dict) -> List[Dict]:
        """关键词匹配（备用方案）"""
        leads = []

        text_lower = text.lower()

        for event_type, rule_config in self.rules.items():
            keywords = rule_config.get("keywords", [])

            for keyword in keywords:
                if keyword in text_lower:
                    # 提取企业名称
                    companies = nlp_processor.extract_companies(text)

                    for company in companies[:1]:  # 只取第一个
                        leads.append(
                            {
                                "company_name": company,
                                "event_type": event_type,
                                "event_detail": f"关键词匹配: {keyword}",
                                "source_article_id": article.get("id"),
                                "source_title": article.get("title", ""),
                                "source_url": article.get("source_url", ""),
                                "source_name": article.get("source_name", ""),
                                "published_at": article.get("published_at"),
                                "confidence": 40,
                            }
                        )
                    break

        return leads


# 全局提取器实例
lead_extractor = LeadExtractor()


def extract_leads(article: Dict) -> List[Dict]:
    """从文章中提取线索"""
    return lead_extractor.extract(article)
