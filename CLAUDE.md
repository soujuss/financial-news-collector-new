# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 常用命令

```bash
# 激活虚拟环境
source venv/bin/activate

# 立即执行一次爬取
python main.py run-once

# 启动定时守护进程（默认每天 8:00）
python main.py daemon

# 测试单个网站（--source 后接 websites.yaml 中的 name）
python main.py test --source 东方财富网

# 生成今日资讯报告
python main.py report

# 查看系统状态
python main.py status

# AI 分析测试（从数据库获取文章，无需爬取）
python test_ai.py                       # 默认昨天
python test_ai.py --date 2026-01-22     # 指定日期
python test_ai.py --today               # 今天
python test_ai.py --days 3              # 最近3天
```

## 项目架构

### 数据流
```
websites.yaml → Scheduler → Spiders → Deduplicator → Database → [AI分析] → Notifiers
                                                                          ↓
                                                               outputs/news_YYYY-MM-DD.html
```

### 核心模块
- **spiders/**: 爬虫模块
  - `base_spider.py`: 通用方法（HTML解析、请求发送）
  - `scrapy_spider.py`: 静态页面爬虫（requests + BeautifulSoup）
  - `rss_spider.py`: RSS 订阅源爬虫（xml.etree.ElementTree）
  - `playwright_spider.py`: 动态页面爬虫（支持反检测 stealth）
- **processors/**: 内容处理
  - `deduplicator.py`: 三级去重（URL → 标题 → 内容哈希）
  - `formatter.py`: 多渠道格式化 + AI报告生成（双标签页）
  - `ai_processor.py`: MiniMax M2.1 集成，JSON解析容错
- **notifiers/**: 通知模块
  - `base.py`: 通知器工厂类
  - `email/telegram/wechat.py`: 各渠道实现

### AI 智能分析
- **角色**: 资深财经研究员 + 编辑总监
- **输出**: 市场综述、主题聚类（带重要性标记）、资讯速递（带一句话点评）
- **报告**: `outputs/news_YYYY-MM-DD.html` 包含 AI分析/原始资讯两个标签页
- **容错**: JSON解析支持三种策略（标准 → 修复 → 正则提取）

### 配置结构
- `config.yaml`: 爬虫参数、超时、重试、通知设置、AI配置（MiniMax）
- `websites.yaml`: 网站URL、CSS选择器、爬虫类型、URL排除模式

**网站配置字段**: `name`, `type` (scrapy/rss/playwright), `list_url`, `list_selector`, `exclude_patterns`, `use_stealth`, `wait_time`, `rss_url`

## CI/CD (GitHub Actions)

### 自动部署
- **Workflow**: `.github/workflows/daily-crawl.yml`
- **触发**: 每天 UTC 0:00（北京时间 8:00）
- **输出**: GitHub Pages (`https://<user>.github.io/<repo>/`)

### GitHub 配置
1. 添加 Secrets: `ANTHROPIC_API_KEY`（AI 分析需要）
2. 启用 Pages: Settings → Pages → Source = "GitHub Actions"
3. 访问首页: `outputs/index.html`（自动跳转到最新报告）

### 手动触发
```bash
# 在 GitHub Actions 页面手动触发
# 或通过 workflow_dispatch 事件
```
