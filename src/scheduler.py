"""
定时任务调度器
"""

import logging
import re
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from .config import config
from .database import db
from .spiders import ScrapySpider, RSSSpider, PlaywrightSpider
from .processors import Deduplicator, Formatter, AIProcessor
from .notifiers import NotifierFactory
from .models import NewsArticle, WebsiteConfig, SpiderType, CrawlResult

logger = logging.getLogger(__name__)


class NewsScheduler:
    """新闻爬取调度器"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.deduplicator = Deduplicator()
        self.formatter = Formatter()
        
        # 初始化 AI 处理器
        self.ai_processor = AIProcessor(config.get('ai', {}))
        
        self.notifiers = []
        self._running = False
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """设置信号处理器"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """信号处理"""
        logger.info(f"收到信号 {signum}, 正在停止调度器...")
        self.stop()
        sys.exit(0)

    def _job_listener(self, event):
        """任务执行监听"""
        if event.exception:
            logger.error(f"任务执行失败: {event.job_id}, 错误: {event.exception}")
        else:
            logger.info(f"任务执行成功: {event.job_id}")

    def add_daily_task(self, hour: int = 8, minute: int = 0):
        """添加每日任务"""
        trigger = CronTrigger(hour=hour, minute=minute)

        self.scheduler.add_job(
            self.run_daily_crawl,
            trigger=trigger,
            id='daily_crawl',
            name='每日新闻爬取',
            replace_existing=True
        )

        logger.info(f"已添加每日任务: 每天 {hour:02d}:{minute:02d}")

    def run_daily_crawl(self):
        """执行每日爬取"""
        logger.info("=" * 50)
        logger.info(f"开始执行每日爬取: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 50)

        self._running = True
        ai_report_data = None

        try:
            # 1. 获取所有网站配置
            websites = config.get_all_website_list()
            logger.info(f"共有 {len(websites)} 个数据源")

            # 2. 从数据库加载已见的URL
            self._load_seen_urls()

            # 3. 爬取所有网站
            all_articles = self._crawl_all_websites(websites)

            logger.info(f"共爬取 {len(all_articles)} 篇新文章")

            if all_articles:
                # 4. 保存到数据库
                saved_count = db.save_articles(all_articles)
                logger.info(f"保存 {saved_count} 篇文章到数据库")
                
                # 4.5 AI 深度分析
                if self.ai_processor.enabled:
                    logger.info("正在进行 AI 深度分析...")
                    ai_report_data = self.ai_processor.process_daily_news(all_articles)

                # 5. 发送通知 (TODO: 使通知器支持 AI 报告格式，目前暂传原始列表)
                self._send_notifications(all_articles)

            # 6. 保存到本地文件
            self._save_to_file(all_articles, ai_report_data)

            # 7. 记录爬取历史
            self._log_crawl_history()

        except Exception as e:
            logger.error(f"每日爬取出错: {e}", exc_info=True)

        finally:
            self._running = False

        return all_articles

    def _crawl_all_websites(self, websites: List[dict]) -> List[NewsArticle]:
        """爬取所有网站"""
        all_articles = []

        for site_config in websites:
            try:
                # 创建网站配置对象
                website = WebsiteConfig(
                    name=site_config['name'],
                    url=site_config['url'],
                    category=site_config['category'],
                    source_type=site_config['source_type'],
                    type=site_config.get('type', SpiderType.SCRAPY.value),
                    list_url=site_config.get('list_url'),
                    list_selector=site_config.get('list_selector'),
                    title_selector=site_config.get('title_selector'),
                    link_selector=site_config.get('link_selector'),
                    date_selector=site_config.get('date_selector'),
                    rss_url=site_config.get('rss_url')
                )

                # 根据类型选择爬虫
                spider_type = website.type
                if spider_type == SpiderType.RSS.value:
                    spider = RSSSpider(website)
                elif spider_type == SpiderType.PLAYWRIGHT.value:
                    spider = PlaywrightSpider(website)
                else:
                    spider = ScrapySpider(website)

                # 执行爬取
                articles = spider.crawl()

                # 去重
                articles = self.deduplicator.deduplicate(articles)

                all_articles.extend(articles)

                # 只在获取到文章时输出摘要
                if articles:
                    logger.info(f"[{website.name}] 成功获取 {len(articles)} 篇文章")

                # 记录结果
                result = CrawlResult(
                    source_name=website.name,
                    category=website.category,
                    source_type=website.source_type,
                    success=len(articles) > 0,
                    articles=articles
                )
                db.save_crawl_result(result)

            except Exception as e:
                logger.error(f"爬取 {site_config.get('name')} 失败: {e}")
                continue

        return all_articles

    def _load_seen_urls(self):
        """从数据库加载已见的URL"""
        try:
            articles = db.get_recent_articles(days=30)
            urls = [a.url for a in articles]
            self.deduplicator.load_from_database(urls)
            logger.info(f"已加载 {len(urls)} 个已见URL")
        except Exception as e:
            logger.warning(f"加载已见URL失败: {e}")

    def _send_notifications(self, articles: List[NewsArticle]):
        """发送通知"""
        if not self.notifiers:
            self.notifiers = NotifierFactory.create_all(config.get_notifiers_config())

        for notifier in self.notifiers:
            if notifier.is_available():
                try:
                    result = notifier.send(articles)
                    logger.info(f"{notifier.name} 通知结果: {'成功' if result.success else '失败'}")
                except Exception as e:
                    logger.error(f"{notifier.name} 通知失败: {e}")

    def _log_crawl_history(self):
        """记录爬取历史"""
        stats = db.get_statistics()
        logger.info(f"当前数据库统计: {stats}")

    def _save_to_file(self, articles: List[NewsArticle], ai_report_data: dict = None):
        """保存爬取结果到本地HTML文件"""
        try:
            # 如果没有新文章，从数据库获取最近的
            if not articles:
                articles = db.get_recent_articles(days=1)
                # 如果有文章，尝试重新生成 AI 报告（可选，这里为了简化暂不重发 LLM 请求）
                # 如果需要重跑 AI，可以在这里调用，但通常 AI 调用昂贵，还是只针对新文章
                if not articles:
                    logger.info("没有文章可保存")
                    return

            # 创建输出目录
            output_dir = Path("outputs")
            output_dir.mkdir(exist_ok=True)

            # 生成文件名
            date_str = datetime.now().strftime('%Y-%m-%d')
            output_file = output_dir / f"news_{date_str}.html"

            # 使用 Formatter 生成 HTML
            if ai_report_data:
                logger.info("生成合并版 HTML 报告（标准列表 + AI分析）")
                html = self.formatter.format_combined_report(articles, ai_report_data)
            else:
                logger.info("生成标准版 HTML 报告")
                subject, html = self.formatter.format_for_email(articles)

            # 保存文件
            output_file.write_text(html, encoding='utf-8')
            logger.info(f"已保存HTML到: {output_file}")

            # 生成归档页
            self._generate_archive_page(output_dir)

        except Exception as e:
            logger.error(f"保存文件失败: {e}")

    def _generate_archive_page(self, output_dir: Path):
        """扫描 outputs 目录生成归档页面"""
        try:
            import re

            reports = []
            # 扫描所有 news_*.html 文件
            for html_file in sorted(output_dir.glob("news_*.html"), reverse=True):
                try:
                    # 从文件名提取日期: news_2026-01-22.html -> 2026-01-22
                    date_str = html_file.stem  # news_2026-01-22
                    date = date_str.replace("news_", "")

                    # 解析 HTML 文件获取标题
                    content = html_file.read_text(encoding='utf-8')

                    # 提取标题 (优先取 h1)
                    title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', content, re.IGNORECASE)
                    if title_match:
                        title = title_match.group(1).strip()
                    else:
                        title = f"{date} 金融资讯"

                    # 提取摘要（取第一段 article 摘要）
                    summary_match = re.search(r'<div class="summary"[^>]*>([^<]+)</div>', content)
                    summary = summary_match.group(1).strip() if summary_match else ""

                    reports.append({
                        'date': date,
                        'title': title,
                        'url': html_file.name,
                        'summary': summary
                    })
                except Exception as e:
                    logger.warning(f"解析 {html_file.name} 失败: {e}")
                    continue

            if reports:
                archive_html = self.formatter.format_archive_page(reports)
                archive_file = output_dir / "archive.html"
                archive_file.write_text(archive_html, encoding='utf-8')
                logger.info(f"已生成归档页: {archive_file} ({len(reports)} 期)")

        except Exception as e:
            logger.error(f"生成归档页失败: {e}")

    def start(self, hour: int = 8, minute: int = 0):
        """启动调度器"""
        # 添加每日任务
        self.add_daily_task(hour=hour, minute=minute)

        # 添加任务监听
        self.scheduler.add_listener(
            self._job_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )

        # 启动调度器
        self.scheduler.start()
        logger.info("调度器已启动")

        # 立即执行一次
        logger.info("立即执行一次爬取...")
        self.run_daily_crawl()

    def stop(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("调度器已停止")

    def run_once(self):
        """执行一次爬取（不启动调度器）"""
        return self.run_daily_crawl()

    def get_status(self) -> dict:
        """获取状态"""
        return {
            'running': self._running,
            'scheduled_jobs': len(self.scheduler.get_jobs()),
            'notifiers_count': len(self.notifiers),
            'database_stats': db.get_statistics()
        }
