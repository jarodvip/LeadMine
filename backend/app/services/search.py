"""
Elasticsearch 搜索服务
"""

from typing import Dict, Optional
from elasticsearch import Elasticsearch

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Elasticsearch 索引名称
LEADS_INDEX = "leads"
ARTICLES_INDEX = "articles"


class ElasticsearchService:
    """Elasticsearch 服务"""

    def __init__(self):
        self.client = None
        self._connect()

    def _connect(self):
        """连接 Elasticsearch"""
        try:
            self.client = Elasticsearch([settings.elasticsearch_url])
            if self.client.ping():
                logger.info("Elasticsearch 连接成功")
                self._create_indices()
            else:
                logger.warning("Elasticsearch 连接失败")
                self.client = None
        except Exception as e:
            logger.warning(f"Elasticsearch 连接异常: {e}")
            self.client = None

    def _create_indices(self):
        """创建索引"""
        if not self.client:
            return

        # 线索索引
        if not self.client.indices.exists(index=LEADS_INDEX):
            self.client.indices.create(
                index=LEADS_INDEX,
                body={
                    "mappings": {
                        "properties": {
                            "id": {"type": "integer"},
                            "company_name": {"type": "text", "analyzer": "ik_max_word"},
                            "event_type": {"type": "keyword"},
                            "event_detail": {"type": "text", "analyzer": "ik_max_word"},
                            "source_name": {"type": "keyword"},
                            "status": {"type": "keyword"},
                            "confidence": {"type": "integer"},
                            "created_at": {"type": "date"},
                        }
                    }
                },
            )
            logger.info(f"创建索引: {LEADS_INDEX}")

        # 文章索引
        if not self.client.indices.exists(index=ARTICLES_INDEX):
            self.client.indices.create(
                index=ARTICLES_INDEX,
                body={
                    "mappings": {
                        "properties": {
                            "id": {"type": "integer"},
                            "title": {"type": "text", "analyzer": "ik_max_word"},
                            "content": {"type": "text", "analyzer": "ik_max_word"},
                            "source_name": {"type": "keyword"},
                            "category": {"type": "keyword"},
                            "keywords": {"type": "keyword"},
                            "crawled_at": {"type": "date"},
                        }
                    }
                },
            )
            logger.info(f"创建索引: {ARTICLES_INDEX}")

    def index_lead(self, lead: Dict) -> bool:
        """索引线索"""
        if not self.client:
            return False

        try:
            self.client.index(
                index=LEADS_INDEX,
                id=lead.get("id"),
                document={
                    "id": lead.get("id"),
                    "company_name": lead.get("company_name"),
                    "event_type": lead.get("event_type"),
                    "event_detail": lead.get("event_detail"),
                    "source_name": lead.get("source_name"),
                    "status": lead.get("status"),
                    "confidence": lead.get("confidence"),
                    "created_at": lead.get("created_at"),
                },
            )
            return True
        except Exception as e:
            logger.error(f"索引线索失败: {e}")
            return False

    def index_article(self, article: Dict) -> bool:
        """索引文章"""
        if not self.client:
            return False

        try:
            self.client.index(
                index=ARTICLES_INDEX,
                id=article.get("id"),
                document={
                    "id": article.get("id"),
                    "title": article.get("title"),
                    "content": article.get("content"),
                    "source_name": article.get("source_name"),
                    "category": article.get("category"),
                    "keywords": article.get("keywords", []),
                    "crawled_at": article.get("crawled_at"),
                },
            )
            return True
        except Exception as e:
            logger.error(f"索引文章失败: {e}")
            return False

    def search_leads(
        self,
        keyword: str,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict:
        """搜索线索"""
        if not self.client:
            return {"total": 0, "data": []}

        try:
            must = [{"match": {"company_name": keyword}}]
            if event_type:
                must.append({"term": {"event_type": event_type}})
            if status:
                must.append({"term": {"status": status}})

            body = {
                "query": {"bool": {"must": must}},
                "from": (page - 1) * page_size,
                "size": page_size,
                "sort": [{"confidence": "desc"}, {"created_at": "desc"}],
            }

            result = self.client.search(index=LEADS_INDEX, body=body)

            return {
                "total": result["hits"]["total"]["value"],
                "data": [hit["_source"] for hit in result["hits"]["hits"]],
            }
        except Exception as e:
            logger.error(f"搜索线索失败: {e}")
            return {"total": 0, "data": []}

    def search_articles(
        self,
        keyword: str,
        source_name: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict:
        """搜索文章"""
        if not self.client:
            return {"total": 0, "data": []}

        try:
            must = [{"multi_match": {"query": keyword, "fields": ["title", "content"]}}]
            if source_name:
                must.append({"term": {"source_name": source_name}})
            if category:
                must.append({"term": {"category": category}})

            body = {
                "query": {"bool": {"must": must}},
                "from": (page - 1) * page_size,
                "size": page_size,
                "sort": [{"crawled_at": "desc"}],
            }

            result = self.client.search(index=ARTICLES_INDEX, body=body)

            return {
                "total": result["hits"]["total"]["value"],
                "data": [hit["_source"] for hit in result["hits"]["hits"]],
            }
        except Exception as e:
            logger.error(f"搜索文章失败: {e}")
            return {"total": 0, "data": []}

    def delete_lead(self, lead_id: int) -> bool:
        """删除线索索引"""
        if not self.client:
            return False

        try:
            self.client.delete(index=LEADS_INDEX, id=lead_id, ignore=[404])
            return True
        except Exception as e:
            logger.error(f"删除线索索引失败: {e}")
            return False

    def delete_article(self, article_id: int) -> bool:
        """删除文章索引"""
        if not self.client:
            return False

        try:
            self.client.delete(index=ARTICLES_INDEX, id=article_id, ignore=[404])
            return True
        except Exception as e:
            logger.error(f"删除文章索引失败: {e}")
            return False


# 全局服务实例
es_service = ElasticsearchService()


def search_leads(keyword: str, **kwargs) -> Dict:
    """搜索线索"""
    return es_service.search_leads(keyword, **kwargs)


def search_articles(keyword: str, **kwargs) -> Dict:
    """搜索文章"""
    return es_service.search_articles(keyword, **kwargs)


def index_lead(lead: Dict) -> bool:
    """索引线索"""
    return es_service.index_lead(lead)


def index_article(article: Dict) -> bool:
    """索引文章"""
    return es_service.index_article(article)
