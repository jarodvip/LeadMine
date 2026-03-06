"""
企业信息补充服务 - 基于公开渠道
支持：百度爱企查、模拟数据
"""

from typing import Optional, Dict, List
import logging
import requests
import hashlib
import time

from app.core.config import settings

logger = logging.getLogger(__name__)


class EnterpriseEnricher:
    """企业信息丰富器"""

    def __init__(self):
        self.cache = {}
        self.cache_ttl = 3600
        self._aiqicha_configured = False
        self._init_api()

    def _init_api(self):
        """初始化API配置"""
        self.aiqicha_key = getattr(settings, "AIQICHA_KEY", None)
        self.aiqicha_secret = getattr(settings, "AIQICHA_SECRET", None)

        if self.aiqicha_key and self.aiqicha_secret:
            self._aiqicha_configured = True
            logger.info("爱企查API已配置")
        else:
            logger.warning("爱企查API未配置，将使用模拟数据")

    def enrich(self, company_name: str) -> Optional[Dict]:
        """
        丰富企业信息
        Args:
            company_name: 企业名称
        Returns:
            企业信息字典
        """
        if not company_name or company_name == "未知":
            return None

        if company_name in self.cache:
            cached = self.cache[company_name]
            if time.time() - cached.get("_timestamp", 0) < self.cache_ttl:
                return cached

        info = self._fetch_company_info(company_name)

        if info:
            info["_timestamp"] = time.time()
            self.cache[company_name] = info

        return info

    def _fetch_company_info(self, company_name: str) -> Optional[Dict]:
        """获取企业信息"""
        if self._aiqicha_configured:
            return self._fetch_from_aiqicha(company_name)
        return self._mock_enrich(company_name)

    def _fetch_from_aiqicha(self, company_name: str) -> Optional[Dict]:
        """从爱企查API获取企业信息"""
        try:
            url = "https://aiqicha.baidu.com/s/detail_getBasicInfo"

            timestamp = str(int(time.time()))
            sign_str = (
                f"key{self.aiqicha_key}timestamp{timestamp}secret{self.aiqicha_secret}"
            )
            sign = hashlib.md5(sign_str.encode()).hexdigest()

            params = {
                "key": self.aiqicha_key,
                "timestamp": timestamp,
                "sign": sign,
                "companyName": company_name,
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return self._parse_aiqicha_response(data.get("data", {}))

            logger.warning(f"爱企查API调用失败: {response.text}")
            return self._mock_enrich(company_name)

        except Exception as e:
            logger.error(f"爱企查API请求失败: {e}")
            return self._mock_enrich(company_name)

    def _parse_aiqicha_response(self, data: Dict) -> Dict:
        """解析爱企查响应"""
        return {
            "company_name": data.get("companyName", ""),
            "legal_person": data.get("legalPerson", ""),
            "registered_capital": data.get("registeredCapital", ""),
            "establishment_date": data.get("establishmentDate", ""),
            "business_status": data.get("businessStatus", ""),
            "phone": data.get("phone", ""),
            "email": data.get("email", ""),
            "address": data.get("address", ""),
            "business_scope": data.get("businessScope", ""),
            "industry": data.get("industry", ""),
            "source": "aiqicha",
        }

    def _mock_enrich(self, company_name: str) -> Dict:
        """模拟企业信息（仅用于开发测试）"""
        logger.info(f"使用模拟数据: {company_name}")
        return {
            "company_name": company_name,
            "legal_person": None,
            "registered_capital": None,
            "establishment_date": None,
            "business_status": "存续",
            "phone": None,
            "email": None,
            "address": None,
            "business_scope": None,
            "industry": None,
            "source": "mock",
            "note": "请配置爱企查API_KEY以获取真实数据",
        }

    def search_company(self, keyword: str) -> List[Dict]:
        """搜索企业"""
        if self._aiqicha_configured:
            return self._search_from_aiqicha(keyword)
        return []

    def _search_from_aiqicha(self, keyword: str) -> List[Dict]:
        """从爱企查搜索企业"""
        try:
            url = "https://aiqicha.baidu.com/s/detail_search"

            timestamp = str(int(time.time()))
            sign_str = (
                f"key{self.aiqicha_key}timestamp{timestamp}secret{self.aiqicha_secret}"
            )
            sign = hashlib.md5(sign_str.encode()).hexdigest()

            params = {
                "key": self.aiqicha_key,
                "timestamp": timestamp,
                "sign": sign,
                "q": keyword,
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return data.get("data", [])

            return []

        except Exception as e:
            logger.error(f"爱企查搜索失败: {e}")
            return []

    def clear_cache(self):
        """清除缓存"""
        self.cache.clear()


enricher = EnterpriseEnricher()


def enrich_company(company_name: str) -> Optional[Dict]:
    """丰富企业信息"""
    return enricher.enrich(company_name)


def search_companies(keyword: str) -> List[Dict]:
    """搜索企业"""
    return enricher.search_company(keyword)
