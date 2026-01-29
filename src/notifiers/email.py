"""
邮件通知器
"""

import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Dict, Any, Optional

from .base import BaseNotifier
from ..models import NewsArticle, PushResult

logger = logging.getLogger(__name__)


class EmailNotifier(BaseNotifier):
    """邮件通知器"""

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.smtp_host = config.get('smtp_host', '')
        self.smtp_port = config.get('smtp_port', 465)
        self.smtp_ssl = config.get('smtp_ssl', True)
        self.username = config.get('username', '')
        self.password = config.get('password', '')
        self.from_name = config.get('from_name', '金融资讯机器人')
        self.to = config.get('to', [])

    def send(self, articles: List[NewsArticle], date: datetime = None) -> PushResult:
        """发送邮件"""
        if not articles:
            return PushResult(
                channel=self.name,
                success=True,
                article_count=0,
                push_time=datetime.now()
            )

        if not self.enabled:
            logger.warning("邮件通知未启用")
            return PushResult(
                channel=self.name,
                success=False,
                article_count=0,
                error_message="邮件通知未启用",
                push_time=datetime.now()
            )

        try:
            from ..processors import Formatter
            formatter = Formatter()
            subject, html_body = formatter.format_for_email(articles, date)

            # 发送邮件
            self._send_email(subject, html_body)

            self._last_result = PushResult(
                channel=self.name,
                success=True,
                article_count=len(articles),
                push_time=datetime.now()
            )

            logger.info(f"邮件发送成功: {len(articles)} 篇文章")
            return self._last_result

        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            self._last_result = PushResult(
                channel=self.name,
                success=False,
                article_count=0,
                error_message=str(e),
                push_time=datetime.now()
            )
            return self._last_result

    def _send_email(self, subject: str, html_body: str):
        """发送邮件"""
        if not self.to:
            raise ValueError("未配置收件人")

        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{self.from_name} <{self.username}>"
        msg['To'] = ', '.join(self.to)

        # 添加HTML内容
        html_part = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(html_part)

        # 发送邮件
        if self.smtp_ssl:
            server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
        else:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)

        server.ehlo()
        server.login(self.username, self.password)
        server.sendmail(self.username, self.to, msg.as_string())
        server.quit()

    def test_connection(self) -> bool:
        """测试SMTP连接"""
        try:
            if self.smtp_ssl:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=10)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)

            server.ehlo()
            if self.username and self.password:
                server.login(self.username, self.password)
            server.quit()
            return True
        except Exception as e:
            logger.error(f"SMTP连接测试失败: {e}")
            return False
