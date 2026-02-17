"""
NLP处理服务 - 分词、关键词提取、实体识别
"""

import jieba
import jieba.analyse
import re
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class NLPProcessor:
    """NLP处理器"""

    # 企业名称识别模式
    COMPANY_PATTERNS = [
        r"([^\s]{2,20}(?:公司|集团|企业|有限|股份|科技|实业|发展|投资|控股))",
        r"([^\s]{2,10}(?:有限公司|有限责任公司|股份有限公司|集团有限公司))",
    ]

    # 金额识别模式
    AMOUNT_PATTERNS = [
        r"(\d+(?:\.\d+)?(?:亿|万|千)?(?:元|人民币|美元|欧元|英镑)?)",
        r"(?:融资金额|投资金额|涉及金额|投资额)((?:\d+(?:\.\d+)?(?:亿|万|千)?(?:元|人民币|美元)))",
    ]

    def __init__(self):
        # 初始化jieba
        jieba.setLogLevel(jieba.logging.INFO)

        # 加载自定义词典（可选）
        self._load_custom_dict()

    def _load_custom_dict(self):
        """加载自定义词典"""
        try:
            # 添加一些常见词汇
            custom_words = [
                "36氪",
                "虎嗅",
                "钛媒体",
                "创业邦",
                "亿欧",
                "融资",
                "并购",
                "收购",
                "上市",
                "IPO",
                "A轮",
                "B轮",
                "C轮",
                "D轮",
                "天使轮",
                "Pre-A",
            ]
            for word in custom_words:
                jieba.add_word(word)
        except Exception as e:
            logger.warning(f"加载自定义词典失败: {e}")

    def segment(self, text: str, use_stopwords: bool = True) -> List[str]:
        """
        中文分词
        Args:
            text: 待分词文本
            use_stopwords: 是否去除停用词
        Returns:
            分词列表
        """
        if not text:
            return []

        # 移除英文标点
        text = re.sub(r"[^\w\s\u4e00-\u9fff]", " ", text)

        words = jieba.lcut(text)

        if use_stopwords:
            words = self._remove_stopwords(words)

        return words

    def _remove_stopwords(self, words: List[str]) -> List[str]:
        """去除停用词"""
        stopwords = {
            "的",
            "了",
            "在",
            "是",
            "我",
            "有",
            "和",
            "就",
            "不",
            "人",
            "都",
            "一",
            "一个",
            "上",
            "也",
            "很",
            "到",
            "说",
            "要",
            "去",
            "你",
            "会",
            "着",
            "没有",
            "看",
            "好",
            "自己",
            "这",
            "那",
            "它",
            "他",
            "她",
            "们",
            "我们",
            "他们",
            "但是",
            "而",
            "与",
            "及",
            "等",
            "可以",
            "可能",
            "这个",
            "那个",
            "什么",
            "怎么",
            "如何",
            "为什么",
        }

        return [w for w in words if w.strip() and w not in stopwords and len(w) > 1]

    def extract_keywords(
        self, text: str, top_k: int = 10, method: str = "textrank"
    ) -> List[str]:
        """
        提取关键词
        Args:
            text: 待提取文本
            top_k: 返回数量
            method: 算法选择 'textrank' 或 'tfidf'
        Returns:
            关键词列表
        """
        if not text:
            return []

        if method == "tfidf":
            keywords = jieba.analyse.extract_tags(text, topK=top_k, withWeight=False)
        else:
            keywords = jieba.analyse.textrank(text, topK=top_k, withWeight=False)

        return keywords

    def extract_keywords_with_weight(
        self, text: str, top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        提取关键词及权重
        Args:
            text: 待提取文本
            top_k: 返回数量
        Returns:
            [(关键词, 权重), ...]
        """
        if not text:
            return []

        keywords = jieba.analyse.textrank(text, topK=top_k, withWeight=True)
        return keywords

    def extract_companies(self, text: str) -> List[str]:
        """
        提取企业名称
        Args:
            text: 待提取文本
        Returns:
            企业名称列表
        """
        if not text:
            return []

        companies = set()

        # 使用正则匹配
        for pattern in self.COMPANY_PATTERNS:
            matches = re.finditer(pattern, text)
            for match in matches:
                company = match.group(1).strip()
                if len(company) >= 4:  # 过滤太短的
                    companies.add(company)

        # 尝试使用词性标注识别机构名
        try:
            words = jieba.posseg.cut(text)
            for word, flag in words:
                if flag == "nt":  # 机构名
                    companies.add(word)
        except Exception as e:
            logger.debug(f"词性标注失败: {e}")

        return list(companies)

    def extract_amount(self, text: str) -> Optional[str]:
        """
        提取金额
        Args:
            text: 待提取文本
        Returns:
            金额字符串，如 "5000万人民币"
        """
        if not text:
            return None

        for pattern in self.AMOUNT_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return None

    def classify_category(self, text: str) -> str:
        """
        文章分类
        Args:
            text: 文章文本
        Returns:
            分类名称
        """
        if not text:
            return "其他"

        category_rules = {
            "科技": [
                "互联网",
                "软件",
                "硬件",
                "AI",
                "人工智能",
                "大数据",
                "云计算",
                "芯片",
                "半导体",
                "数字化",
            ],
            "金融": [
                "融资",
                "投资",
                "金融",
                "银行",
                "保险",
                "证券",
                "基金",
                "理财",
                "上市",
                "IPO",
            ],
            "汽车": ["汽车", "电动车", "新能源汽车", "自动驾驶", "智能驾驶", "出行"],
            "医疗": ["医疗", "医药", "生物", "健康", "医院", "药物", "疫苗"],
            "消费": ["电商", "零售", "食品", "餐饮", "美妆", "服饰", "零售"],
            "教育": ["教育", "培训", "学习", "学校", "在线教育", "K12"],
            "地产": ["房地产", "地产", "房产", "建筑", "物业", "万科", "碧桂园"],
            "制造": ["制造", "工厂", "生产", "供应链", "工业", "机器人"],
        }

        keywords = self.extract_keywords(text, top_k=20)
        text_lower = text.lower()

        for category, words in category_rules.items():
            count = sum(1 for w in words if w in text_lower)
            if count >= 2:
                return category

        return "其他"

    def analyze(self, text: str) -> Dict:
        """
        完整分析
        Args:
            text: 待分析文本
        Returns:
            分析结果字典
        """
        return {
            "keywords": self.extract_keywords(text),
            "companies": self.extract_companies(text),
            "amount": self.extract_amount(text),
            "category": self.classify_category(text),
            "segments": self.segment(text),
        }


# 全局NLP处理器
nlp_processor = NLPProcessor()


def segment_text(text: str) -> List[str]:
    """分词"""
    return nlp_processor.segment(text)


def extract_keywords(text: str, top_k: int = 10) -> List[str]:
    """提取关键词"""
    return nlp_processor.extract_keywords(text, top_k)


def extract_companies(text: str) -> List[str]:
    """提取企业名称"""
    return nlp_processor.extract_companies(text)


def analyze_text(text: str) -> Dict:
    """完整分析"""
    return nlp_processor.analyze(text)
