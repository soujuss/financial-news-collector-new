"""
Telegram通知器
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

import requests

from .base import BaseNotifier
from ..models import NewsArticle, PushResult

logger = logging.getLogger(__name__)


class TelegramNotifier(BaseNotifier):
    """Telegram通知器"""

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.bot_token = config.get('bot_token', '')
        self.chat_id = config.get('chat_id', '')
        self.parse_mode = config.get('parse_mode', 'HTML')

    def send(self, articles: List[NewsArticle], date: datetime = None) -> PushResult:
        """发送Telegram消息"""
        if not articles:
            return PushResult(
                channel=self.name,
                success=True,
                article_count=0,
                push_time=datetime.now()
            )

        if not self.enabled:
            logger.warning("Telegram通知未启用")
            return PushResult(
                channel=self.name,
                success=False,
                article_count=0,
                error_message="Telegram通知未启用",
                push_time=datetime.now()
            )

        try:
            from ..processors import Formatter
            formatter = Formatter()
            content = formatter.format_for_telegram(articles, date)

            # 发送消息
            self._send_message(content)

            self._last_result = PushResult(
                channel=self.name,
                success=True,
                article_count=len(articles),
                push_time=datetime.now()
            )

            logger.info(f"Telegram消息发送成功: {len(articles)} 篇文章")
            return self._last_result

        except Exception as e:
            logger.error(f"Telegram消息发送失败: {e}")
            self._last_result = PushResult(
                channel=self.name,
                success=False,
                article_count=0,
                error_message=str(e),
                push_time=datetime.now()
            )
            return self._last_result

    def _send_message(self, content: str):
        """发送Telegram消息"""
        if not self.bot_token or not self.chat_id:
            raise ValueError("未配置Telegram bot_token或chat_id")

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        # 限制消息长度（Telegram限制4096字符）
        if len(content) > 3800:
            content = content[:3800] + "\n\n...(内容过长，已截断)"

        payload = {
            "chat_id": self.chat_id,
            "text": content,
            "parse_mode": self.parse_mode,
            "disable_web_page_preview": True
        }

        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()

        return response.json()

    def test_connection(self) -> bool:
        """测试Telegram连接"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            response = requests.get(url, timeout=10)
            data = response.json()

            if data.get('ok'):
                logger.info(f"Telegram Bot连接成功: @{data['result']['username']}")
                return True
            else:
                logger.error(f"Telegram Bot连接失败: {data}")
                return False
        except Exception as e:
            logger.error(f"Telegram连接测试失败: {e}")
            return False
