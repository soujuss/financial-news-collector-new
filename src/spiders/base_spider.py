"""
基础爬虫类
"""

import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from ..config import config
from ..models import NewsArticle, SpiderType, WebsiteConfig

logger = logging.getLogger(__name__)


class BaseSpider(ABC):
    """爬虫基类"""

    def __init__(self, website_config: WebsiteConfig):
        self.config = website_config
        self.name = website_config.name
        self.base_url = website_config.url
        self.category = website_config.category
        self.source_type = website_config.source_type
        self.encoding = getattr(website_config, 'encoding', None)
        self.use_proxy = getattr(website_config, 'use_proxy', False)

        spider_config = config.get_spider_config()
        self.timeout = spider_config.get('timeout', 30)
        self.retry_times = spider_config.get('retry_times', 3)
        self.delay = spider_config.get('delay', 1)
        self.max_items = spider_config.get('max_items_per_source', 50)

        # 获取代理设置
        proxy_config = spider_config.get('proxy', {})
        self.proxy_url = proxy_config.get('url', 'http://127.0.0.1:7897')

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': spider_config.get('user_agent',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

    def crawl(self) -> List[NewsArticle]:
        """执行爬取"""
        logger.info(f"开始爬取: {self.name} ({self.base_url})")
        try:
            articles = self._crawl_impl()
            logger.info(f"爬取完成: {self.name}, 获取 {len(articles)} 篇文章")
            return articles
        except Exception as e:
            logger.error(f"爬取失败: {self.name}, 错误: {e}")
            return []

    @abstractmethod
    def _crawl_impl(self) -> List[NewsArticle]:
        """实际爬取逻辑，子类实现"""
        pass

    def _make_request(self, url: str, retries: int = None) -> Optional[requests.Response]:
        """发送HTTP请求"""
        if retries is None:
            retries = self.retry_times

        last_error = None
        for attempt in range(retries):
            try:
                # 设置代理
                proxies = {}
                if self.use_proxy or (hasattr(self.config, 'use_proxy') and self.config.use_proxy):
                    proxies = {
                        'http': self.proxy_url,
                        'https': self.proxy_url,
                    }
                    logger.debug(f"[{self.name}] 使用代理: {self.proxy_url}")

                response = self.session.get(url, timeout=self.timeout, proxies=proxies)
                response.raise_for_status()

                # 正确处理中文编码
                # 优先使用配置的编码，其次使用响应头中的编码
                if self.encoding:
                    response.encoding = self.encoding
                elif response.apparent_encoding:
                    response.encoding = response.apparent_encoding
                elif 'charset' in response.headers.get('content-type', '').lower():
                    # 从 Content-Type 中提取编码
                    content_type = response.headers.get('content-type', '')
                    match = re.search(r'charset=([^\s;]+)', content_type, re.IGNORECASE)
                    if match:
                        response.encoding = match.group(1)
                else:
                    # 默认尝试 utf-8
                    response.encoding = 'utf-8'

                return response
            except requests.RequestException as e:
                last_error = e
                if attempt < retries - 1:
                    import time
                    time.sleep(self.delay)

        # 只在最后一次失败时输出警告
        if last_error:
            error_type = type(last_error).__name__
            if "timed out" in str(last_error).lower():
                logger.debug(f"[{self.name}] 请求超时: {url}")
            elif "404" in str(last_error):
                logger.debug(f"[{self.name}] 页面不存在 (404): {url}")
            elif "503" in str(last_error):
                logger.debug(f"[{self.name}] 服务暂时不可用 (503): {url}")
            else:
                logger.debug(f"[{self.name}] 请求失败: {url}")
        return None

    def _parse_list_page(self, html: str, list_selector: str = None,
                         title_selector: str = None, link_selector: str = None) -> List[Dict[str, str]]:
        """解析列表页"""
        soup = BeautifulSoup(html, 'lxml')
        items = []

        # 使用配置的选择器或默认值
        selector = list_selector or self.config.list_selector or '.news-list li'
        title_s = title_selector or self.config.title_selector or ''
        link_s = link_selector or self.config.link_selector or ''

        # 获取URL排除模式
        exclude_patterns = getattr(self.config, 'exclude_patterns', [])

        elements = soup.select(selector)
        for elem in elements[:self.max_items]:
            try:
                # 如果 title_selector 为空，使用元素本身
                if title_s:
                    title_elem = elem.select_one(title_s)
                else:
                    title_elem = elem

                # 如果 link_selector 为空，使用元素本身
                if link_s:
                    link_elem = elem.select_one(link_s)
                else:
                    link_elem = elem

                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    link = link_elem.get('href', '')

                    if title and link:
                        # 处理相对链接
                        if not link.startswith('http'):
                            link = urljoin(self.base_url, link)

                        # URL过滤：排除广告、导航等无效链接
                        if exclude_patterns and any(pattern in link for pattern in exclude_patterns):
                            logger.debug(f"排除无效链接: {link}")
                            continue

                        items.append({
                            'title': title,
                            'url': link
                        })
            except Exception as e:
                logger.debug(f"解析列表项失败: {e}")
                continue

        return items

    def _extract_article_content(self, url: str, html: str) -> tuple:
        """提取文章内容"""
        soup = BeautifulSoup(html, 'lxml')

        # 尝试多种方式提取正文
        content = ""
        summary = ""

        # 方法1: 查找文章容器
        article_elem = soup.find('article') or soup.find(class_=re.compile(r'article|content|post|entry'))

        if article_elem:
            # 移除脚本和样式
            for tag in article_elem.find_all(['script', 'style', 'nav', 'header', 'footer']):
                tag.decompose()

            # 获取纯文本
            paragraphs = article_elem.find_all('p')
            if paragraphs:
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs])
                summary = paragraphs[0].get_text(strip=True)[:200] if paragraphs else ""

        # 方法2: 如果没有找到，尝试其他选择器
        if not content:
            for selector in ['.content', '.article-body', '.post-content', '#content']:
                elem = soup.select_one(selector)
                if elem:
                    for tag in elem.find_all(['script', 'style', 'nav', 'header', 'footer']):
                        tag.decompose()
                    content = elem.get_text(strip=True)
                    summary = content[:200]
                    break

        # 方法3: 使用正则表达式提取
        if not content:
            # 移除脚本和样式
            for tag in soup.find_all(['script', 'style']):
                tag.decompose()
            body = soup.find('body')
            if body:
                content = body.get_text(strip=True)
                summary = content[:200]

        # 清理内容
        content = self._clean_content(content)
        summary = self._clean_content(summary)

        return summary, content

    def _clean_content(self, text: str) -> str:
        """清理内容"""
        if not text:
            return ""

        # 移除多余空白
        lines = text.split('\n')
        lines = [line.strip() for line in lines if line.strip()]
        return '\n'.join(lines)

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """解析日期"""
        if not date_str:
            return None

        date_str = date_str.strip()

        # 常见日期格式
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d',
            '%Y/%m/%d %H:%M:%S',
            '%Y/%m/%d %H:%M',
            '%Y/%m/%d',
            '%m-%d %H:%M',
            '%m月%d日 %H:%M',
            '%m月%d日',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    def _create_article(self, title: str, url: str, summary: str = "", content: str = "",
                        publish_time: datetime = None) -> NewsArticle:
        """创建文章对象"""
        return NewsArticle(
            title=title,
            url=url,
            source=self.name,
            category=self.category,
            source_type=self.source_type,
            publish_time=publish_time,
            summary=summary,
            content=content,
            crawled_time=datetime.now()
        )
