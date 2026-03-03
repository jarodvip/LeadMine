"""
定时任务调度器 - 支持分布式锁
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import redis

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.core.config import settings
from app.models.models import DataSource

logger = get_logger(__name__)


class DistributedLock:
    """分布式锁（基于 Redis）"""

    def __init__(self, redis_url: str, lock_key: str, ttl: int = 300):
        self.redis_client = redis.from_url(redis_url)
        self.lock_key = lock_key
        self.ttl = ttl

    def acquire(self) -> bool:
        """获取锁"""
        try:
            return self.redis_client.set(self.lock_key, "1", nx=True, ex=self.ttl)
        except Exception as e:
            logger.warning(f"获取分布式锁失败: {e}")
            return True  # 失败时允许执行

    def release(self):
        """释放锁"""
        try:
            self.redis_client.delete(self.lock_key)
        except Exception as e:
            logger.warning(f"释放分布式锁失败: {e}")


class CrawlScheduler:
    """爬虫定时任务调度器"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.running = False

    def start(self):
        """启动调度器"""
        if self.running:
            logger.warning("调度器已在运行")
            return

        # 从数据库加载数据源并添加任务
        self._load_tasks_from_db()

        self.scheduler.start()
        self.running = True
        logger.info("爬虫调度器已启动")

    def stop(self):
        """停止调度器"""
        if not self.running:
            return

        self.scheduler.shutdown(wait=False)
        self.running = False
        logger.info("爬虫调度器已停止")

    def _load_tasks_from_db(self):
        """从数据库加载任务"""
        db = SessionLocal()
        try:
            sources = db.query(DataSource).filter(DataSource.enabled == True).all()  # noqa: E712

            for source in sources:
                self.add_crawl_task(source)

            logger.info(f"已加载 {len(sources)} 个爬虫任务")

        finally:
            db.close()

    def add_crawl_task(self, source):
        """添加爬虫任务"""
        job_id = f"crawl_{source.id}"

        # 如果任务已存在，先移除
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        # 添加新任务
        self.scheduler.add_job(
            self._crawl_source,
            trigger=IntervalTrigger(minutes=source.crawl_interval),
            args=[source.id],
            id=job_id,
            name=f"crawl_{source.name}",
            replace_existing=True,
        )

        logger.info(f"添加爬虫任务: {source.name}, 间隔: {source.crawl_interval}分钟")

    def remove_crawl_task(self, source_id: int):
        """移除爬虫任务"""
        job_id = f"crawl_{source_id}"

        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info(f"移除爬虫任务: {job_id}")

    def _crawl_source(self, source_id: int):
        """执行爬取任务（支持分布式锁）"""
        from scrapers.spider_factory import SpiderFactory

        # 获取分布式锁
        lock = DistributedLock(settings.redis_url, f"lock:crawl:{source_id}", ttl=300)
        if not lock.acquire():
            logger.info(f"爬取任务正在执行中，跳过: source_id={source_id}")
            return

        db = SessionLocal()
        try:
            source = db.query(DataSource).filter(DataSource.id == source_id).first()

            if not source or not source.enabled:
                logger.warning(f"数据源不存在或已禁用: {source_id}")
                return

            logger.info(f"开始爬取: {source.name}")

            # 执行爬取
            articles = SpiderFactory.crawl_source(
                {
                    "type": source.type,
                    "url": source.url,
                    "name": source.name,
                    "config": source.config,
                }
            )

            # 保存文章到数据库
            from app.services.article_service import save_articles

            saved_count = save_articles(articles, source.name)

            # 更新最后抓取时间
            source.last_crawl_at = datetime.now()
            db.commit()

            logger.info(
                f"爬取完成: {source.name}, 获取 {len(articles)} 篇, 保存 {saved_count} 篇"
            )

            # 自动处理新文章
            if saved_count > 0:
                from app.services.processor import data_processor

                result = data_processor.process_pending_articles(limit=50)
                logger.info(f"文章处理完成: {result}")

        except Exception as e:
            logger.error(f"爬取任务失败 {source_id}: {e}")
        finally:
            db.close()
            lock.release()

    def trigger_manual_crawl(self, source_id: int):
        """手动触发爬取"""
        self._crawl_source(source_id)


# 全局调度器实例
scheduler = CrawlScheduler()
