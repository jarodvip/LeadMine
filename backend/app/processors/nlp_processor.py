"""
NLP处理服务 - 分词、关键词提取、实体识别
"""

import jieba
import jieba.analyse
import re
from typing import List, Dict, Optional, Tuple, Set
import logging

logger = logging.getLogger(__name__)


# 无效企业名称黑名单
INVALID_COMPANY_BLACKLIST = {
    "有限公司",
    "股份有限公司",
    "有限责任公司",
    "集团有限公司",
    "有限公司，",
    "股份有限公司，",
    "有限公司。",
    "股份有限公司。",
    "未知",
    "一些公司",
    "该公司",
    "本公司",
    "贵公司",
    "上市公司",
    "新公司",
    "大公司",
    "小公司",
    "总公司",
    "分公司",
    "母公司",
    "子公司",
    "集团公司",
    "控股公司",
    "投资公司",
    "管理公司",
    "咨询公司",
    "服务公司",
    "科技公司",
    "网络公司",
    "信息公司",
    "技术公司",
    "发展公司",
    "实业公司",
    "产业公司",
    "资产管理公司",
    "持续助力中小企业",
    "为什么你公司",
    "据外媒报道",
    "一位接近监管层人士透露",
    "从2026产业投资",
}

# 知名企业名称（用于优先匹配）
KNOWN_COMPANIES = {
    "阿里巴巴",
    "腾讯",
    "百度",
    "字节跳动",
    "美团",
    "京东",
    "拼多多",
    "小米",
    "华为",
    "滴滴",
    "快手",
    "哔哩哔哩",
    "B站",
    "网易",
    "新浪",
    "搜狐",
    "360",
    "携程",
    "百度",
    "蚂蚁集团",
    "支付宝",
    "微信",
    "抖音",
    "今日头条",
    "小红书",
    "知乎",
    "比亚迪",
    "蔚来",
    "理想汽车",
    "小鹏汽车",
    "吉利",
    "长城汽车",
    "上汽",
    "一汽",
    "中芯国际",
    "台积电",
    "英伟达",
    "特斯拉",
    "苹果",
    "微软",
    "谷歌",
    "亚马逊",
    "软银",
    "红杉资本",
    "高瓴资本",
    "IDG",
    "经纬中国",
    "真格基金",
    "联想",
    "中兴",
    "OPPO",
    "vivo",
    "荣耀",
    "魅族",
    "一加",
    "科大讯飞",
    "商汤科技",
    "旷视科技",
    "依图科技",
    "云从科技",
    "大疆",
    "快手科技",
    "猿辅导",
    "作业帮",
    "跟谁学",
    "好未来",
    "顺丰",
    "京东物流",
    "菜鸟网络",
    "中通",
    "圆通",
    "韵达",
    "申通",
    "平安",
    "中国人寿",
    "太平洋保险",
    "泰康",
    "华泰",
    "中信",
    "招商银行",
    "茅台",
    "五粮液",
    "伊利",
    "蒙牛",
    "农夫山泉",
    "海天味业",
    "恒大",
    "万科",
    "碧桂园",
    "融创",
    "保利",
    "绿地",
    "龙湖",
    "虎牙",
    "斗鱼",
    "映客",
    "花椒",
    "陌陌",
    "探探",
    "得物",
    "唯品会",
    "蘑菇街",
    "聚美优品",
    "寺库",
    "作业帮",
    "猿辅导",
    "VIPKID",
    "好未来",
    "新东方",
    "高途",
    "喜茶",
    "奈雪的茶",
    "蜜雪冰城",
    "茶百道",
    "古茗",
    "瑞幸咖啡",
    "星巴克",
    "麦当劳",
    "肯德基",
    "必胜客",
    "李宁",
    "安踏",
    "特步",
    "361度",
    "鸿星尔克",
    "优衣库",
    "ZARA",
    "H&M",
    "无印良品",
}


