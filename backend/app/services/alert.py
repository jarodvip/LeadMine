"""
告警服务
"""

import redis
from datetime import datetime, timedelta
from typing import List, Dict
from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.core.logging import get_logger
from app.core.database import SessionLocal
from app.models import Lead, Article, DataSource

logger = get_logger(__name__)


class AlertRule:
    """告警规则"""

    def __init__(
        self,
        name: str,
        condition: callable,
        threshold: any,
        message: str,
        severity: str = "warning",
    ):
        self.name = name
        self.condition = condition
        self.threshold = threshold
        self.message = message
        self.severity = severity


class AlertService:
    """告警服务"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.alerts: List[Dict] = []
        self.redis_client = None

        try:
            self.redis_client = redis.from_url(settings.redis_url)
            self.redis_client.ping()
            logger.info("告警服务 Redis 连接成功")
        except Exception as e:
            logger.warning(f"告警服务 Redis 连接失败: {e}")

    def check_all_rules(self) -> List[Dict]:
        """检查所有告警规则"""
        alerts = []
        db = SessionLocal()

        try:
            # 规则 1: 今日无新线索
            today_start = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            leads_today = db.query(Lead).filter(Lead.created_at >= today_start).count()

            if leads_today == 0:
                alerts.append(
                    {
                        "name": "no_new_leads_today",
                        "severity": "warning",
                        "message": "今日暂无新线索，请检查爬虫是否正常运行",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            # 规则 2: 爬虫失败过多
            sources = db.query(DataSource).filter(DataSource.enabled == True).all()  # noqa: E712
            failed_sources = []
            for source in sources:
                if source.last_crawl_at:
                    time_since_crawl = datetime.now() - source.last_crawl_at
                    # 如果超过抓取间隔的 2 倍时间未抓取，视为失败
                    if time_since_crawl > timedelta(minutes=source.crawl_interval * 2):
                        failed_sources.append(source.name)

            if failed_sources:
                alerts.append(
                    {
                        "name": "crawl_failures",
                        "severity": "warning",
                        "message": f"以下数据源长时间未抓取: {', '.join(failed_sources)}",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            # 规则 3: 待处理文章过多
            pending_articles = (
                db.query(Article).filter(Article.status == "pending").count()
            )
            if pending_articles > 1000:
                alerts.append(
                    {
                        "name": "pending_articles_high",
                        "severity": "critical",
                        "message": f"待处理文章过多: {pending_articles} 篇",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            # 规则 4: 重复文章过多
            duplicates = db.query(Article).filter(Article.is_duplicate == True).count()  # noqa: E712
            total = db.query(Article).count()
            if total > 0 and duplicates / total > 0.5:
                alerts.append(
                    {
                        "name": "high_duplicate_rate",
                        "severity": "info",
                        "message": f"重复文章比例较高: {duplicates}/{total} ({duplicates * 100 // total}%)",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            # 规则 5: 数据库连接异常（检查 MySQL）
            try:
                db.execute("SELECT 1")
            except Exception as e:
                alerts.append(
                    {
                        "name": "database_error",
                        "severity": "critical",
                        "message": f"数据库连接异常: {str(e)}",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        except Exception as e:
            logger.error(f"告警检查失败: {e}")
        finally:
            db.close()

        # 发送告警到 Redis
        self._publish_alerts(alerts)

        return alerts

    def _publish_alerts(self, alerts: List[Dict]):
        """发布告警到 Redis"""
        if not self.redis_client or not alerts:
            return

        try:
            for alert in alerts:
                # 发布告警
                self.redis_client.lpush("alerts:queue", str(alert))

            # 只保留最近 100 条告警
            self.redis_client.ltrim("alerts:queue", 0, 99)

            # 设置告警 key 的过期时间
            self.redis_client.expire("alerts:queue", 86400)

        except Exception as e:
            logger.warning(f"发布告警失败: {e}")

    def get_recent_alerts(self, limit: int = 10) -> List[Dict]:
        """获取最近告警"""
        if not self.redis_client:
            return []

        try:
            alerts = self.redis_client.lrange("alerts:queue", 0, limit - 1)
            return [eval(a) for a in alerts]  # noqa: S314
        except Exception as e:
            logger.warning(f"获取告警失败: {e}")
            return []

    def start(self):
        """启动告警检查调度"""
        # 检查任务是否已存在，如果存在先移除
        if self.scheduler.get_job("alert_checker"):
            self.scheduler.remove_job("alert_checker")
        
        # 每 5 分钟检查一次
        self.scheduler.add_job(
            self.check_all_rules,
            "interval",
            minutes=5,
            id="alert_checker",
            name="告警检查",
            replace_existing=True,
        )
        self.scheduler.start()
        logger.info("告警服务已启动")

    def stop(self):
        """停止告警服务"""
        self.scheduler.shutdown()


# 全局告警服务
alert_service = AlertService()


def check_alerts() -> List[Dict]:
    """检查告警"""
    return alert_service.check_all_rules()


def get_alerts(limit: int = 10) -> List[Dict]:
    """获取告警"""
    return alert_service.get_recent_alerts(limit)
