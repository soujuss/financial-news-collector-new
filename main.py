#!/usr/bin/env python3
"""
金融资讯定时爬取系统 - 主入口
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import config
from src.scheduler import NewsScheduler
from src.database import db
from src.processors import Formatter


def setup_logging():
    """设置日志"""
    log_config = config.get_logging_config()

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, log_config.get('level', 'INFO')),
        format=log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_config.get('file', 'logs/news_collector.log'), encoding='utf-8')
        ]
    )


def cmd_test(args):
    """测试模式"""
    from src.spiders import ScrapySpider, PlaywrightSpider, RSSSpider
    from src.models import WebsiteConfig, SpiderType

    print("=" * 60)
    print("测试模式 - 爬取单个网站")
    print("=" * 60)

    # 测试爬取
    if args.source:
        websites = config.get_all_website_list()
        targets = []

        for w in websites:
            # 匹配网站名称或分类
            if args.source.lower() in w['name'].lower() or \
               w['category'].lower() == args.source.lower():
                targets.append(w)

        if targets:
            # 取第一个匹配
            target = targets[0]
            print(f"找到 {len(targets)} 个匹配，使用: {target['name']}")
            website = WebsiteConfig(
                name=target['name'],
                url=target['url'],
                category=target['category'],
                source_type=target['source_type'],
                type=target.get('type', SpiderType.SCRAPY.value),
                list_url=target.get('list_url'),
                list_selector=target.get('list_selector'),
                title_selector=target.get('title_selector'),
                link_selector=target.get('link_selector'),
                date_selector=target.get('date_selector'),
                rss_url=target.get('rss_url'),
                encoding=target.get('encoding'),
                use_stealth=target.get('use_stealth', False),
                proxy_url=target.get('proxy_url'),
                wait_time=target.get('wait_time', 2),
                headless=target.get('headless', True)
            )

            # 根据类型选择爬虫
            spider_type = website.type
            if spider_type == SpiderType.PLAYWRIGHT.value:
                print(f"使用 Playwright 爬虫")
                spider = PlaywrightSpider(website)
            elif spider_type == SpiderType.RSS.value:
                print(f"使用 RSS 爬虫")
                spider = RSSSpider(website)
            else:
                print(f"使用 Scrapy 爬虫")
                spider = ScrapySpider(website)

            articles = spider.crawl()

            print(f"\n爬取结果:")
            print(f"  来源: {target['name']}")
            print(f"  数量: {len(articles)}")

            for i, article in enumerate(articles[:5], 1):
                print(f"  {i}. {article.title}")
                print(f"     URL: {article.url}")
                if article.summary:
                    print(f"     摘要: {article.summary[:100]}...")
        else:
            print(f"未找到网站: {args.source}")
            print(f"可用的分类: insurance, banks, finance, regulation, internet_finance")
    else:
        print("请指定测试来源: --source <分类或网站名>")


def cmd_run_once(args):
    """单次运行"""
    print("=" * 60)
    print("单次运行模式")
    print("=" * 60)

    scheduler = NewsScheduler()
    articles = scheduler.run_once()

    print(f"\n完成! 共获取 {len(articles)} 篇新文章")

    # 显示今日统计
    stats = db.get_statistics()
    print(f"数据库统计: 今日 {stats['today_count']} 篇, 总计 {stats['total_count']} 篇")


def cmd_daemon(args):
    """守护进程模式"""
    print("=" * 60)
    print("守护进程模式 - 启动定时调度")
    print("=" * 60)

    hour = args.hour or config.get_scheduler_config().get('hour', 8)
    minute = args.minute or config.get_scheduler_config().get('minute', 0)

    print(f"定时任务: 每天 {hour:02d}:{minute:02d}")

    scheduler = NewsScheduler()
    scheduler.start(hour=hour, minute=minute)

    print("\n调度器运行中, 按 Ctrl+C 停止")

    try:
        # 保持运行
        import time
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n正在停止...")
        scheduler.stop()


def cmd_status(args):
    """查看状态"""
    scheduler = NewsScheduler()
    status = scheduler.get_status()

    print("=" * 60)
    print("系统状态")
    print("=" * 60)

    print(f"运行状态: {'运行中' if status['running'] else '空闲'}")
    print(f"定时任务数: {status['scheduled_jobs']}")
    print(f"通知器数量: {status['notifiers_count']}")

    stats = status['database_stats']
    print(f"\n数据库统计:")
    print(f"  总文章数: {stats['total_count']}")
    print(f"  今日新增: {stats['today_count']}")
    print(f"  待推送: {stats['pending_count']}")

    print(f"\n各分类统计:")
    for category, count in stats['category_counts'].items():
        print(f"  {category}: {count} 篇")


def cmd_report(args):
    """生成报告"""
    print("=" * 60)
    print("资讯报告")
    print("=" * 60)

    days = args.days or 1
    articles = db.get_recent_articles(days=days)

    if not articles:
        print(f"最近 {days} 天没有资讯")
        return

    formatter = Formatter()
    report = formatter.format_daily_report(articles)

    print(report)


def cmd_notify(args):
    """手动发送通知"""
    print("=" * 60)
    print("手动发送通知")
    print("=" * 60)

    days = args.days or 1
    articles = db.get_articles_for_push(days=days)

    if not articles:
        print(f"没有待推送的文章")
        return

    print(f"准备推送 {len(articles)} 篇文章")

    from src.notifiers import NotifierFactory
    notifiers = NotifierFactory.create_all(config.get_notifiers_config())

    for notifier in notifiers:
        if notifier.is_available():
            print(f"\n通过 {notifier.name} 发送...")
            result = notifier.send(articles)
            print(f"  结果: {'成功' if result.success else '失败'}")
            if result.error_message:
                print(f"  错误: {result.error_message}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='金融资讯定时爬取系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py --test --source insurance     # 测试爬取保险资讯
  python main.py --run-once                    # 单次执行爬取
  python main.py --daemon                      # 启动定时守护进程
  python main.py --status                      # 查看系统状态
  python main.py --report                      # 生成今日报告
  python main.py --notify                      # 手动发送通知
        """
    )

    parser.add_argument('--config', '-c', default='config/config.yaml',
                        help='配置文件路径')

    subparsers = parser.add_subparsers(dest='command', help='命令')

    # 测试命令
    test_parser = subparsers.add_parser('test', help='测试模式')
    test_parser.add_argument('--source', '-s', help='指定测试来源(分类或网站名)')

    # 单次运行命令
    subparsers.add_parser('run-once', help='单次执行爬取')

    # 守护进程命令
    daemon_parser = subparsers.add_parser('daemon', help='启动定时守护进程')
    daemon_parser.add_argument('--hour', type=int, help='定时小时(0-23)')
    daemon_parser.add_argument('--minute', type=int, help='定时分钟(0-59)')

    # 状态命令
    subparsers.add_parser('status', help='查看系统状态')

    # 报告命令
    report_parser = subparsers.add_parser('report', help='生成资讯报告')
    report_parser.add_argument('--days', type=int, default=1, help='最近天数(默认1)')

    # 通知命令
    notify_parser = subparsers.add_parser('notify', help='手动发送通知')
    notify_parser.add_argument('--days', type=int, default=1, help='最近天数(默认1)')

    args = parser.parse_args()

    # 设置日志
    setup_logging()

    logger = logging.getLogger(__name__)

    if args.command == 'test':
        cmd_test(args)
    elif args.command == 'run-once':
        cmd_run_once(args)
    elif args.command == 'daemon':
        cmd_daemon(args)
    elif args.command == 'status':
        cmd_status(args)
    elif args.command == 'report':
        cmd_report(args)
    elif args.command == 'notify':
        cmd_notify(args)
    else:
        # 默认单次运行
        cmd_run_once(args)


if __name__ == '__main__':
    main()
