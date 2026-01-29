"""
数据库操作模块
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path

from .config import config
from .models import NewsArticle, CrawlResult

logger = logging.getLogger(__name__)


class Database:
    """数据库管理类"""

    _instance: Optional['Database'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    @classmethod
    def get_instance(cls) -> 'Database':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        db_config = config.get_database_config()
        db_path = db_config.get('path', 'data/news.db')
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()
        self._initialized = True

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        return sqlite3.connect(str(self.db_path))

    def _init_db(self):
        """初始化数据库表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 新闻表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS news_articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    source TEXT NOT NULL,
                    category TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    publish_time DATETIME,
                    summary TEXT,
                    content TEXT,
                    crawled_time DATETIME NOT NULL,
                    is_push BOOLEAN DEFAULT 0,
                    push_time DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 爬取历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS crawl_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    articles_count INTEGER DEFAULT 0,
                    error_message TEXT,
                    crawl_time DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 推送历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS push_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    article_count INTEGER DEFAULT 0,
                    error_message TEXT,
                    push_time DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_url ON news_articles(url)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_category ON news_articles(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_crawled_time ON news_articles(crawled_time)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_is_push ON news_articles(is_push)')

            conn.commit()
            logger.info("数据库初始化完成")

    def save_articles(self, articles: List[NewsArticle]) -> int:
        """保存文章，返回成功保存的数量"""
        saved_count = 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for article in articles:
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO news_articles
                        (title, url, source, category, source_type, publish_time, summary, content, crawled_time)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        article.title,
                        article.url,
                        article.source,
                        article.category,
                        article.source_type,
                        article.publish_time,
                        article.summary,
                        article.content,
                        article.crawled_time
                    ))
                    if cursor.rowcount > 0:
                        saved_count += 1
                except Exception as e:
                    logger.error(f"保存文章失败: {article.url}, 错误: {e}")
            conn.commit()
        return saved_count

    def save_crawl_result(self, result: CrawlResult):
        """保存爬取结果"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO crawl_history
                (source_name, category, source_type, success, articles_count, error_message, crawl_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.source_name,
                result.category,
                result.source_type,
                result.success,
                len(result.articles),
                result.error_message,
                result.crawl_time
            ))
            conn.commit()

    def get_articles_for_push(self, days: int = 1, limit: int = 100) -> List[NewsArticle]:
        """获取待推送的文章"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM news_articles
                WHERE is_push = 0
                AND crawled_time >= ?
                ORDER BY crawled_time DESC
                LIMIT ?
            ''', (datetime.now() - timedelta(days=days), limit))

            rows = cursor.fetchall()
            return [self._row_to_article(row) for row in rows]

    def mark_articles_pushed(self, article_ids: List[int]):
        """标记文章已推送"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ','.join('?' * len(article_ids))
            cursor.execute(f'''
                UPDATE news_articles
                SET is_push = 1, push_time = ?
                WHERE id IN ({placeholders})
            ''', [datetime.now()] + article_ids)
            conn.commit()

    def is_url_exists(self, url: str) -> bool:
        """检查URL是否存在"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM news_articles WHERE url = ?', (url,))
            return cursor.fetchone() is not None

    def get_recent_articles(self, category: str = None, days: int = 7, limit: int = 50) -> List[NewsArticle]:
        """获取最近的文章"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute('''
                    SELECT * FROM news_articles
                    WHERE category = ? AND crawled_time >= ?
                    ORDER BY crawled_time DESC
                    LIMIT ?
                ''', (category, datetime.now() - timedelta(days=days), limit))
            else:
                cursor.execute('''
                    SELECT * FROM news_articles
                    WHERE crawled_time >= ?
                    ORDER BY crawled_time DESC
                    LIMIT ?
                ''', (datetime.now() - timedelta(days=days), limit))

            rows = cursor.fetchall()
            return [self._row_to_article(row) for row in rows]

    def get_articles_by_date(self, date: str, limit: int = 100) -> List[NewsArticle]:
        """获取指定日期的文章

        Args:
            date: 日期字符串，格式 YYYY-MM-DD
            limit: 最大返回数量，默认100

        Returns:
            文章列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 使用 date() 函数比较日期部分
            cursor.execute('''
                SELECT * FROM news_articles
                WHERE date(crawled_time) = ?
                ORDER BY crawled_time DESC
                LIMIT ?
            ''', (date, limit))

            rows = cursor.fetchall()
            return [self._row_to_article(row) for row in rows]

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 总文章数
            cursor.execute('SELECT COUNT(*) FROM news_articles')
            total_count = cursor.fetchone()[0]

            # 今日文章数
            cursor.execute('SELECT COUNT(*) FROM news_articles WHERE date(crawled_time) = date(?)',
                          (datetime.now().strftime('%Y-%m-%d'),))
            today_count = cursor.fetchone()[0]

            # 各分类文章数
            cursor.execute('SELECT category, COUNT(*) FROM news_articles GROUP BY category')
            category_counts = dict(cursor.fetchall())

            # 待推送文章数
            cursor.execute('SELECT COUNT(*) FROM news_articles WHERE is_push = 0')
            pending_count = cursor.fetchone()[0]

            return {
                'total_count': total_count,
                'today_count': today_count,
                'category_counts': category_counts,
                'pending_count': pending_count
            }

    def _row_to_article(self, row) -> NewsArticle:
        """将数据库行转换为NewsArticle对象"""
        return NewsArticle(
            id=row[0],
            title=row[1],
            url=row[2],
            source=row[3],
            category=row[4],
            source_type=row[5],
            publish_time=datetime.fromisoformat(row[6]) if row[6] else None,
            summary=row[7],
            content=row[8],
            crawled_time=datetime.fromisoformat(row[9]) if row[9] else datetime.now(),
            is_push=bool(row[10]),
            push_time=datetime.fromisoformat(row[11]) if row[11] else None
        )

    def clear_old_data(self, days: int = 30):
        """清理旧数据"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM news_articles WHERE crawled_time < ?',
                          (datetime.now() - timedelta(days=days),))
            deleted_count = cursor.rowcount
            conn.commit()
            logger.info(f"清理了 {deleted_count} 条{days}天前的数据")
            return deleted_count


# 全局数据库实例
db = Database.get_instance()
