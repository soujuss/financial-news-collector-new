"""
文章内容提取器
"""

import logging
import re
from typing import Tuple, Optional
from datetime import datetime

from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

logger = logging.getLogger(__name__)


class ArticleExtractor:
    """文章内容提取器"""

    def __init__(self):
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)

        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords', quiet=True)

        try:
            nltk.data.find('tokenizers/punkt_tab')
        except LookupError:
            nltk.download('punkt_tab', quiet=True)

    def extract(self, html: str, url: str = "") -> Tuple[Optional[str], Optional[str], Optional[datetime]]:
        """
        从HTML中提取文章信息

        Returns:
            tuple: (title, content, publish_time)
        """
        if not html:
            return None, None, None

        soup = BeautifulSoup(html, 'lxml')

        # 提取标题
        title = self._extract_title(soup)

        # 提取发布时间
        publish_time = self._extract_publish_time(soup)

        # 提取正文
        content = self._extract_content(soup)

        # 提取摘要
        summary = self._extract_summary(content) if content else ""

        return title, content, publish_time

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取标题"""
        # 尝试多种方式获取标题
        title_selectors = [
            'article h1',
            '.article-title',
            '.post-title',
            '.entry-title',
            'h1.title',
            'h1',
            'title'
        ]

        for selector in title_selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                if text and len(text) > 5:
                    return text

        # 如果都失败，返回页面title
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)

        return ""

    def _extract_publish_time(self, soup: BeautifulSoup) -> Optional[datetime]:
        """提取发布时间"""
        # 查找包含时间的元素
        time_patterns = [
            r'\d{4}-\d{2}-\d{2}\s*\d{2}:\d{2}:\d{2}',
            r'\d{4}-\d{2}-\d{2}\s*\d{2}:\d{2}',
            r'\d{4}-\d{2}-\d{2}',
            r'\d{4}/\d{2}/\d{2}',
            r'\d{2}月\d{2}日\s*\d{2}:\d{2}',
            r'\d{2}月\d{2}日',
        ]

        # 查找meta标签中的时间
        meta_time = soup.find('meta', property='article:published_time')
        if meta_time and meta_time.get('content'):
            return self._parse_time(meta_time['content'])

        meta_time = soup.find('meta', attrs={'name': 'pubdate'})
        if meta_time and meta_time.get('content'):
            return self._parse_time(meta_time['content'])

        # 查找time标签
        time_elem = soup.find('time')
        if time_elem and time_elem.get('datetime'):
            return self._parse_time(time_elem['datetime'])

        # 查找常见的时间元素
        time_selectors = [
            '.publish-time',
            '.publish-time span',
            '.article-time',
            '.post-time',
            '.time',
            '.date',
            '[class*="time"]',
            '[class*="date"]'
        ]

        for selector in time_selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                for pattern in time_patterns:
                    match = re.search(pattern, text)
                    if match:
                        dt = self._parse_time(match.group())
                        if dt:
                            return dt

        return None

    def _parse_time(self, time_str: str) -> Optional[datetime]:
        """解析时间字符串"""
        if not time_str:
            return None

        formats = [
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d',
            '%Y/%m/%d %H:%M:%S',
            '%Y/%m/%d %H:%M',
            '%Y/%m/%d',
            '%m月%d日 %H:%M',
            '%m月%d日',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue

        return None

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取正文内容"""
        # 移除不需要的元素
        for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer',
                                   'aside', '.sidebar', '.advertisement',
                                   '.ad', '.comments', '.comment']):
            tag.decompose()

        # 查找文章主体
        article_selectors = [
            'article',
            '.article-content',
            '.post-content',
            '.entry-content',
            '.article-body',
            '.post-body',
            '.content',
            '#article-content',
            '#content',
            '.main-content'
        ]

        content_elem = None
        for selector in article_selectors:
            elem = soup.select_one(selector)
            if elem:
                content_elem = elem
                break

        if not content_elem:
            content_elem = soup.find('body')
            if not content_elem:
                return ""

        # 获取所有段落
        paragraphs = content_elem.find_all('p')

        if not paragraphs:
            # 如果没有p标签，获取所有文本节点
            text = content_elem.get_text(separator='\n')
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            return '\n'.join(lines)

        # 提取段落文本
        text_parts = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text and len(text) > 10:  # 过滤太短的段落
                text_parts.append(text)

        return '\n\n'.join(text_parts)

    def _extract_summary(self, content: str, max_length: int = 200) -> str:
        """提取摘要"""
        if not content:
            return ""

        # 取前几句话
        try:
            sentences = sent_tokenize(content[:1000])
            if sentences:
                summary = sentences[0]
                if len(summary) > max_length:
                    summary = summary[:max_length] + "..."
                return summary
        except Exception:
            pass

        # 如果无法分句，直接取前N个字符
        if len(content) > max_length:
            return content[:max_length] + "..."

        return content
