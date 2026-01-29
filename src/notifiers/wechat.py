"""
企业微信通知器
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

import requests

from .base import BaseNotifier
from ..models import NewsArticle, PushResult

logger = logging.getLogger(__name__)


class WeChatNotifier(BaseNotifier):
    """企业微信通知器"""

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.webhook_url = config.get('webhook_url', '')

    def send(self, articles: List[NewsArticle], date: datetime = None) -> PushResult:
        """发送企业微信消息"""
        if not articles:
            return PushResult(
                channel=self.name,
                success=True,
                article_count=0,
                push_time=datetime.now()
            )

        if not self.enabled:
            logger.warning("企业微信通知未启用")
            return PushResult(
                channel=self.name,
                success=False,
                article_count=0,
                error_message="企业微信通知未启用",
                push_time=datetime.now()
            )

        try:
            from ..processors import Formatter
            formatter = Formatter()
            content = formatter.format_for_wechat(articles, date)

            # 发送消息
            self._send_message(content)

            self._last_result = PushResult(
                channel=self.name,
                success=True,
                article_count=len(articles),
                push_time=datetime.now()
            )

            logger.info(f"企业微信消息发送成功: {len(articles)} 篇文章")
            return self._last_result

        except Exception as e:
            logger.error(f"企业微信消息发送失败: {e}")
            self._last_result = PushResult(
                channel=self.name,
                success=False,
                article_count=0,
                error_message=str(e),
                push_time=datetime.now()
            )
            return self._last_result

    def _send_message(self, content: Dict[str, Any]):
        """发送企业微信消息"""
        if not self.webhook_url:
            raise ValueError("未配置企业微信webhook_url")

        response = requests.post(
            self.webhook_url,
            json=content,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()

        return response.json()

    def test_connection(self) -> bool:
        """测试企业微信连接"""
        try:
            # 发送测试消息
            test_content = {
                "msgtype": "text",
                "text": {
                    "content": "✅ 金融资讯机器人连接测试成功",
                    "mentioned_list": []
                }
            }

            response = requests.post(
                self.webhook_url,
                json=test_content,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('errcode') == 0:
                    logger.info("企业微信连接测试成功")
                    return True

            logger.error(f"企业微信连接测试失败: {response.text}")
            return False

        except Exception as e:
            logger.error(f"企业微信连接测试失败: {e}")
            return False