class NLPProcessor:
    """NLP处理器"""

    # 企业名称识别模式（按优先级排序）
    COMPANY_PATTERNS = [
        # 完整公司名
        r"([^\s，。！？、；："
        "''（）【】《》]{2,15}(?:有限公司|有限责任公司|股份有限公司|集团有限公司))",
        # 常见后缀
        r"([^\s，。！？、；："
        "''（）【】《》]{2,12}(?:公司|集团|企业|科技|网络|智能|教育|医疗|金融|投资|控股|实业|发展|传媒|文化|咨询|服务|信息|技术|电子|通信|汽车|新能源|生物|制药|健康|食品|餐饮|零售|电商|物流|供应链))",
        # 英文公司
        r"([A-Z][a-zA-Z\s]{2,20}(?:Inc|Corp|Ltd|LLC|Company|Co)\.?)",
        # 简短名称（需要额外验证）
        r"([^\s，。！？、；：" "''（）【】《》]{3,8}(?:科技|网络|智能|教育|医疗))",
    ]

    # 金额识别模式
    AMOUNT_PATTERNS = [
        r"(\d+(?:\.\d+)?\s*(?:亿|万|千)?(?:元|人民币|美元|欧元|英镑|港币))",
        r"(?:融资金额|投资金额|涉及金额|投资额|金额)[:：]?\s*(\d+(?:\.\d+)?\s*(?:亿|万)(?:元|人民币|美元)?)",
    ]

    def __init__(self):
        jieba.setLogLevel(jieba.logging.INFO)
        self._load_custom_dict()

    def _load_custom_dict(self):
        """加载自定义词典"""
        try:
            # 添加知名企业名
            for company in KNOWN_COMPANIES:
                jieba.add_word(company, freq=1000, tag="nt")

            # 添加行业词汇
            custom_words = [
                ("36氪", 100, "nt"),
                ("虎嗅", 100, "nt"),
                ("钛媒体", 100, "nt"),
                ("创业邦", 100, "nt"),
                ("亿欧", 100, "nt"),
                ("融资", 100, "n"),
                ("并购", 100, "n"),
                ("收购", 100, "vn"),
                ("上市", 100, "v"),
                ("IPO", 100, "n"),
                ("A轮", 50, "n"),
                ("B轮", 50, "n"),
                ("C轮", 50, "n"),
                ("D轮", 50, "n"),
                ("天使轮", 50, "n"),
                ("Pre-A", 50, "n"),
                ("战略融资", 50, "n"),
                ("人工智能", 100, "n"),
                ("大数据", 100, "n"),
                ("云计算", 100, "n"),
                ("区块链", 100, "n"),
                ("物联网", 100, "n"),
                ("5G", 100, "n"),
            ]
            for word, freq, tag in custom_words:
                jieba.add_word(word, freq=freq, tag=tag)

            logger.info("自定义词典加载成功")
        except Exception as e:
            logger.warning(f"加载自定义词典失败: {e}")

    def segment(self, text: str, use_stopwords: bool = True) -> List[str]:
        """中文分词"""
        if not text:
            return []
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
            "以下",
            "以上",
            "之后",
            "之前",
            "通过",
            "进行",
            "已经",
            "正在",
            "将要",
            "能够",
            "应该",
            "需要",
            "可能",
            "或者",
            "以及",
            "但是",
            "如果",
            "因为",
            "所以",
            "虽然",
            "但是",
            "然而",
            "不过",
            "只是",
            "还有",
            "以及",
        }
        return [w for w in words if w.strip() and w not in stopwords and len(w) > 1]

    def extract_keywords(
        self, text: str, top_k: int = 10, method: str = "textrank"
    ) -> List[str]:
        """提取关键词"""
        if not text:
            return []
        if method == "tfidf":
            return jieba.analyse.extract_tags(text, topK=top_k, withWeight=False)
        return jieba.analyse.textrank(text, topK=top_k, withWeight=False)

    def extract_keywords_with_weight(
        self, text: str, top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """提取关键词及权重"""
        if not text:
            return []
        return jieba.analyse.textrank(text, topK=top_k, withWeight=True)

    def extract_companies(self, text: str, title: str = "") -> List[str]:
        """
        提取企业名称（优化版）
        优先级：标题 > 知名企业 > 正则匹配 > NER
        """
        if not text:
            return []

        companies: Set[str] = set()

        # 1. 先从标题提取（标题通常包含主体企业）
        if title:
            title_companies = self._extract_companies_from_text(title, prioritize=True)
            companies.update(title_companies)

        # 2. 从正文提取
        body_companies = self._extract_companies_from_text(text, prioritize=False)
        companies.update(body_companies)

        # 3. 过滤无效名称
        filtered = self._filter_companies(companies)

        # 4. 按优先级排序（标题中的优先）
        result = []
        if title:
            title_set = set(self._extract_companies_from_text(title, prioritize=True))
            # 标题中的企业排在前面
            for c in filtered:
                if c in title_set:
                    result.insert(0, c)
                else:
                    result.append(c)
        else:
            result = list(filtered)

        return result[:5]  # 最多返回5个

    def _extract_companies_from_text(
        self, text: str, prioritize: bool = False
    ) -> List[str]:
        """从文本中提取企业名称"""
        companies = set()

        # 1. 匹配知名企业
        for company in KNOWN_COMPANIES:
            if company in text:
                companies.add(company)

        # 2. 正则匹配
        for pattern in self.COMPANY_PATTERNS:
            try:
                matches = re.finditer(pattern, text)
                for match in matches:
                    company = match.group(1).strip()
                    if self._is_valid_company_name(company):
                        companies.add(company)
            except Exception as e:
                logger.debug(f"正则匹配失败: {e}")

        # 3. NER提取（词性标注）
        try:
            words = jieba.posseg.cut(text)
            for word, flag in words:
                if flag in ("nt", "nto", "nts", "nth"):  # 机构名
                    if self._is_valid_company_name(word):
                        companies.add(word)
        except Exception as e:
            logger.debug(f"NER提取失败: {e}")

        return list(companies)

    def _is_valid_company_name(self, name: str) -> bool:
        """验证企业名称是否有效"""
        if not name or len(name) < 2:
            return False

        # 过滤黑名单
        if name in INVALID_COMPANY_BLACKLIST:
            return False

        # 过滤纯数字
        if name.isdigit():
            return False

        # 过滤常见误匹配
        invalid_patterns = [
            r"^从\d",  # 从2026...
            r"^据",  # 据外媒...
            r"^一位",  # 一位接近...
            r"^为什么",  # 为什么...
            r"^持续",  # 持续助力...
        ]
        for pattern in invalid_patterns:
            if re.match(pattern, name):
                return False

        return True

    def _filter_companies(self, companies: Set[str]) -> Set[str]:
        """过滤和去重企业名称"""
        filtered = set()

        for company in companies:
            # 基本验证
            if not self._is_valid_company_name(company):
                continue

            # 去除标点
            company = re.sub(r'[，。！？、；：""' "（）【】《》\s]+", "", company)

            if company and len(company) >= 2:
                filtered.add(company)

        return filtered

    def extract_amount(self, text: str) -> Optional[str]:
        """提取金额"""
        if not text:
            return None

        for pattern in self.AMOUNT_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def classify_category(self, text: str) -> str:
        """文章分类"""
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
                "智能",
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
            "汽车": [
                "汽车",
                "电动车",
                "新能源汽车",
                "自动驾驶",
                "智能驾驶",
                "出行",
                "车企",
            ],
            "医疗": ["医疗", "医药", "生物", "健康", "医院", "药物", "疫苗", "制药"],
            "消费": ["电商", "零售", "食品", "餐饮", "美妆", "服饰", "零售", "消费"],
            "教育": ["教育", "培训", "学习", "学校", "在线教育", "K12"],
            "地产": ["房地产", "地产", "房产", "建筑", "物业"],
            "制造": ["制造", "工厂", "生产", "供应链", "工业", "机器人"],
        }

        keywords = self.extract_keywords(text, top_k=20)
        text_lower = text.lower()

        for category, words in category_rules.items():
            count = sum(1 for w in words if w in text_lower)
            if count >= 2:
                return category

        return "其他"

    def analyze(self, text: str, title: str = "") -> Dict:
        """完整分析"""
        return {
            "keywords": self.extract_keywords(text),
            "companies": self.extract_companies(text, title),
            "amount": self.extract_amount(text),
            "category": self.classify_category(text),
            "segments": self.segment(text),
        }


# 全局NLP处理器
nlp_processor = NLPProcessor()


def segment_text(text: str) -> List[str]:
    return nlp_processor.segment(text)


def extract_keywords(text: str, top_k: int = 10) -> List[str]:
    return nlp_processor.extract_keywords(text, top_k)


def extract_companies(text: str, title: str = "") -> List[str]:
    return nlp_processor.extract_companies(text, title)


def analyze_text(text: str, title: str = "") -> Dict:
    return nlp_processor.analyze(text, title)
