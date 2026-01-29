"""
去重处理器
"""

import hashlib
import logging
import re
from typing import List, Set, Dict
from collections import defaultdict

from ..models import NewsArticle

logger = logging.getLogger(__name__)


class Deduplicator:
    """文章去重处理器"""

    def __init__(self):
        self._seen_urls: Set[str] = set()
        self._seen_hashes: Set[str] = set()
        self._title_index: Dict[str, List[str]] = defaultdict(list)  # 标题哈希 -> URLs

    def add_seen(self, url: str, title: str = ""):
        """添加已见的URL"""
        self._seen_urls.add(url)

        if title:
            title_hash = self._normalize_title(title)
            self._title_index[title_hash].append(url)

    def is_seen(self, url: str, title: str = "") -> bool:
        """检查是否已存在"""
        # URL完全匹配
        if url in self._seen_urls:
            return True

        # 标准化后标题匹配
        if title:
            title_hash = self._normalize_title(title)
            if title_hash in self._title_index:
                return True

        return False

    def deduplicate(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """对文章列表去重"""
        unique_articles = []

        for article in articles:
            if self.is_seen(article.url, article.title):
                logger.debug(f"去重跳过: {article.title}")
                continue

            # 计算内容哈希
            content_hash = self._compute_content_hash(article)
            if content_hash in self._seen_hashes:
                logger.debug(f"内容重复跳过: {article.title}")
                continue

            # 标记为已见
            self.add_seen(article.url, article.title)
            self._seen_hashes.add(content_hash)
            unique_articles.append(article)

        logger.info(f"去重: 输入 {len(articles)} 篇, 输出 {len(unique_articles)} 篇")
        return unique_articles

    def _normalize_title(self, title: str) -> str:
        """标准化标题"""
        if not title:
            return ""

        # 转小写
        title = title.lower()

        # 移除特殊字符
        title = re.sub(r'[^\w\s]', '', title)

        # 移除多余空格
        title = ' '.join(title.split())

        return title

    def _compute_content_hash(self, article: NewsArticle) -> str:
        """计算内容哈希"""
        # 组合关键字段
        content = f"{article.title}|{article.source}|{article.publish_time}"

        # 添加摘要
        if article.summary:
            content += f"|{article.summary[:100]}"

        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def clear(self):
        """清空已见记录"""
        self._seen_urls.clear()
        self._seen_hashes.clear()
        self._title_index.clear()

    def load_from_database(self, urls: List[str]):
        """从数据库加载已见的URL"""
        self._seen_urls.update(urls)
        logger.info(f"从数据库加载了 {len(urls)} 个已见URL")
