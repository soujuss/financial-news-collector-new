"""
内容格式化器
"""
import logging
import os
from datetime import datetime
from typing import List, Dict, Any
from ..models import NewsArticle

logger = logging.getLogger(__name__)

class Formatter:
    """内容格式化器"""

    # 分类显示名称映射
    CATEGORY_NAMES = {
        'insurance': '保险行业',
        'banks': '银行行业',
        'finance': '财经资讯',
        'regulation': '政策法规',
        'internet_finance': '互联网金融',
        'market': '市场动态'
    }

    def __init__(self):
        pass

    def format_for_email(self, articles: List[NewsArticle], date: datetime = None) -> tuple:
        """
        格式化为邮件格式 (标准 HTML)

        Returns:
            tuple: (subject, html_body)
        """
        if not articles:
            return "金融资讯日报", "<p>今日暂无资讯</p>"

        if date is None:
            date = datetime.now()

        subject = f"金融资讯日报 - {date.strftime('%Y年%m月%d日')}"

        # 按分类组织文章
        categorized = self._categorize_articles(articles)

        # 生成HTML
        html = self._generate_html(categorized, date)

        return subject, html

    def format_ai_report(self, ai_data: Dict[str, Any], date: datetime = None) -> str:
        """
        将 AI 分析结果格式化为现代化的 HTML 研报
        """
        if date is None:
            date = datetime.now()

        return self._generate_ai_html_template(ai_data, date)

    def format_combined_report(self, articles: List[NewsArticle], ai_data: Dict[str, Any] = None, date: datetime = None) -> str:
        """
        生成合并版 HTML 报告（标准列表 + AI分析），使用 Tab 切换

        Returns:
            str: 合并后的完整HTML
        """
        if date is None:
            date = datetime.now()

        # 生成 AI 分析部分 HTML
        ai_sections_html = self._generate_ai_sections(ai_data) if ai_data else ""

        # 生成文章列表部分 HTML
        categorized = self._categorize_articles(articles)
        articles_html = self._generate_articles_section(categorized, date)

        # 生成完整合并版 HTML
        return self._generate_combined_html(ai_sections_html, articles_html, len(articles), date)

    def _generate_ai_sections(self, data: Dict[str, Any]) -> str:
        """提取 AI 分析的各个部分（市场综述、深度专题、资讯速递）"""
        if not data:
            return ""

        # 1. 市场综述
        sentiment_html = ""
        if "market_sentiment" in data:
            sentiment_html = f"""
            <div class="sentiment-box glass-effect">
                <div class="box-header"><span class="icon">📈</span> 市场情绪与宏观综述</div>
                <div class="box-content">{data['market_sentiment']}</div>
            </div>
            """

        # 2. 深度专题
        themes_html = ""
        if "themes" in data:
            theme_cards = ""
            for theme in data["themes"]:
                imp = theme.get("importance", "中")
                importance_class = "imp-high" if imp == "高" else "imp-med"

                # 关联文章链接
                articles_links = ""
                if "articles" in theme:
                    links = []
                    for art in theme["articles"]:
                        source = art.source or "未知来源"
                        links.append(f'<a href="{art.url}" target="_blank" class="source-tag">{source}</a>')
                    if links:
                        articles_links = f'<div class="ref-links"><span class="ref-label">相关报道:</span> {"".join(links)}</div>'

                theme_cards += f"""
                <div class="theme-card">
                    <div class="theme-header">
                        <div class="theme-title-wrapper">
                            <span class="theme-title">{theme.get('title')}</span>
                        </div>
                        <span class="importance {importance_class}">{imp}关注</span>
                    </div>
                    <div class="theme-body">
                        <div class="summary-section">
                            {theme.get('summary')}
                        </div>
                        <div class="insight-section">
                            <div class="insight-label">💡 研究员洞察</div>
                            <div class="insight-text">{theme.get('insight')}</div>
                        </div>
                        {articles_links}
                    </div>
                </div>
                """

            themes_html = f"""
            <div class="section-container">
                <div class="section-header">
                    <span class="section-icon">🧐</span> 深度专题
                </div>
                <div class="themes-grid">
                    {theme_cards}
                </div>
            </div>
            """

        # 3. 资讯速递
        flash_html = ""
        if "news_flash" in data:
            flash_items = ""
            for item in data["news_flash"]:
                article_info = ""
                if "article" in item:
                    art = item["article"]
                    article_info = f'<a href="{art.url}" target="_blank" class="flash-source">{art.source} ↗</a>'

                flash_items += f"""
                <div class="flash-item">
                    <div class="flash-content">
                        <div class="flash-title">
                            {item.get('title')} {article_info}
                        </div>
                        <div class="flash-comment">
                           <span class="comment-icon">👉</span> {item.get('one_sentence_comment')}
                        </div>
                    </div>
                </div>
                """

            flash_html = f"""
            <div class="section-container">
                <div class="section-header">
                    <span class="section-icon">⚡</span> 资讯速递
                </div>
                <div class="flash-grid">
                    {flash_items}
                </div>
            </div>
            """

        return sentiment_html + themes_html + flash_html

    def _generate_articles_section(self, categorized_articles: Dict[str, List[NewsArticle]], date: datetime) -> str:
        """生成文章列表部分的 HTML"""
        sections_html = ""

        # 排序：优先显示配置中定义的分类
        sorted_keys = sorted(categorized_articles.keys(),
                           key=lambda x: list(self.CATEGORY_NAMES.keys()).index(x) if x in self.CATEGORY_NAMES else 999)

        for category in sorted_keys:
            articles = categorized_articles[category]
            cat_name = self.CATEGORY_NAMES.get(category, category.upper())

            rows = ""
            for i, art in enumerate(articles, 1):
                rows += f"""
                <div class="article-item">
                    <h3>{i}. <a href="{art.url}" target="_blank">{art.title}</a></h3>
                    <div class="meta">
                        <span class="source">{art.source}</span>
                        <span class="time">{art.publish_time.strftime('%H:%M') if art.publish_time else ''}</span>
                    </div>
                    <p class="summary">{art.summary or '暂无摘要'}</p>
                </div>
                """

            sections_html += f"""
            <div class="category-section">
                <h2>{cat_name} ({len(articles)})</h2>
                {rows}
            </div>
            """

        return sections_html

    def _generate_combined_html(self, ai_html: str, articles_html: str, article_count: int, date: datetime) -> str:
        """生成完整的合并版 HTML 页面"""
        date_str = date.strftime('%Y年%m月%d日')

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>金融早报 | 合并报告 - {date_str}</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Sans+SC:wght@300;400;500;700&display=swap" rel="stylesheet">
            <style>
                :root {{
                    --primary: #2563eb;
                    --primary-dark: #1e40af;
                    --secondary: #64748b;
                    --accent: #f59e0b;
                    --success: #10b981;
                    --danger: #ef4444;
                    --bg-page: #f8fafc;
                    --bg-card: #ffffff;
                    --text-main: #1e293b;
                    --text-muted: #64748b;
                    --border-color: #e2e8f0;
                    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
                    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
                }}

                body {{
                    font-family: 'Inter', 'Noto Sans SC', sans-serif;
                    line-height: 1.6;
                    color: var(--text-main);
                    background-color: var(--bg-page);
                    margin: 0;
                    padding: 0;
                    -webkit-font-smoothing: antialiased;
                }}

                .main-container {{
                    max-width: 900px;
                    margin: 0 auto;
                    padding: 40px 20px;
                }}

                /* Header */
                .report-header {{
                    text-align: center;
                    margin-bottom: 40px;
                }}
                .report-title {{
                    font-size: 32px;
                    font-weight: 800;
                    color: #0f172a;
                    letter-spacing: -0.025em;
                    margin: 0;
                    display: inline-block;
                    position: relative;
                }}
                .report-title::after {{
                    content: '';
                    display: block;
                    width: 60px;
                    height: 4px;
                    background: var(--primary);
                    margin: 15px auto 0;
                    border-radius: 2px;
                }}
                .report-subtitle {{
                    font-size: 16px;
                    color: var(--text-muted);
                    font-weight: 500;
                    margin-top: 10px;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                }}

                /* Tab Navigation */
                .tab-nav {{
                    display: flex;
                    gap: 8px;
                    margin-bottom: 40px;
                    border-bottom: 2px solid var(--border-color);
                    padding-bottom: 0;
                }}
                .tab-btn {{
                    padding: 14px 28px;
                    border: none;
                    background: transparent;
                    font-size: 15px;
                    font-weight: 600;
                    color: var(--text-muted);
                    cursor: pointer;
                    position: relative;
                    transition: color 0.3s;
                    border-radius: 8px 8px 0 0;
                }}
                .tab-btn:hover {{
                    color: var(--primary);
                    background: rgba(37, 99, 235, 0.05);
                }}
                .tab-btn.active {{
                    color: var(--primary);
                }}
                .tab-btn.active::after {{
                    content: '';
                    position: absolute;
                    bottom: -2px;
                    left: 0;
                    right: 0;
                    height: 3px;
                    background: var(--primary);
                    border-radius: 3px 3px 0 0;
                }}
                .tab-count {{
                    font-size: 12px;
                    background: var(--border-color);
                    padding: 2px 8px;
                    border-radius: 12px;
                    margin-left: 8px;
                    color: var(--text-muted);
                }}

                /* Tab Content */
                .tab-content {{
                    min-height: 400px;
                }}
                .tab-pane {{
                    display: none;
                    animation: fadeIn 0.4s ease;
                }}
                .tab-pane.active {{
                    display: block;
                }}
                @keyframes fadeIn {{
                    from {{ opacity: 0; transform: translateY(15px); }}
                    to {{ opacity: 1; transform: translateY(0); }}
                }}

                /* AI Section Styles (reused from AI template) */
                .sentiment-box {{
                    background: linear-gradient(135deg, #ffffff 0%, #eff6ff 100%);
                    border: 1px solid #dbeafe;
                    border-radius: 16px;
                    padding: 24px;
                    margin-bottom: 50px;
                    box-shadow: var(--shadow-md);
                    position: relative;
                    overflow: hidden;
                }}
                .sentiment-box::before {{
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 4px;
                    height: 100%;
                    background: var(--primary);
                }}
                .box-header {{
                    font-size: 18px;
                    font-weight: 700;
                    color: #1e3a8a;
                    margin-bottom: 15px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }}
                .box-content {{
                    font-size: 16px;
                    color: #334155;
                    font-weight: 400;
                    text-align: justify;
                    line-height: 1.7;
                }}

                .section-header {{
                    font-size: 24px;
                    font-weight: 700;
                    color: #0f172a;
                    margin-bottom: 25px;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    border-bottom: 2px solid var(--border-color);
                    padding-bottom: 10px;
                }}
                .section-icon {{
                    font-size: 24px;
                }}

                .themes-grid {{
                    display: grid;
                    gap: 25px;
                    margin-bottom: 50px;
                }}
                .theme-card {{
                    background: var(--bg-card);
                    border-radius: 12px;
                    padding: 24px;
                    box-shadow: var(--shadow-sm);
                    border: 1px solid var(--border-color);
                    transition: all 0.3s ease;
                }}
                .theme-card:hover {{
                    box-shadow: var(--shadow-lg);
                    transform: translateY(-2px);
                    border-color: #cbd5e1;
                }}
                .theme-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    margin-bottom: 18px;
                    gap: 15px;
                }}
                .theme-title {{
                    font-size: 20px;
                    font-weight: 700;
                    color: #0f172a;
                    line-height: 1.3;
                }}
                .importance {{
                    font-size: 12px;
                    padding: 4px 10px;
                    border-radius: 20px;
                    font-weight: 600;
                    white-space: nowrap;
                    text-transform: uppercase;
                    letter-spacing: 0.02em;
                }}
                .imp-high {{ background-color: #fee2e2; color: #b91c1c; }}
                .imp-med {{ background-color: #fef3c7; color: #b45309; }}

                .summary-section {{
                    font-size: 15px;
                    color: #475569;
                    margin-bottom: 15px;
                    line-height: 1.6;
                }}
                .insight-section {{
                    background-color: #f0fdf4;
                    border-left: 3px solid #10b981;
                    padding: 15px;
                    border-radius: 0 8px 8px 0;
                    margin-bottom: 15px;
                }}
                .insight-label {{
                    font-size: 13px;
                    font-weight: 700;
                    color: #047857;
                    margin-bottom: 5px;
                    text-transform: uppercase;
                }}
                .insight-text {{
                    font-size: 15px;
                    color: #065f46;
                }}

                .ref-links {{
                    margin-top: 15px;
                    padding-top: 15px;
                    border-top: 1px dashed var(--border-color);
                    display: flex;
                    flex-wrap: wrap;
                    gap: 8px;
                    align-items: center;
                }}
                .ref-label {{
                    font-size: 12px;
                    color: #94a3b8;
                    font-weight: 600;
                }}
                .source-tag {{
                    font-size: 11px;
                    color: #475569;
                    background: #f1f5f9;
                    padding: 2px 8px;
                    border-radius: 4px;
                    text-decoration: none;
                    transition: background 0.2s;
                }}
                .source-tag:hover {{
                    background: #e2e8f0;
                    color: var(--primary);
                }}

                .flash-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                }}
                .flash-item {{
                    background: var(--bg-card);
                    border: 1px solid var(--border-color);
                    border-radius: 10px;
                    padding: 18px;
                    transition: transform 0.2s;
                }}
                .flash-item:hover {{
                    border-color: #cbd5e1;
                    box-shadow: var(--shadow-md);
                }}
                .flash-title {{
                    font-size: 15px;
                    font-weight: 600;
                    color: #0f172a;
                    margin-bottom: 10px;
                    line-height: 1.4;
                }}
                .flash-source {{
                    font-size: 11px;
                    color: #94a3b8;
                    font-weight: 400;
                    margin-left: 5px;
                    text-decoration: none;
                }}
                .flash-source:hover {{ color: var(--primary); }}
                .flash-comment {{
                    font-size: 13px;
                    color: #b45309;
                    background-color: #fffbeb;
                    padding: 8px 12px;
                    border-radius: 6px;
                    margin-top: 8px;
                    display: flex;
                    align-items: flex-start;
                    gap: 8px;
                }}
                .comment-icon {{
                    flex-shrink: 0;
                }}

                /* Articles List Styles */
                .category-section {{
                    margin-bottom: 35px;
                }}
                .category-section h2 {{
                    color: #34495e;
                    border-left: 5px solid #3498db;
                    padding-left: 12px;
                    margin-bottom: 18px;
                    font-size: 20px;
                }}
                .article-item {{
                    margin-bottom: 18px;
                    padding-bottom: 18px;
                    border-bottom: 1px solid #eee;
                }}
                .article-item h3 {{
                    margin-bottom: 6px;
                    font-size: 16px;
                    font-weight: 600;
                }}
                .article-item a {{
                    color: #2980b9;
                    text-decoration: none;
                }}
                .article-item a:hover {{
                    text-decoration: underline;
                }}
                .meta {{
                    font-size: 12px;
                    color: #7f8c8d;
                    margin-bottom: 6px;
                }}
                .meta .source {{
                    margin-right: 12px;
                }}
                .summary {{
                    font-size: 14px;
                    color: #555;
                    margin: 0;
                    line-height: 1.6;
                }}

                /* Footer */
                .footer {{
                    text-align: center;
                    color: #94a3b8;
                    font-size: 12px;
                    margin-top: 60px;
                    padding-bottom: 30px;
                    border-top: 1px solid var(--border-color);
                    padding-top: 20px;
                }}

                @media (max-width: 600px) {{
                    .flash-grid {{
                        grid-template-columns: 1fr;
                    }}
                    .main-container {{
                        padding: 20px 15px;
                    }}
                    .report-title {{
                        font-size: 24px;
                    }}
                    .tab-btn {{
                        padding: 12px 16px;
                        font-size: 14px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="main-container">
                <div class="report-header">
                    <h1 class="report-title">金融早报</h1>
                    <div class="report-subtitle">合并报告 · {date_str}</div>
                </div>

                <!-- Tab Navigation -->
                <div class="tab-nav">
                    <button class="tab-btn active" data-tab="ai-analysis">AI 深度分析</button>
                    <button class="tab-btn" data-tab="all-articles">全部资讯 <span class="tab-count">{article_count}</span></button>
                </div>

                <!-- Tab Content -->
                <div class="tab-content">
                    <!-- Tab 1: AI Analysis -->
                    <div id="ai-analysis" class="tab-pane active">
                        {ai_html if ai_html else '<p style="color: var(--text-muted); text-align: center; padding: 40px;">暂无 AI 分析数据</p>'}
                    </div>

                    <!-- Tab 2: All Articles -->
                    <div id="all-articles" class="tab-pane">
                        {articles_html}
                    </div>
                </div>

                <div class="footer">
                    Generated by Financial News Collector • AI 分析由 MiniMax M2.1 提供
                </div>
            </div>

            <script>
                // Tab switching logic
                document.querySelectorAll('.tab-btn').forEach(btn => {{
                    btn.addEventListener('click', function() {{
                        // Remove active class from all buttons
                        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                        // Add active class to clicked button
                        this.classList.add('active');

                        // Hide all tab panes
                        document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
                        // Show target tab pane
                        const targetTab = this.getAttribute('data-tab');
                        document.getElementById(targetTab).classList.add('active');
                    }});
                }});

                // Check URL hash for initial tab
                if (window.location.hash === '#articles') {{
                    document.querySelector('[data-tab="all-articles"]').click();
                }}
            </script>
        </body>
        </html>
        """

    def format_for_telegram(self, articles: List[NewsArticle], date: datetime = None) -> str:
        """
        格式化为 Telegram 消息 (HTML)
        """
        import html
        
        if not articles:
            return "今日暂无资讯"

        if date is None:
            date = datetime.now()

        date_str = date.strftime('%Y-%m-%d')
        content = f"<b>{date_str} 金融资讯日报</b>\n\n"

        # 按分类
        categorized = self._categorize_articles(articles)
        
        # 排序
        sorted_keys = sorted(categorized.keys(), 
                           key=lambda x: list(self.CATEGORY_NAMES.keys()).index(x) if x in self.CATEGORY_NAMES else 999)

        idx = 1
        for category in sorted_keys:
            cat_list = categorized[category]
            cat_name = self.CATEGORY_NAMES.get(category, category.upper())
            
            content += f"<b>{cat_name}</b>\n"
            for art in cat_list:
                # 使用 HTML 格式，必须转义标题中的特殊字符
                safe_title = html.escape(art.title)
                content += f"{idx}. <a href=\"{art.url}\">{safe_title}</a>\n"
                idx += 1
            content += "\n"

        content += f"共 {len(articles)} 篇 | Generated by News Collector"
        return content

    def _categorize_articles(self, articles: List[NewsArticle]) -> Dict[str, List[NewsArticle]]:
        """按分类整理文章"""
        categorized = {}
        for article in articles:
            cat = article.category or 'other'
            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append(article)
        return categorized

    def _generate_html(self, categorized_articles: Dict[str, List[NewsArticle]], date: datetime) -> str:
        """生成标准的基础 HTML 报告"""
        date_str = date.strftime('%Y年%m月%d日')
        
        sections_html = ""
        
        # 排序：优先显示配置中定义的分类
        sorted_keys = sorted(categorized_articles.keys(), 
                           key=lambda x: list(self.CATEGORY_NAMES.keys()).index(x) if x in self.CATEGORY_NAMES else 999)

        for category in sorted_keys:
            articles = categorized_articles[category]
            cat_name = self.CATEGORY_NAMES.get(category, category.upper())
            
            rows = ""
            for i, art in enumerate(articles, 1):
                rows += f"""
                <div class="article-item">
                    <h3>{i}. <a href="{art.url}" target="_blank">{art.title}</a></h3>
                    <div class="meta">
                        <span class="source">{art.source}</span>
                        <span class="time">{art.publish_time.strftime('%H:%M') if art.publish_time else ''}</span>
                    </div>
                    <p class="summary">{art.summary or '暂无摘要'}</p>
                </div>
                """
            
            sections_html += f"""
            <div class="category-section">
                <h2>{cat_name} ({len(articles)})</h2>
                {rows}
            </div>
            """

        template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1 {{ color: #2c3e50; border-bottom: 2px solid #2c3e50; padding-bottom: 10px; }}
                h2 {{ color: #34495e; margin-top: 30px; border-left: 5px solid #3498db; padding-left: 10px; }}
                .article-item {{ margin-bottom: 20px; padding-bottom: 20px; border-bottom: 1px solid #eee; }}
                .article-item h3 {{ margin-bottom: 5px; font-size: 16px; }}
                .article-item a {{ color: #2980b9; text-decoration: none; }}
                .meta {{ font-size: 12px; color: #7f8c8d; margin-bottom: 5px; }}
                .summary {{ font-size: 14px; color: #555; margin: 0; }}
            </style>
        </head>
        <body>
            <h1>金融资讯日报 <small>{date_str}</small></h1>
            {sections_html}
            <footer>
                <p>Generated by Financial News Collector at {datetime.now().strftime('%H:%M:%S')}</p>
            </footer>
        </body>
        </html>
        """
        return template

    def _generate_ai_html_template(self, data: Dict[str, Any], date: datetime) -> str:
        """
        生成 AI 增强版 HTML 报告 (Modern Premium Style)
        """
        date_str = date.strftime('%Y年%m月%d日')
        
        # 1. 市场综述
        sentiment_html = ""
        if "market_sentiment" in data:
            sentiment_html = f"""
            <div class="sentiment-box glass-effect">
                <div class="box-header"><span class="icon">📈</span> 市场情绪与宏观综述</div>
                <div class="box-content">{data['market_sentiment']}</div>
            </div>
            """

        # 2. 深度专题
        themes_html = ""
        if "themes" in data:
            theme_cards = ""
            for theme in data["themes"]:
                imp = theme.get("importance", "中")
                importance_class = "imp-high" if imp == "高" else "imp-med"
                
                # 关联文章链接
                articles_links = ""
                if "articles" in theme:
                    links = []
                    for art in theme["articles"]:
                        source = art.source or "未知来源"
                        links.append(f'<a href="{art.url}" target="_blank" class="source-tag">{source}</a>')
                    if links:
                        articles_links = f'<div class="ref-links"><span class="ref-label">相关报道:</span> {"".join(links)}</div>'
                
                theme_cards += f"""
                <div class="theme-card">
                    <div class="theme-header">
                        <div class="theme-title-wrapper">
                            <span class="theme-title">{theme.get('title')}</span>
                        </div>
                        <span class="importance {importance_class}">{imp}关注</span>
                    </div>
                    <div class="theme-body">
                        <div class="summary-section">
                            {theme.get('summary')}
                        </div>
                        <div class="insight-section">
                            <div class="insight-label">💡 研究员洞察</div>
                            <div class="insight-text">{theme.get('insight')}</div>
                        </div>
                        {articles_links}
                    </div>
                </div>
                """
            
            themes_html = f"""
            <div class="section-container">
                <div class="section-header">
                    <span class="section-icon">🧐</span> 深度专题
                </div>
                <div class="themes-grid">
                    {theme_cards}
                </div>
            </div>
            """

        # 3. 资讯速递
        flash_html = ""
        if "news_flash" in data:
            flash_items = ""
            for item in data["news_flash"]:
                article_info = ""
                if "article" in item:
                    art = item["article"]
                    article_info = f'<a href="{art.url}" target="_blank" class="flash-source">{art.source} ↗</a>'
                
                flash_items += f"""
                <div class="flash-item">
                    <div class="flash-content">
                        <div class="flash-title">
                            {item.get('title')} {article_info}
                        </div>
                        <div class="flash-comment">
                           <span class="comment-icon">👉</span> {item.get('one_sentence_comment')}
                        </div>
                    </div>
                </div>
                """
            
            flash_html = f"""
            <div class="section-container">
                <div class="section-header">
                    <span class="section-icon">⚡</span> 资讯速递
                </div>
                <div class="flash-grid">
                    {flash_items}
                </div>
            </div>
            """

        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>金融早报 | AI 深度版 - {date_str}</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Sans+SC:wght@300;400;500;700&display=swap" rel="stylesheet">
            <style>
                :root {{
                    --primary: #2563eb;
                    --primary-dark: #1e40af;
                    --secondary: #64748b;
                    --accent: #f59e0b;
                    --success: #10b981;
                    --danger: #ef4444;
                    --bg-page: #f8fafc;
                    --bg-card: #ffffff;
                    --text-main: #1e293b;
                    --text-muted: #64748b;
                    --border-color: #e2e8f0;
                    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
                    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
                }}
                
                body {{
                    font-family: 'Inter', 'Noto Sans SC', sans-serif;
                    line-height: 1.6;
                    color: var(--text-main);
                    background-color: var(--bg-page);
                    margin: 0;
                    padding: 0;
                    -webkit-font-smoothing: antialiased;
                }}
                
                .main-container {{
                    max-width: 900px;
                    margin: 0 auto;
                    padding: 40px 20px;
                }}
                
                /* Header */
                .report-header {{
                    text-align: center;
                    margin-bottom: 50px;
                }}
                .report-title {{
                    font-size: 32px;
                    font-weight: 800;
                    color: #0f172a;
                    letter-spacing: -0.025em;
                    margin: 0;
                    display: inline-block;
                    position: relative;
                }}
                .report-title::after {{
                    content: '';
                    display: block;
                    width: 60px;
                    height: 4px;
                    background: var(--primary);
                    margin: 15px auto 0;
                    border-radius: 2px;
                }}
                .report-subtitle {{
                    font-size: 16px;
                    color: var(--text-muted);
                    font-weight: 500;
                    margin-top: 10px;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                }}
                
                /* Sentiment Box */
                .sentiment-box {{
                    background: linear-gradient(135deg, #ffffff 0%, #eff6ff 100%);
                    border: 1px solid #dbeafe;
                    border-radius: 16px;
                    padding: 24px;
                    margin-bottom: 50px;
                    box-shadow: var(--shadow-md);
                    position: relative;
                    overflow: hidden;
                }}
                .sentiment-box::before {{
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 4px;
                    height: 100%;
                    background: var(--primary);
                }}
                .box-header {{
                    font-size: 18px;
                    font-weight: 700;
                    color: #1e3a8a;
                    margin-bottom: 15px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }}
                .box-content {{
                    font-size: 16px;
                    color: #334155;
                    font-weight: 400;
                    text-align: justify;
                    line-height: 1.7;
                }}

                /* Section Headers */
                .section-header {{
                    font-size: 24px;
                    font-weight: 700;
                    color: #0f172a;
                    margin-bottom: 25px;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    border-bottom: 2px solid var(--border-color);
                    padding-bottom: 10px;
                }}
                .section-icon {{
                    font-size: 24px;
                }}
                
                /* Theme Cards */
                .themes-grid {{
                    display: grid;
                    gap: 25px;
                    margin-bottom: 50px;
                }}
                .theme-card {{
                    background: var(--bg-card);
                    border-radius: 12px;
                    padding: 24px;
                    box-shadow: var(--shadow-sm);
                    border: 1px solid var(--border-color);
                    transition: all 0.3s ease;
                }}
                .theme-card:hover {{
                    box-shadow: var(--shadow-lg);
                    transform: translateY(-2px);
                    border-color: #cbd5e1;
                }}
                .theme-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    margin-bottom: 18px;
                    gap: 15px;
                }}
                .theme-title {{
                    font-size: 20px;
                    font-weight: 700;
                    color: #0f172a;
                    line-height: 1.3;
                }}
                .importance {{
                    font-size: 12px;
                    padding: 4px 10px;
                    border-radius: 20px;
                    font-weight: 600;
                    white-space: nowrap;
                    text-transform: uppercase;
                    letter-spacing: 0.02em;
                }}
                .imp-high {{ background-color: #fee2e2; color: #b91c1c; }}
                .imp-med {{ background-color: #fef3c7; color: #b45309; }}
                
                .summary-section {{
                    font-size: 15px;
                    color: #475569;
                    margin-bottom: 15px;
                    line-height: 1.6;
                }}
                .insight-section {{
                    background-color: #f0fdf4;
                    border-left: 3px solid #10b981;
                    padding: 15px;
                    border-radius: 0 8px 8px 0;
                    margin-bottom: 15px;
                }}
                .insight-label {{
                    font-size: 13px;
                    font-weight: 700;
                    color: #047857;
                    margin-bottom: 5px;
                    text-transform: uppercase;
                }}
                .insight-text {{
                    font-size: 15px;
                    color: #065f46;
                }}
                
                .ref-links {{
                    margin-top: 15px;
                    padding-top: 15px;
                    border-top: 1px dashed var(--border-color);
                    display: flex;
                    flex-wrap: wrap;
                    gap: 8px;
                    align-items: center;
                }}
                .ref-label {{
                    font-size: 12px;
                    color: #94a3b8;
                    font-weight: 600;
                }}
                .source-tag {{
                    font-size: 11px;
                    color: #475569;
                    background: #f1f5f9;
                    padding: 2px 8px;
                    border-radius: 4px;
                    text-decoration: none;
                    transition: background 0.2s;
                }}
                .source-tag:hover {{
                    background: #e2e8f0;
                    color: var(--primary);
                }}

                /* News Flash Grid */
                .flash-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                }}
                .flash-item {{
                    background: var(--bg-card);
                    border: 1px solid var(--border-color);
                    border-radius: 10px;
                    padding: 18px;
                    transition: transform 0.2s;
                }}
                .flash-item:hover {{
                    border-color: #cbd5e1;
                    box-shadow: var(--shadow-md);
                }}
                .flash-title {{
                    font-size: 15px;
                    font-weight: 600;
                    color: #0f172a;
                    margin-bottom: 10px;
                    line-height: 1.4;
                }}
                .flash-source {{
                    font-size: 11px;
                    color: #94a3b8;
                    font-weight: 400;
                    margin-left: 5px;
                    text-decoration: none;
                }}
                .flash-source:hover {{ color: var(--primary); }}
                .flash-comment {{
                    font-size: 13px;
                    color: #b45309;
                    background-color: #fffbeb;
                    padding: 8px 12px;
                    border-radius: 6px;
                    margin-top: 8px;
                    display: flex;
                    align-items: flex-start;
                    gap: 8px;
                }}
                .comment-icon {{
                    flex-shrink: 0;
                }}
                
                .footer {{
                    text-align: center;
                    color: #94a3b8;
                    font-size: 12px;
                    margin-top: 60px;
                    padding-bottom: 30px;
                    border-top: 1px solid var(--border-color);
                    padding-top: 20px;
                }}
                
                @media (max-width: 600px) {{
                    .flash-grid {{
                        grid-template-columns: 1fr;
                    }}
                    .main-container {{
                        padding: 20px 15px;
                    }}
                    .report-title {{
                        font-size: 24px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="main-container">
                <div class="report-header">
                    <h1 class="report-title">金融早报</h1>
                    <div class="report-subtitle">AI 深度分析版 · {date_str}</div>
                </div>

                {sentiment_html}
                {themes_html}
                {flash_html}

                <div class="footer">
                    Created by AI News Collector • Powered by MiniMax M2.1
                </div>
            </div>
        </body>
        </html>
        """
        return full_html

    def format_archive_page(self, reports: list) -> str:
        """
        生成历史归档页面

        Args:
            reports: 列表，每个元素包含 {'date': 'YYYY-MM-DD', 'title': '标题', 'url': '文件名.html', 'summary': '摘要'}

        Returns:
            str: 归档页面 HTML
        """
        # 按日期降序排列
        sorted_reports = sorted(reports, key=lambda x: x['date'], reverse=True)

        # 按年份分组
        from collections import defaultdict
        by_year = defaultdict(list)
        for report in sorted_reports:
            year = report['date'][:4]
            by_year[year].append(report)

        # 按年份降序排列
        years = sorted(by_year.keys(), reverse=True)

        year_sections_html = ""
        for year in years:
            items_html = ""
            for report in by_year[year]:
                # 格式化日期显示
                date_obj = datetime.strptime(report['date'], '%Y-%m-%d')
                date_display = date_obj.strftime('%m月%d日')
                week_day = date_obj.strftime('%a')
                week_map = {'Mon': '周一', 'Tue': '周二', 'Wed': '周三', 'Thu': '周四', 'Fri': '周五', 'Sat': '周六', 'Sun': '周日'}
                week_display = week_map.get(week_day, week_day)

                items_html += f"""
                <div class="archive-item">
                    <div class="archive-date">{date_display} <span class="weekday">{week_display}</span></div>
                    <div class="archive-content">
                        <a href="{report['url']}" class="archive-link">{report['title']}</a>
                        {f'<div class="archive-summary">{report["summary"]}</div>' if report.get('summary') else ''}
                    </div>
                </div>
                """

            year_sections_html += f"""
            <div class="year-section">
                <div class="year-header">{year}年</div>
                <div class="archive-list">
                    {items_html}
                </div>
            </div>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>金融早报 | 历史归档</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Sans+SC:wght@300;400;500;700&display=swap" rel="stylesheet">
            <style>
                :root {{
                    --primary: #2563eb;
                    --bg-page: #f8fafc;
                    --text-main: #1e293b;
                    --text-muted: #64748b;
                    --border-color: #e2e8f0;
                }}

                body {{
                    font-family: 'Inter', 'Noto Sans SC', sans-serif;
                    line-height: 1.6;
                    color: var(--text-main);
                    background-color: var(--bg-page);
                    margin: 0;
                    padding: 0;
                    -webkit-font-smoothing: antialiased;
                }}

                .main-container {{
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 40px 20px;
                }}

                .report-header {{
                    text-align: center;
                    margin-bottom: 50px;
                }}
                .report-title {{
                    font-size: 32px;
                    font-weight: 800;
                    color: #0f172a;
                    letter-spacing: -0.025em;
                    margin: 0;
                }}
                .report-title::after {{
                    content: '';
                    display: block;
                    width: 60px;
                    height: 4px;
                    background: var(--primary);
                    margin: 15px auto 0;
                    border-radius: 2px;
                }}
                .report-subtitle {{
                    font-size: 16px;
                    color: var(--text-muted);
                    font-weight: 500;
                    margin-top: 10px;
                }}

                .year-section {{
                    margin-bottom: 40px;
                }}
                .year-header {{
                    font-size: 24px;
                    font-weight: 700;
                    color: #0f172a;
                    margin-bottom: 20px;
                    padding-bottom: 10px;
                    border-bottom: 2px solid var(--border-color);
                }}

                .archive-list {{
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                }}
                .archive-item {{
                    display: flex;
                    align-items: flex-start;
                    gap: 20px;
                    padding: 16px;
                    background: white;
                    border-radius: 12px;
                    border: 1px solid var(--border-color);
                    transition: all 0.2s;
                }}
                .archive-item:hover {{
                    border-color: #cbd5e1;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                }}
                .archive-date {{
                    font-size: 15px;
                    font-weight: 600;
                    color: #0f172a;
                    white-space: nowrap;
                    min-width: 80px;
                }}
                .weekday {{
                    font-size: 12px;
                    color: var(--text-muted);
                    font-weight: 400;
                    margin-left: 4px;
                }}
                .archive-content {{
                    flex: 1;
                }}
                .archive-link {{
                    font-size: 15px;
                    font-weight: 500;
                    color: var(--primary);
                    text-decoration: none;
                    display: block;
                }}
                .archive-link:hover {{
                    text-decoration: underline;
                }}
                .archive-summary {{
                    font-size: 13px;
                    color: var(--text-muted);
                    margin-top: 6px;
                    line-height: 1.5;
                }}

                .footer {{
                    text-align: center;
                    color: #94a3b8;
                    font-size: 12px;
                    margin-top: 60px;
                    padding-bottom: 30px;
                    border-top: 1px solid var(--border-color);
                    padding-top: 20px;
                }}

                .stats {{
                    text-align: center;
                    color: var(--text-muted);
                    font-size: 14px;
                    margin-bottom: 40px;
                }}

                @media (max-width: 600px) {{
                    .archive-item {{
                        flex-direction: column;
                        gap: 8px;
                    }}
                    .archive-date {{
                        font-size: 13px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="main-container">
                <div class="report-header">
                    <h1 class="report-title">金融早报</h1>
                    <div class="report-subtitle">历史归档</div>
                </div>

                <div class="stats">共 {len(sorted_reports)} 期 · {len(years)} 年</div>

                {year_sections_html}

                <div class="footer">
                    Generated by Financial News Collector
                </div>
            </div>
        </body>
        </html>
        """
        return html
