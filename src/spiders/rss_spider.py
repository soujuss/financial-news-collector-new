"""
RSS爬虫
"""

import logging
from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin

import feedparser

from .base_spider import BaseSpider
from ..models import NewsArticle, SpiderType, WebsiteConfig

logger = logging.getLogger(__name__)


class RSSSpider(BaseSpider):
    """RSS订阅爬虫"""

    def __init__(self, website_config: WebsiteConfig):
        super().__init__(website_config)
        self.type = SpiderType.RSS
        # 如果配置了rss_url则使用，否则尝试常见的rss地址
        self.rss_url = website_config.rss_url

    def _crawl_impl(self) -> List[NewsArticle]:
        """RSS爬取实现"""
        articles = []

        # 获取RSS feed URL
        feed_url = self._get_feed_url()
        if not feed_url:
            logger.warning(f"无法找到RSS feed: {self.name}")
            return []

        try:
            # 解析RSS
            feed = feedparser.parse(feed_url)

            if feed.bozo:
                logger.warning(f"RSS解析失败: {self.name}, 错误: {feed.bozo_exception}")

            for entry in feed.entries[:self.max_items]:
                try:
                    article = self._parse_entry(entry)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.debug(f"解析RSS条目失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"获取RSS失败: {self.name}, 错误: {e}")

        return articles

    def _get_feed_url(self) -> Optional[str]:
        """获取RSS feed URL"""
        if self.rss_url:
            return self.rss_url

        # 尝试常见的RSS地址
        common_paths = [
            '/rss',
            '/feed',
            '/feed.xml',
            '/rss.xml',
            '/atom.xml',
            '/rss/feed.xml',
        ]

        for path in common_paths:
            url = urljoin(self.base_url, path)
            response = self._make_request(url)
            if response and 'xml' in response.headers.get('Content-Type', '').lower():
                return url

        return None

    def _parse_entry(self, entry) -> Optional[NewsArticle]:
        """解析RSS条目"""
        # 获取标题
        title = entry.get('title', '').strip()
        if not title:
            return None

        # 获取链接
        link = entry.get('link', '')
        if not link:
            return None

        # 获取发布时间
        publish_time = None
        if hasattr(entry, 'published_parsed'):
            publish_time = datetime(*entry.published_parsed[:6])
        elif hasattr(entry, 'updated_parsed'):
            publish_time = datetime(*entry.updated_parsed[:6])
        elif hasattr(entry, 'published'):
            publish_time = self._parse_date(entry.published)

        # 获取摘要
        summary = ""
        if hasattr(entry, 'summary'):
            summary = entry.summary
        elif hasattr(entry, 'description'):
            summary = entry.description

        # 清理HTML标签
        from bs4 import BeautifulSoup
        if summary:
            soup = BeautifulSoup(summary, 'lxml')
            summary = soup.get_text(strip=True)[:500]

        return self._create_article(
            title=title,
            url=link,
            summary=summary,
            publish_time=publish_time
        )
