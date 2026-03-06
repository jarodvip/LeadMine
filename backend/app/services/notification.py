"""
通知服务 - 邮件和Webhook通知
"""

import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
import logging

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class NotificationService:
    """通知服务"""

    def __init__(self):
        self.smtp_host = getattr(settings, "SMTP_HOST", None)
        self.smtp_port = getattr(settings, "SMTP_PORT", 587)
        self.smtp_user = getattr(settings, "SMTP_USER", None)
        self.smtp_password = getattr(settings, "SMTP_PASSWORD", None)
        self.smtp_from = getattr(settings, "SMTP_FROM", self.smtp_user)
        self.webhook_url = getattr(settings, "WEBHOOK_URL", None)
        self.webhook_secret = getattr(settings, "WEBHOOK_SECRET", None)

    def notify_new_leads(self, leads: List[Dict]) -> bool:
        """通知新线索"""
        if not leads:
            return True

        subject = f"LeadMine - 新增 {len(leads)} 条线索"
        body = self._build_leads_body(leads)

        return self._send_notifications(subject, body)

    def notify_alert(self, alert: Dict) -> bool:
        """通知告警"""
        subject = f"[{alert.get('severity', 'info').upper()}] LeadMine - {alert.get('name', '告警')}"
        body = alert.get("message", "")

        return self._send_notifications(subject, body)

    def _build_leads_body(self, leads: List[Dict]) -> str:
        """构建线索通知内容"""
        lines = ["以下是今日新增的线索：\n"]

        for i, lead in enumerate(leads[:10], 1):
            lines.append(f"{i}. {lead.get('company_name', '未知')}")
            lines.append(f"   类型: {lead.get('event_type', '未知')}")
            if lead.get("event_amount"):
                lines.append(f"   金额: {lead.get('event_amount')}")
            if lead.get("source_name"):
                lines.append(f"   来源: {lead.get('source_name')}")
            lines.append("")

        if len(leads) > 10:
            lines.append(f"\n... 还有 {len(leads) - 10} 条线索")

        lines.append("\n---\n查看更多: http://localhost:8501/leads")

        return "\n".join(lines)

    def _send_notifications(self, subject: str, body: str) -> bool:
        """发送所有通知"""
        success = True

        if self.smtp_host and self.smtp_user:
            if not self._send_email(subject, body):
                success = False

        if self.webhook_url:
            if not self._send_webhook(subject, body):
                success = False

        if not self.smtp_host and not self.webhook_url:
            logger.info(f"通知（未配置）: {subject}")

        return success

    def _send_email(self, subject: str, body: str) -> bool:
        """发送邮件通知"""
        try:
            recipients = getattr(settings, "NOTIFY_EMAILS", "").split(",")
            recipients = [r.strip() for r in recipients if r.strip()]

            if not recipients:
                logger.warning("未配置邮件接收者")
                return False

            msg = MIMEMultipart()
            msg["From"] = self.smtp_from
            msg["To"] = ", ".join(recipients)
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"邮件通知已发送: {subject}")
            return True

        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False

    def _send_webhook(self, subject: str, body: str) -> bool:
        """发送Webhook通知"""
        try:
            payload = {
                "subject": subject,
                "content": body,
                "timestamp": self._get_timestamp(),
            }

            headers = {"Content-Type": "application/json"}

            if self.webhook_secret:
                import hmac
                import hashlib

                signature = hmac.new(
                    self.webhook_secret.encode(),
                    payload.__str__().encode(),
                    hashlib.sha256,
                ).hexdigest()
                headers["X-Signature"] = signature

            response = requests.post(
                self.webhook_url, json=payload, headers=headers, timeout=10
            )

            if response.status_code < 400:
                logger.info(f"Webhook通知已发送: {subject}")
                return True
            else:
                logger.warning(f"Webhook返回错误: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"发送Webhook失败: {e}")
            return False

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime

        return datetime.now().isoformat()


notification_service = NotificationService()


def notify_new_leads(leads: List[Dict]) -> bool:
    """通知新线索"""
    return notification_service.notify_new_leads(leads)


def notify_alert(alert: Dict) -> bool:
    """通知告警"""
    return notification_service.notify_alert(alert)
