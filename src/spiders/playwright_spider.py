"""
Playwright动态页面爬虫
"""

import asyncio
import logging
import random
import time
from typing import List, Optional
from urllib.parse import urljoin

from .base_spider import BaseSpider
from ..config import config
from ..models import NewsArticle, SpiderType, WebsiteConfig

logger = logging.getLogger(__name__)

# 随机User-Agent列表
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


class PlaywrightSpider(BaseSpider):
    """Playwright动态页面爬虫"""

    def __init__(self, website_config: WebsiteConfig):
        super().__init__(website_config)
        self.type = SpiderType.PLAYWRIGHT
        self._browser = None

    def _get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        return random.choice(USER_AGENTS)

    async def _create_stealth_context(self, p) -> dict:
        """创建反检测浏览器上下文"""
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--mute-audio',
            '--disable-accelerated-2d-canvas',
        ]

        # 获取代理设置
        spider_config = config.get_spider_config()
        proxy_config = spider_config.get('proxy', {})
        proxy_enabled = proxy_config.get('enabled', False) or (hasattr(self.config, 'use_proxy') and self.config.use_proxy)
        proxy_url = proxy_config.get('url', 'http://127.0.0.1:7897')

        # 启动浏览器
        browser = await p.chromium.launch(
            headless=self.config.headless if hasattr(self.config, 'headless') else True,
            args=browser_args
        )

        # 构建context参数
        context_params = {
            'user_agent': self._get_random_user_agent(),
            'viewport': {'width': 1920, 'height': 1080},
            'locale': 'zh-CN',
            'timezone_id': 'Asia/Shanghai',
            'java_script_enabled': True,
            'has_touch': False,
            'color_scheme': None,
            'reduced_motion': 'no-preference',
        }

        # 如果启用代理，添加代理设置
        if proxy_enabled:
            context_params['proxy'] = {'server': proxy_url}
            logger.info(f"[{self.name}] Playwright使用代理: {proxy_url}")

        # 创建上下文
        context = await browser.new_context(**context_params)

        # 注入stealth脚本
        try:
            from playwright_stealth import Stealth
            page = await context.new_page()
            stealth = Stealth()
            await stealth.apply(page)
        except ImportError:
            logger.warning("playwright-stealth未安装，跳过stealth注入")
        except Exception as e:
            logger.debug(f"stealth注入失败: {e}")

        return {'browser': browser, 'context': context}

    async def _crawl_impl_async(self) -> List[NewsArticle]:
        """异步爬取实现"""
        articles = []

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                # 创建反检测上下文
                resources = await self._create_stealth_context(p)
                browser = resources['browser']
                context = resources['context']

                page = await context.new_page()

                # 获取列表页
                list_url = self.config.list_url or self.base_url
                logger.info(f"加载页面: {list_url}")

                # 随机等待
                wait_time = getattr(self.config, 'wait_time', 2) + random.uniform(0, 2)

                await page.goto(list_url, wait_until='domcontentloaded', timeout=30000)

                # 等待页面渲染
                await page.wait_for_timeout(int(wait_time * 1000))

                # 等待内容加载
                try:
                    await page.wait_for_selector(
                        self.config.list_selector or '.news-list li',
                        timeout=10000
                    )
                except Exception as e:
                    logger.warning(f"等待选择器超时: {e}")

                # 解析列表
                items = await self._parse_list_page_async(page)

                for item in items:
                    try:
                        article = await self._crawl_article_async(page, item['url'], item['title'])
                        if article:
                            articles.append(article)
                    except Exception as e:
                        logger.debug(f"爬取文章失败: {item.get('url')}, 错误: {e}")
                        continue

                await browser.close()

        except ImportError:
            logger.error("Playwright未安装，请运行: pip install playwright && playwright install")
        except Exception as e:
            logger.error(f"Playwright爬取失败: {self.name}, 错误: {e}", exc_info=True)

        return articles

    async def _parse_list_page_async(self, page) -> List[dict]:
        """异步解析列表页"""
        items = []

        selector = self.config.list_selector or '.news-list li'
        title_s = self.config.title_selector if self.config.title_selector else None
        link_s = self.config.link_selector if self.config.link_selector else None

        # 获取URL排除模式
        exclude_patterns = getattr(self.config, 'exclude_patterns', [])

        elements = await page.query_selector_all(selector)

        for elem in elements[:self.max_items]:
            try:
                # 如果 title_selector 为空，使用元素本身
                if title_s:
                    title_elem = await elem.query_selector(title_s)
                else:
                    title_elem = elem

                # 如果 link_selector 为空，使用元素本身
                if link_s:
                    link_elem = await elem.query_selector(link_s)
                else:
                    link_elem = elem

                if title_elem and link_elem:
                    title = await title_elem.inner_text()
                    link = await link_elem.get_attribute('href')

                    if title and link:
                        if not link.startswith('http'):
                            link = urljoin(self.base_url, link)

                        # URL过滤：排除广告、导航等无效链接
                        if exclude_patterns and any(pattern in link for pattern in exclude_patterns):
                            logger.debug(f"排除无效链接: {link}")
                            continue

                        items.append({
                            'title': title.strip(),
                            'url': link
                        })
            except Exception as e:
                logger.debug(f"解析列表项失败: {e}")
                continue

        return items

    async def _crawl_article_async(self, page, url: str, title: str) -> Optional[NewsArticle]:
        """异步爬取单篇文章"""
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(2000)

            # 提取内容
            summary, content = await self._extract_content_async(page)

            return self._create_article(
                title=title,
                url=url,
                summary=summary,
                content=content
            )
        except Exception as e:
            logger.debug(f"提取文章内容失败: {url}, 错误: {e}")
            return None

    async def _extract_content_async(self, page) -> tuple:
        """异步提取文章内容"""
        content = ""
        summary = ""

        # 尝试多种选择器
        selectors = [
            'article',
            '.article-content',
            '.post-content',
            '.content',
            '#content',
            '.article-body',
            '.article-main',
            '.news-content',
            '.text-content',
        ]

        for selector in selectors:
            try:
                elem = await page.query_selector(selector)
                if elem:
                    # 获取所有段落
                    paragraphs = await elem.query_selector_all('p')
                    if paragraphs:
                        text_parts = []
                        for p in paragraphs:
                            text = await p.inner_text()
                            if text.strip():
                                text_parts.append(text.strip())

                        if text_parts:
                            content = '\n\n'.join(text_parts)
                            summary = text_parts[0][:200] if text_parts else ""
                            break
            except Exception:
                continue

        # 如果没有找到，尝试获取整个页面文本
        if not content:
            try:
                text = await page.inner_text('body')
                if text:
                    # 清理文本
                    lines = text.split('\n')
                    lines = [line.strip() for line in lines if line.strip()]
                    content = '\n'.join(lines)
                    summary = content[:200]
            except Exception:
                pass

        return summary, content

    def _crawl_impl(self) -> List[NewsArticle]:
        """同步调用异步方法"""
        try:
            return asyncio.run(self._crawl_impl_async())
        except KeyboardInterrupt:
            logger.info("用户中断爬取")
            return []
