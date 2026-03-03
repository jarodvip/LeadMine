"""
数据处理管道 - 整合所有处理步骤
"""

from typing import List, Dict
import logging

from app.core.database import SessionLocal
from app.models import Article, Lead
from app.processors.cleaner import ArticleCleaner
from app.processors.deduplicator import deduplicator
from app.processors.nlp_processor import nlp_processor
from app.processors.lead_extractor import lead_extractor
from app.processors.enricher import enricher

logger = logging.getLogger(__name__)


class DataProcessor:
    """数据处理器"""

    def __init__(self):
        self.cleaner = ArticleCleaner()

    def process_article(self, article_id: int) -> Dict:
        """
        处理单篇文章
        Args:
            article_id: 文章ID
        Returns:
            处理结果
        """
        db = SessionLocal()

        try:
            article = db.query(Article).filter(Article.id == article_id).first()

            if not article:
                return {"error": "文章不存在"}

            if article.status == "processed":
                return {"message": "文章已处理"}

            # 1. 清洗内容（如果需要）
            if article.content:
                cleaned_content = self.cleaner.clean_html(article.content)
                if cleaned_content != article.content:
                    article.content = cleaned_content

            # 2. 提取关键词
            text = f"{article.title} {article.content or ''}"
            keywords = nlp_processor.extract_keywords(text, top_k=10)
            article.keywords = keywords

            # 3. 分类
            category = nlp_processor.classify_category(text)
            article.category = category

            # 4. 检查重复
            is_duplicate = deduplicator.is_duplicate(text, source=article.source_name)
            article.is_duplicate = is_duplicate

            # 5. 更新状态
            article.status = "processed"
            db.commit()

            # 6. 如果不是重复，提取线索
            leads = []
            if not is_duplicate:
                leads = self._extract_leads_from_article(article, db)

            return {
                "article_id": article_id,
                "keywords": keywords,
                "category": category,
                "is_duplicate": is_duplicate,
                "leads_count": len(leads),
            }

        except Exception as e:
            logger.error(f"处理文章失败: {article_id}, {e}")
            db.rollback()
            return {"error": str(e)}
        finally:
            db.close()

    def _extract_leads_from_article(self, article: Article, db) -> List[Lead]:
        """从文章中提取线索"""
        leads = []

        try:
            article_dict = {
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "source_url": article.source_url,
                "source_name": article.source_name,
                "published_at": article.published_at,
            }

            # 提取线索
            lead_dicts = lead_extractor.extract(article_dict)

            for lead_data in lead_dicts:
                # 检查是否已存在相同线索
                existing = (
                    db.query(Lead)
                    .filter(
                        Lead.company_name == lead_data["company_name"],
                        Lead.event_type == lead_data["event_type"],
                        Lead.source_title == lead_data["source_title"],
                    )
                    .first()
                )

                if existing:
                    continue

                # 创建线索
                lead = Lead(**lead_data)
                db.add(lead)
                leads.append(lead)

            if leads:
                db.commit()
                logger.info(f"从文章 {article.id} 提取 {len(leads)} 条线索")

        except Exception as e:
            logger.error(f"提取线索失败: {e}")
            db.rollback()

        return leads

    def process_pending_articles(self, limit: int = 50) -> Dict:
        """
        批量处理待处理文章
        """
        db = SessionLocal()

        try:
            articles = (
                db.query(Article).filter(Article.status == "pending").limit(limit).all()
            )

            results = {
                "total": len(articles),
                "success": 0,
                "failed": 0,
                "duplicates": 0,
                "leads_extracted": 0,
            }

            for article in articles:
                try:
                    result = self.process_article(article.id)

                    if "error" in result:
                        results["failed"] += 1
                    else:
                        results["success"] += 1
                        if result.get("is_duplicate"):
                            results["duplicates"] += 1
                        results["leads_extracted"] += result.get("leads_count", 0)

                except Exception as e:
                    logger.error(f"处理文章异常: {article.id}, {e}")
                    results["failed"] += 1

            return results

        finally:
            db.close()

    def enrich_lead(self, lead_id: int, enrich_company_info: bool = True) -> Dict:
        """
        丰富线索信息
        """
        db = SessionLocal()

        try:
            lead = db.query(Lead).filter(Lead.id == lead_id).first()

            if not lead:
                return {"error": "线索不存在"}

            if (
                enrich_company_info
                and lead.company_name
                and lead.company_name != "未知"
            ):
                # 获取企业信息
                company_info = enricher.enrich(lead.company_name)

                if company_info:
                    # 更新线索
                    lead.enrichment_data = company_info
                    db.commit()

                    return {"lead_id": lead_id, "enriched": True, "data": company_info}

            return {"lead_id": lead_id, "enriched": False}

        finally:
            db.close()


# 全局处理器
data_processor = DataProcessor()


def process_article(article_id: int) -> Dict:
    """处理单篇文章"""
    return data_processor.process_article(article_id)


def process_pending_articles(limit: int = 50) -> Dict:
    """批量处理待处理文章"""
    return data_processor.process_pending_articles(limit)


def enrich_lead(lead_id: int) -> Dict:
    """丰富线索信息"""
    return data_processor.enrich_lead(lead_id)
