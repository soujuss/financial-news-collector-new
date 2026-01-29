"""
数据模型模块
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class NewsCategory(str, Enum):
    """新闻分类"""
    INSURANCE = "insurance"
    BANKS = "banks"
    FINANCE = "finance"
    REGULATION = "regulation"
    INTERNET_FINANCE = "internet_finance"


class SpiderType(str, Enum):
    """爬虫类型"""
    SCRAPY = "scrapy"
    RSS = "rss"
    PLAYWRIGHT = "playwright"


@dataclass
class NewsArticle:
    """新闻文章模型"""
    id: Optional[int] = None
    title: str = ""
    url: str = ""
    source: str = ""
    category: str = ""
    source_type: str = ""  # 例如：监管机构、行业协会等
    publish_time: Optional[datetime] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    crawled_time: datetime = field(default_factory=datetime.now)
    is_push: bool = False
    push_time: Optional[datetime] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'title': self.title,
            'url': self.url,
            'source': self.source,
            'category': self.category,
            'source_type': self.source_type,
            'publish_time': self.publish_time.isoformat() if self.publish_time else None,
            'summary': self.summary,
            'content': self.content,
            'crawled_time': self.crawled_time.isoformat(),
            'is_push': self.is_push,
            'push_time': self.push_time.isoformat() if self.push_time else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'NewsArticle':
        """从字典创建"""
        return cls(
            title=data.get('title', ''),
            url=data.get('url', ''),
            source=data.get('source', ''),
            category=data.get('category', ''),
            source_type=data.get('source_type', ''),
            publish_time=datetime.fromisoformat(data['publish_time']) if data.get('publish_time') else None,
            summary=data.get('summary'),
            content=data.get('content'),
            crawled_time=datetime.fromisoformat(data['crawled_time']) if data.get('crawled_time') else datetime.now(),
            is_push=data.get('is_push', False),
            push_time=datetime.fromisoformat(data['push_time']) if data.get('push_time') else None
        )


@dataclass
class WebsiteConfig:
    """网站配置模型"""
    name: str
    url: str
    category: str
    source_type: str
    type: str = SpiderType.SCRAPY.value
    list_url: Optional[str] = None
    list_selector: Optional[str] = None
    title_selector: Optional[str] = None
    link_selector: Optional[str] = None
    date_selector: Optional[str] = None
    rss_url: Optional[str] = None
    encoding: Optional[str] = None
    # Playwright增强配置
    use_stealth: bool = False
    proxy_url: Optional[str] = None
    wait_time: int = 2  # 随机等待秒数
    headless: bool = True

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'name': self.name,
            'url': self.url,
            'category': self.category,
            'source_type': self.source_type,
            'type': self.type,
            'list_url': self.list_url,
            'list_selector': self.list_selector,
            'title_selector': self.title_selector,
            'link_selector': self.link_selector,
            'date_selector': self.date_selector,
            'rss_url': self.rss_url,
            'encoding': self.encoding,
            'use_stealth': self.use_stealth,
            'proxy_url': self.proxy_url,
            'wait_time': self.wait_time,
            'headless': self.headless
        }


@dataclass
class CrawlResult:
    """爬取结果模型"""
    source_name: str
    category: str
    source_type: str
    success: bool
    articles: List[NewsArticle] = field(default_factory=list)
    error_message: Optional[str] = None
    crawl_time: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'source_name': self.source_name,
            'category': self.category,
            'source_type': self.source_type,
            'success': self.success,
            'articles_count': len(self.articles),
            'error_message': self.error_message,
            'crawl_time': self.crawl_time.isoformat()
        }


@dataclass
class PushResult:
    """推送结果模型"""
    channel: str
    success: bool
    article_count: int = 0
    error_message: Optional[str] = None
    push_time: datetime = field(default_factory=datetime.now)
