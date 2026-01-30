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
            <div class="sentiment-box glass-effect has-select selected" data-card-type="sentiment">
                <div class="card-select-indicator"></div>
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
                <div class="theme-card has-select selected" data-card-type="theme">
                    <div class="card-select-indicator"></div>
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
                <div class="flash-item has-select selected" data-card-type="flash">
                    <div class="card-select-indicator"></div>
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
            <title>金融日报 | 合并报告 - {date_str}</title>
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

                /* Screenshot Feature Styles */
                .ai-toolbar {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    flex-wrap: wrap;
                    gap: 12px;
                    padding: 12px 16px;
                    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                    border: 1px solid #bae6fd;
                    border-radius: 12px;
                    margin-bottom: 16px;
                    position: sticky;
                    top: 0;
                    z-index: 100;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                }}
                .toolbar-left {{
                    display: flex;
                    align-items: center;
                    gap: 16px;
                    flex-wrap: wrap;
                }}
                .toolbar-right {{
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }}
                .selected-count {{
                    font-size: 14px;
                    color: #475569;
                }}
                .selected-count strong {{
                    color: #2563eb;
                }}

                /* Card Selection Checkbox */
                .card-select-wrapper {{
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    cursor: pointer;
                    user-select: none;
                }}
                .card-select-checkbox {{
                    width: 20px;
                    height: 20px;
                    border: 2px solid #cbd5e1;
                    border-radius: 4px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s;
                    flex-shrink: 0;
                }}
                .card-select-checkbox svg {{
                    width: 14px;
                    height: 14px;
                    stroke: white;
                    stroke-width: 3;
                    fill: none;
                    opacity: 0;
                    transition: opacity 0.2s;
                }}
                .card-select-wrapper:hover .card-select-checkbox {{
                    border-color: #2563eb;
                }}
                .card-select-wrapper.active .card-select-checkbox {{
                    background: #2563eb;
                    border-color: #2563eb;
                }}
                .card-select-wrapper.active .card-select-checkbox svg {{
                    opacity: 1;
                }}
                .card-select-label {{
                    font-size: 14px;
                    color: #475569;
                }}

                /* Card Select Indicator (for cards) */
                .card-select-indicator {{
                    position: absolute;
                    top: 8px;
                    right: 8px;
                    width: 18px;
                    height: 18px;
                    border: 2px solid #cbd5e1;
                    border-radius: 50%;
                    background: white;
                    cursor: pointer;
                    transition: all 0.2s;
                    z-index: 5;
                }}
                .card-select-indicator::after {{
                    content: '';
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%) scale(0);
                    width: 10px;
                    height: 10px;
                    background: #2563eb;
                    border-radius: 50%;
                    transition: transform 0.2s;
                }}
                .theme-card.selected .card-select-indicator,
                .flash-item.selected .card-select-indicator,
                .sentiment-box.selected .card-select-indicator {{
                    border-color: #2563eb;
                }}
                .theme-card.selected .card-select-indicator::after,
                .flash-item.selected .card-select-indicator::after,
                .sentiment-box.selected .card-select-indicator::after {{
                    transform: translate(-50%, -50%) scale(1);
                }}
                .sentiment-box .card-select-indicator {{
                    top: 10px;
                    right: 10px;
                }}

                /* Screenshot Button */
                .screenshot-btn {{
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    padding: 10px 20px;
                    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s;
                    box-shadow: 0 2px 4px rgba(37, 99, 235, 0.3);
                }}
                .screenshot-btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
                }}
                .screenshot-btn:active {{
                    transform: translateY(0);
                }}
                }}
                .screenshot-btn:disabled {{
                    background: #94a3b8;
                    cursor: not-allowed;
                    transform: none;
                    box-shadow: none;
                }}
                .screenshot-btn .spinner {{
                    animation: spin 1s linear infinite;
                }}
                @keyframes spin {{
                    from {{ transform: rotate(0deg); }}
                    to {{ transform: rotate(360deg); }}
                }}

                /* Card Selected State */
                .theme-card, .flash-item {{
                    transition: all 0.3s ease;
                }}
                .theme-card.has-select, .flash-item.has-select {{
                    cursor: pointer;
                    border: 2px solid transparent;
                }}
                .theme-card.has-select:hover, .flash-item.has-select:hover {{
                    border-color: #e2e8f0;
                }}
                .theme-card.selected, .flash-item.selected {{
                    border-color: #2563eb;
                    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
                }}
                .theme-card.excluded, .flash-item.excluded {{
                    visibility: hidden;
                    position: absolute;
                    width: 0;
                    height: 0;
                    padding: 0;
                    margin: 0;
                    overflow: hidden;
                }}

                /* Modal */
                .modal {{
                    display: none;
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.7);
                    z-index: 1000;
                    backdrop-filter: blur(4px);
                }}
                .modal.active {{
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .modal-content {{
                    background: white;
                    border-radius: 16px;
                    max-width: 90%;
                    max-height: 90%;
                    overflow: auto;
                    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
                }}
                .modal-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 20px 24px;
                    border-bottom: 1px solid #e2e8f0;
                }}
                .modal-header h3 {{
                    margin: 0;
                    font-size: 18px;
                    color: #0f172a;
                }}
                .modal-close {{
                    background: none;
                    border: none;
                    font-size: 28px;
                    color: #64748b;
                    cursor: pointer;
                    line-height: 1;
                }}
                .modal-close:hover {{
                    color: #0f172a;
                }}
                .modal-body {{
                    padding: 24px;
                    text-align: center;
                    background: #f8fafc;
                }}
                .modal-body img {{
                    max-width: 100%;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                }}
                .modal-footer {{
                    display: flex;
                    gap: 12px;
                    justify-content: center;
                    padding: 20px 24px;
                    border-top: 1px solid #e2e8f0;
                }}
                .btn-primary, .btn-secondary {{
                    padding: 10px 24px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s;
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                }}
                .btn-primary {{
                    background: #2563eb;
                    color: white;
                    border: none;
                }}
                .btn-primary:hover {{
                    background: #1d4ed8;
                }}
                .btn-secondary {{
                    background: white;
                    color: #475569;
                    border: 1px solid #cbd5e1;
                }}
                .btn-secondary:hover {{
                    background: #f8fafc;
                }}
                .toast {{
                    position: fixed;
                    bottom: 30px;
                    left: 50%;
                    transform: translateX(-50%) translateY(100px);
                    background: #0f172a;
                    color: white;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-size: 14px;
                    opacity: 0;
                    transition: all 0.3s;
                    z-index: 1001;
                }}
                .toast.show {{
                    transform: translateX(-50%) translateY(0);
                    opacity: 1;
                }}

                /* Dedicated Screenshot Container (Mobile Optimized) */
                #capture-container {{
                    position: fixed;
                    left: -9999px;
                    top: 0;
                    width: 375px;
                    background: #ffffff;
                    padding: 16px;
                    box-sizing: border-box;
                }}

                /* Mobile-optimized capture card style */
                .capture-card {{
                    margin-bottom: 16px;
                    background: #fff;
                    border-radius: 12px;
                    overflow: hidden;
                }}

                /* Screenshot title */
                .capture-title {{
                    font-size: 20px;
                    font-weight: 700;
                    text-align: center;
                    padding: 16px 0;
                    margin-bottom: 8px;
                    color: #0f172a;
                }}
            </style>
        </head>
        <body>
            <div class="main-container">
                <div class="report-header">
                    <h1 class="report-title">金融日报</h1>
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
                        <!-- Screenshot Toolbar -->
                        <div class="ai-toolbar" id="ai-toolbar">
                            <div class="toolbar-left">
                                <label class="card-select-wrapper" data-card="sentiment">
                                    <div class="card-select-checkbox">
                                        <svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg>
                                    </div>
                                    <span class="card-select-label">市场综述</span>
                                </label>
                                <label class="card-select-wrapper" data-card="themes">
                                    <div class="card-select-checkbox">
                                        <svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg>
                                    </div>
                                    <span class="card-select-label">深度专题</span>
                                </label>
                                <label class="card-select-wrapper" data-card="flash">
                                    <div class="card-select-checkbox">
                                        <svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg>
                                    </div>
                                    <span class="card-select-label">资讯速递</span>
                                </label>
                            </div>
                            <div class="toolbar-right">
                                <span class="selected-count">已选择 <strong id="selected-count">3</strong> 项</span>
                                <button id="screenshot-btn" class="screenshot-btn">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
                                    生成长截图
                                </button>
                            </div>
                        </div>

                        {ai_html if ai_html else '<p style="color: var(--text-muted); text-align: center; padding: 40px;">暂无 AI 分析数据</p>'}
                    </div>

                    <!-- Screenshot Modal -->
                    <div id="screenshot-modal" class="modal">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h3>截图预览</h3>
                                <button class="modal-close">&times;</button>
                            </div>
                            <div class="modal-body">
                                <img id="screenshot-preview" src="" alt="截图预览">
                            </div>
                            <div class="modal-footer">
                                <button id="copy-btn" class="btn-primary">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                                    复制图片
                                </button>
                                <button id="download-btn" class="btn-secondary">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                                    下载 PNG
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- Toast -->
                    <div id="toast" class="toast"></div>

                    <!-- Tab 2: All Articles -->
                    <div id="all-articles" class="tab-pane">
                        {articles_html}
                    </div>
                </div>

                <div class="footer">
                    Generated by Financial News Collector • AI 分析由 MiniMax M2.1 提供
                </div>
            </div>

            <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
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

                // ============ Screenshot Feature ============
                (function() {{
                    'use strict';

                    const ScreenshotManager = {{
                        selectedCards: new Set(),
                        currentImageData: null,

                        init: function() {{
                            this.cacheElements();
                            this.bindEvents();
                            this.selectAllCards();
                            this.updateCount();
                        }},

                        cacheElements: function() {{
                            this.toolbar = document.getElementById('ai-toolbar');
                            this.screenshotBtn = document.getElementById('screenshot-btn');
                            this.modal = document.getElementById('screenshot-modal');
                            this.previewImg = document.getElementById('screenshot-preview');
                            this.copyBtn = document.getElementById('copy-btn');
                            this.downloadBtn = document.getElementById('download-btn');
                            this.toast = document.getElementById('toast');
                            this.aiAnalysis = document.getElementById('ai-analysis');
                            this.captureContainer = document.getElementById('capture-container');
                        }},

                        bindEvents: function() {{
                            var self = this;

                            // Card selection toggles
                            document.querySelectorAll('.card-select-wrapper').forEach(function(wrapper) {{
                                wrapper.addEventListener('click', function(e) {{
                                    e.preventDefault();
                                    e.stopPropagation();
                                    var cardType = this.getAttribute('data-card');
                                    if (cardType) {{
                                        self.toggleCardType(cardType);
                                    }}
                                }});
                            }});

                            // Individual card selection
                            document.querySelectorAll('.sentiment-box, .theme-card, .flash-item').forEach(function(card) {{
                                card.addEventListener('click', function() {{
                                    self.toggleCard(this);
                                }});
                            }});

                            // Screenshot button
                            this.screenshotBtn.addEventListener('click', function() {{
                                self.captureScreenshot();
                            }});

                            // Modal close
                            document.querySelector('.modal-close').addEventListener('click', function() {{
                                self.closeModal();
                            }});

                            this.copyBtn.addEventListener('click', function() {{
                                self.copyToClipboard();
                            }});

                            this.downloadBtn.addEventListener('click', function() {{
                                self.downloadImage();
                            }});

                            // Close modal on background click
                            this.modal.addEventListener('click', function(e) {{
                                if (e.target === self.modal) {{
                                    self.closeModal();
                                }}
                            }});
                        }},

                        toggleCardType: function(cardType) {{
                            var wrappers = document.querySelectorAll('.card-select-wrapper[data-card="' + cardType + '"]');
                            var cards = document.querySelectorAll('[data-card-type="' + cardType + '"]');

                            // Check if all cards of this type are selected
                            var allSelected = true;
                            cards.forEach(function(card) {{
                                if (!this.selectedCards.has(card)) {{
                                    allSelected = false;
                                }}
                            }}.bind(this));

                            // Toggle
                            wrappers.forEach(function(wrapper) {{
                                if (allSelected) {{
                                    wrapper.classList.remove('active');
                                }} else {{
                                    wrapper.classList.add('active');
                                }}
                            }});

                            cards.forEach(function(card) {{
                                if (allSelected) {{
                                    card.classList.remove('selected');
                                    this.selectedCards.delete(card);
                                }} else {{
                                    card.classList.add('selected');
                                    this.selectedCards.add(card);
                                }}
                            }}.bind(this));

                            this.updateCount();
                        }},

                        toggleCard: function(card) {{
                            if (this.selectedCards.has(card)) {{
                                card.classList.remove('selected');
                                this.selectedCards.delete(card);
                            }} else {{
                                card.classList.add('selected');
                                this.selectedCards.add(card);
                            }}
                            this.updateCount();
                            // Update toolbar checkbox based on card type
                            this.updateToolbarCheckbox(card.getAttribute('data-card-type'));
                        }},

                        selectAllCards: function() {{
                            document.querySelectorAll('.has-select').forEach(function(card) {{
                                card.classList.add('selected');
                                this.selectedCards.add(card);
                            }}.bind(this));
                            // Update all toolbar checkboxes
                            this.updateToolbarCheckbox('sentiment');
                            this.updateToolbarCheckbox('themes');
                            this.updateToolbarCheckbox('flash');
                        }},

                        deselectAllCards: function() {{
                            document.querySelectorAll('.has-select').forEach(function(card) {{
                                card.classList.remove('selected');
                                this.selectedCards.delete(card);
                            }}.bind(this));
                            // Update all toolbar checkboxes
                            this.updateToolbarCheckbox('sentiment');
                            this.updateToolbarCheckbox('themes');
                            this.updateToolbarCheckbox('flash');
                        }},

                        updateCount: function() {{
                            var count = this.selectedCards.size;
                            var countEl = document.getElementById('selected-count');
                            if (countEl) {{
                                countEl.textContent = count;
                            }}
                            this.screenshotBtn.disabled = count === 0;
                        }},

                        updateToolbarCheckbox: function(cardType) {{
                            var wrappers = document.querySelectorAll('.card-select-wrapper[data-card="' + cardType + '"]');
                            var cards = document.querySelectorAll('[data-card-type="' + cardType + '"]');
                            var allSelected = true;

                            cards.forEach(function(card) {{
                                if (!this.selectedCards.has(card)) {{
                                    allSelected = false;
                                }}
                            }}.bind(this));

                            wrappers.forEach(function(wrapper) {{
                                if (allSelected) {{
                                    wrapper.classList.add('active');
                                }} else {{
                                    wrapper.classList.remove('active');
                                }}
                            }});
                        }},

                        hideUnselectedCards: function() {{
                            document.querySelectorAll('.has-select').forEach(function(card) {{
                                if (!this.selectedCards.has(card)) {{
                                    card.classList.add('excluded');
                                }}
                            }}.bind(this));
                        }},

                        showAllCards: function() {{
                            document.querySelectorAll('.has-select.excluded').forEach(function(card) {{
                                card.classList.remove('excluded');
                            }});
                        }},

                        showToast: function(message) {{
                            this.toast.textContent = message;
                            this.toast.classList.add('show');
                            setTimeout(function() {{
                                this.toast.classList.remove('show');
                            }}.bind(this), 2000);
                        }},

                        // Mobile-optimized: Prepare cards in dedicated container
                        preCapture: function() {{
                            var container = this.captureContainer;
                            if (!container) return;

                            // Clear previous content
                            container.innerHTML = '';

                            // Add title
                            var title = document.createElement('div');
                            title.className = 'capture-title';
                            title.textContent = '金融日报';
                            container.appendChild(title);

                            // Clone selected cards in DOM order (maintains original order)
                            var allCards = document.querySelectorAll('.has-select');
                            allCards.forEach(function(card) {{
                                if (this.selectedCards.has(card)) {{
                                    var clone = card.cloneNode(true);

                                    // Remove selection indicator
                                    var indicator = clone.querySelector('.card-select-indicator');
                                    if (indicator) indicator.remove();

                                    // Remove selection-related classes
                                    clone.classList.remove('selected', 'has-select', 'excluded');

                                    // Convert position:fixed to relative (html2canvas fix)
                                    clone.querySelectorAll('*').forEach(function(el) {{
                                        var style = window.getComputedStyle(el);
                                        if (style.position === 'fixed') {{
                                            el.style.position = 'relative';
                                        }}
                                    }});

                                    // Wrap in capture-card for mobile optimization
                                    var wrapper = document.createElement('div');
                                    wrapper.className = 'capture-card';
                                    wrapper.appendChild(clone);
                                    container.appendChild(wrapper);
                                }}
                            }}.bind(this));
                        }},

                        captureScreenshot: function() {{
                            var self = this;
                            var btn = this.screenshotBtn;
                            var originalHTML = btn.innerHTML;

                            btn.innerHTML = '<svg class="spinner" viewBox="0 0 24 24" width="18" height="18"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" fill="none" stroke-dasharray="30 60"/></svg> 生成中...';
                            btn.disabled = true;

                            // Prepare cards in dedicated container
                            this.preCapture();

                            // Use the cached capture container
                            var container = this.captureContainer;
                            if (!container || container.children.length === 0) {{
                                this.showToast('请先选择要截图的卡片');
                                btn.innerHTML = originalHTML;
                                btn.disabled = false;
                                return;
                            }}

                            // Use dedicated container for capture
                            html2canvas(container, {{
                                useCORS: true,
                                allowTaint: true,
                                backgroundColor: '#ffffff',
                                scale: 2,  // Retina quality
                                width: 375,  // Mobile width
                                logging: false
                            }}).then(function(canvas) {{
                                // Show preview
                                self.currentImageData = canvas.toDataURL('image/png', 1.0);
                                self.previewImg.src = self.currentImageData;
                                self.modal.classList.add('active');

                                // Mobile: show long-press hint
                                if (/Mobile|Android|iPhone/i.test(navigator.userAgent)) {{
                                    self.showToast('长按图片保存到相册');
                                }}
                            }}).catch(function(error) {{
                                console.error('Screenshot failed:', error);
                                self.showToast('截图失败，请重试');
                            }}).finally(function() {{
                                btn.innerHTML = originalHTML;
                                btn.disabled = self.selectedCards.size === 0;
                            }});
                        }},

                        closeModal: function() {{
                            this.modal.classList.remove('active');
                        }},

                        downloadImage: function() {{
                            if (!this.currentImageData) return;

                            var link = document.createElement('a');
                            var date = new Date().toISOString().slice(0, 10);
                            link.download = '金融日报-AI分析-' + date + '.png';
                            link.href = this.currentImageData;
                            link.click();
                        }},

                        copyToClipboard: function() {{
                            var self = this;
                            if (!this.currentImageData) return;

                            // Convert data URL to blob
                            fetch(this.currentImageData)
                                .then(function(res) {{ return res.blob(); }})
                                .then(function(blob) {{
                                    var item = new ClipboardItem({{ 'image/png': blob }});
                                    return navigator.clipboard.write([item]);
                                }})
                                .then(function() {{
                                    self.showToast('已复制到剪贴板');
                                    self.closeModal();
                                }})
                                .catch(function(error) {{
                                    console.error('Copy failed:', error);
                                    self.showToast('复制失败，请手动保存');
                                }});
                        }}
                    }};

                    // Initialize on DOM ready
                    if (document.readyState === 'loading') {{
                        document.addEventListener('DOMContentLoaded', function() {{
                            ScreenshotManager.init();
                        }});
                    }} else {{
                        ScreenshotManager.init();
                    }}
                }})();
            </script>

            <!-- Dedicated Screenshot Container (Hidden, for Mobile Optimized Capture) -->
            <div id="capture-container"></div>
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
            <title>金融日报 | AI 深度版 - {date_str}</title>
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
                    <h1 class="report-title">金融日报</h1>
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
            <title>金融日报 | 历史归档</title>
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
                    <h1 class="report-title">金融日报</h1>
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
