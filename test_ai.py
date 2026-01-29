#!/usr/bin/env python3
"""
AI 测试脚本 - 从数据库获取文章并生成AI分析报告
无需重新爬取数据

用法:
    python test_ai.py                    # 默认获取昨天文章
    python test_ai.py --date 2026-01-22  # 获取指定日期文章
    python test_ai.py --today            # 获取今天文章
"""
import logging
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.database import db
from src.processors import AIProcessor, Formatter
from src.config import config


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='AI 财经分析测试脚本')
    parser.add_argument('--date', type=str, help='指定日期 (格式: YYYY-MM-DD)')
    parser.add_argument('--today', action='store_true', help='获取今天文章')
    parser.add_argument('--days', type=int, default=1, help='获取最近N天文章 (默认: 1)')
    return parser.parse_args()


def get_target_date(args) -> str:
    """根据参数计算目标日期"""
    if args.date:
        return args.date
    elif args.today:
        return datetime.now().strftime('%Y-%m-%d')
    else:
        # 默认昨天
        yesterday = datetime.now() - timedelta(days=args.days)
        return yesterday.strftime('%Y-%m-%d')


def main():
    args = parse_args()
    target_date = get_target_date(args)

    print("=" * 60)
    print(f"AI 财经分析测试 - {target_date}")
    print("=" * 60)

    # 从数据库获取指定日期文章
    articles = db.get_articles_by_date(target_date)
    print(f"从数据库获取 {len(articles)} 篇文章 ({target_date})")

    if not articles:
        print("数据库中没有该日期的文章，请先运行爬虫")
        return

    # 初始化 AI 处理器
    ai_config = config.get('ai', {})
    ai_processor = AIProcessor(ai_config)

    if not ai_processor.enabled:
        print("AI 功能未启用，请检查 config.yaml 中的 ai 配置")
        return

    # AI 分析
    print("正在进行 AI 深度分析...")
    report_data = ai_processor.process_daily_news(articles)

    if not report_data:
        print("AI 分析失败")
        return

    # 生成 HTML 报告
    formatter = Formatter()
    html = formatter.format_ai_report(report_data)

    # 保存文件
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"ai_{target_date}.html"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print("=" * 60)
    print(f"AI 报告已保存到: {output_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
