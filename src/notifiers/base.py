"""
通知器基类
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..models import NewsArticle, PushResult

logger = logging.getLogger(__name__)


class BaseNotifier(ABC):
    """通知器基类"""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.enabled = config.get('enabled', False)
        self._last_result: Optional[PushResult] = None

    @abstractmethod
    def send(self, articles: List[NewsArticle], date: datetime = None) -> PushResult:
        """
        发送通知

        Args:
            articles: 文章列表
            date: 日期

        Returns:
            PushResult: 推送结果
        """
        pass

    def is_available(self) -> bool:
        """检查是否可用"""
        return self.enabled

    def get_last_result(self) -> Optional[PushResult]:
        """获取上次推送结果"""
        return self._last_result


class NotifierFactory:
    """通知器工厂"""

    _notifiers = {}

    @classmethod
    def create(cls, notifier_type: str, config: Dict[str, Any]) -> BaseNotifier:
        """创建通知器"""
        from .email import EmailNotifier
        from .telegram import TelegramNotifier
        from .wechat import WeChatNotifier

        notifiers = {
            'email': EmailNotifier,
            'telegram': TelegramNotifier,
            'wechat': WeChatNotifier,
        }

        if notifier_type not in notifiers:
            raise ValueError(f"未知的通知类型: {notifier_type}")

        return notifiers[notifier_type](notifier_type, config)

    @classmethod
    def create_all(cls, configs: Dict[str, Any]) -> List[BaseNotifier]:
        """创建所有启用的通知器"""
        notifiers = []

        for notifier_type, config in configs.items():
            if config.get('enabled', False):
                try:
                    notifier = cls.create(notifier_type, config)
                    notifiers.append(notifier)
                    logger.info(f"已启用 {notifier_type} 通知器")
                except Exception as e:
                    logger.error(f"创建 {notifier_type} 通知器失败: {e}")

        return notifiers
