"""
Scrapy爬虫
"""

import logging
from typing import List, Optional

from .base_spider import BaseSpider
from ..models import NewsArticle, SpiderType, WebsiteConfig

logger = logging.getLogger(__name__)


class ScrapySpider(BaseSpider):
    """Scrapy爬虫实现"""

    def __init__(self, website_config: WebsiteConfig):
        super().__init__(website_config)
        self.type = SpiderType.SCRAPY

    def _crawl_impl(self) -> List[NewsArticle]:
        """Scrapy爬取实现"""
        articles = []

        # 获取列表页URL
        list_url = self.config.list_url or self.base_url

        # 发送请求
        response = self._make_request(list_url)
        if not response:
            return []

        # 解析列表页
        items = self._parse_list_page(response.text)

        for item in items:
            try:
                # 获取文章详情
                article = self._crawl_article(item['url'], item['title'])
                if article:
                    articles.append(article)
            except Exception as e:
                logger.debug(f"爬取文章失败: {item.get('url')}, 错误: {e}")
                continue

        return articles

    def _crawl_article(self, url: str, title: str) -> Optional[NewsArticle]:
        """爬取单篇文章"""
        response = self._make_request(url)
        if not response:
            return None

        # 提取内容
        summary, content = self._extract_article_content(url, response.text)

        return self._create_article(
            title=title,
            url=url,
            summary=summary,
            content=content
        )
