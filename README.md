# 金融资讯定时爬取系统

定时从主流财经网站爬取资讯，整理后通过多渠道（邮件/Telegram/企业微信）推送给用户。

## 功能特点

- **多源爬取**: 支持 Scrapy、Playwright 多种爬取方式
- **智能过滤**: URL 排除模式过滤广告、无效链接
- **定时执行**: 每天自动执行，支持自定义时间
- **多渠道推送**: 支持邮件、Telegram、企业微信
- **AI 智能分析**: MiniMax M2.1 模型生成市场综述、主题聚类、洞察点评
- **去重机制**: 自动去重，避免重复内容
- **易于配置**: YAML 配置文件，易于维护

## 数据源概览

| 分类 | 来源数量 | 说明 |
|------|----------|------|
| 综合财经门户 | 5 个 | 东方财富网、新浪财经、证券时报网等 |
| 深度财经媒体 | 3 个 | 财新网、第一财经、21世纪经济报道 |
| 实时数据平台 | 2 个 | 金十数据、华尔街见闻、格隆汇 |

## 安装

```bash
# 进入项目目录
cd financial-news-collector

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或: venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器（用于动态页面）
playwright install chromium
```

## 配置

### 1. 修改 config/config.yaml

```yaml
# 数据库配置
database:
  path: "data/news.db"

# 爬虫配置
spider:
  timeout: 30           # 请求超时(秒)
  retry_times: 3        # 重试次数
  delay: 1              # 请求间隔(秒)

# 定时配置 (每天早上8点)
scheduler:
  hour: 8
  minute: 0

# 通知配置
notifiers:
  email:
    enabled: false      # 改为 true 启用
    smtp_host: "smtp.163.com"
    smtp_port: 465
    username: "your@email.com"
    password: "your_password"
    from_name: "金融资讯机器人"
    to:
      - "user@example.com"

  telegram:
    enabled: false      # 改为 true 启用
    bot_token: "your_bot_token"
    chat_id: "your_chat_id"

  wechat:
    enabled: false      # 改为 true 启用
    webhook_url: "https://qyapi.weixin.qq.com/..."
```

### 2. 修改 config/websites.yaml

按需注释/取消注释网站配置，每个网站的 selector 可能需要根据实际页面结构调整。

### 3. AI 智能分析配置（可选）

系统支持使用 MiniMax M2.1 模型进行 AI 智能分析：

```yaml
# AI 配置
ai:
  enabled: true                      # 改为 false 禁用 AI
  provider: "anthropic"              # 使用 Anthropic SDK
  api_key: "${ANTHROPIC_API_KEY}"    # 从环境变量读取 API Key
  base_url: "https://api.minimaxi.com/anthropic"  # MiniMax 兼容端点
  model: "MiniMax-M2.1"              # AI 模型
  temperature: 0.3                   # 温度参数（越低越稳定）
```

设置 API Key：
```bash
export ANTHROPIC_API_KEY="your_api_key_here"
```

## 快速开始

### 步骤 1：激活虚拟环境

```bash
cd /Users/sword/work/AI/financial-news-collector
source venv/bin/activate
```

### 步骤 2：配置通知（可选）

编辑 `config/config.yaml`，启用你需要的通知渠道：

```yaml
# 邮件通知
email:
  enabled: true  # 改为 true 启用
  smtp_host: "smtp.163.com"
  smtp_port: 465
  smtp_ssl: true
  username: "your@email.com"
  password: "your授权码"
  from_name: "金融资讯机器人"
  to:
    - "user@example.com"

# 或 Telegram 通知
telegram:
  enabled: true  # 改为 true 启用
  bot_token: "your_bot_token"
  chat_id: "your_chat_id"
```

### 步骤 3：执行爬取

```bash
# 方式一：立即执行一次
python main.py run-once

# 方式二：启动定时守护进程（每天 8:00 自动执行）
python main.py daemon

# 自定义执行时间
python main.py daemon --hour 9 --minute 30  # 每天 9:30 执行
```

### 步骤 4：查看结果

```bash
# 查看今日资讯报告
python main.py report

# 查看系统状态
python main.py status

# 查看数据库统计
./venv/bin/python -c "from src.database import db; print(db.get_statistics())"

# 查看日志
tail -f logs/news_collector.log
```

### 步骤 5：手动发送通知（如已配置）

```bash
python main.py notify
```

## 命令速查

| 命令 | 说明 |
|------|------|
| `python main.py run-once` | 立即执行一次爬取 |
| `python main.py daemon` | 启动定时守护进程 |
| `python main.py daemon --hour 9 --minute 30` | 自定义执行时间 |
| `python main.py test --source 东方财富网` | 测试爬取单个网站 |
| `python main.py test --source insurance` | 测试爬取保险分类 |
| `python main.py status` | 查看系统状态 |
| `python main.py report` | 生成今日资讯报告 |
| `python main.py report --days 7` | 生成最近 7 天报告 |
| `python main.py notify` | 手动发送通知 |

## AI 智能分析

### AI 分析脚本

无需重新爬取数据，可直接从数据库获取文章进行 AI 分析：

```bash
# 默认获取昨天文章进行分析
python test_ai.py

# 获取指定日期文章
python test_ai.py --date 2026-01-22

# 获取今天文章
python test_ai.py --today

# 获取最近 3 天文章
python test_ai.py --days 3
```

### AI 输出报告

AI 分析会生成包含以下内容的报告：

| 区块 | 内容 |
|------|------|
| **市场综述** | AI 生成的市场情绪与宏观综述 |
| **深度专题** | 主题聚类 + 研究员洞察 + 重要性标记 |
| **资讯速递** | 精选新闻 + 一句话点评 |

报告保存路径：`outputs/ai_YYYY-MM-DD.html`

### HTML 报告（合并版）

爬取完成后自动生成 `outputs/news_YYYY-MM-DD.html`，包含：
- **AI 分析标签页**：市场综述、深度专题、资讯速递
- **原始资讯标签页**：按来源分类的原始文章列表

## 停止服务

如果用 `daemon` 模式启动，按 `Ctrl+C` 即可停止服务。

## 项目结构

```
financial-news-collector/
├── config/
│   ├── config.yaml         # 主配置文件（通知、定时、爬虫设置）
│   └── websites.yaml       # 网站配置（URL、选择器、分类）
├── src/
│   ├── __init__.py
│   ├── config.py           # 配置加载模块
│   ├── models.py           # 数据模型（NewsArticle、CrawlResult）
│   ├── database.py         # SQLite 数据库操作
│   ├── scheduler.py        # 定时任务调度器
│   ├── spiders/            # 爬虫模块
│   │   ├── __init__.py
│   │   ├── base_spider.py  # 爬虫基类
│   │   ├── scrapy_spider.py  # 通用网页爬虫
│   │   ├── rss_spider.py     # RSS 订阅源爬虫
│   │   └── playwright_spider.py  # 动态页面爬虫
│   ├── processors/         # 内容处理
│   │   ├── __init__.py
│   │   ├── deduplicator.py  # 去重处理器
│   │   ├── formatter.py     # 格式化器（邮件/Telegram/企业微信）
│   │   └── ai_processor.py  # AI 智能分析（MiniMax M2.1）
│   └── notifiers/          # 通知模块
│       ├── __init__.py
│       ├── email.py        # 邮件通知
│       ├── telegram.py     # Telegram 通知
│       └── wechat.py       # 企业微信通知
├── data/                   # 数据库存储目录
├── logs/                   # 日志文件目录
├── outputs/                # 生成报告输出目录
├── main.py                 # 入口文件
├── test_ai.py              # AI 分析测试脚本
├── requirements.txt        # Python 依赖
├── .gitignore
└── README.md
```

## 通知渠道配置

### 邮件

支持 Gmail、163 邮箱、QQ 邮箱等 SMTP 服务。

**Gmail 配置示例：**
```yaml
email:
  enabled: true
  smtp_host: "smtp.gmail.com"
  smtp_port: 587
  smtp_ssl: true
  username: "your@gmail.com"
  password: "your_app_password"  # 使用应用专用密码
```

**163 邮箱配置示例：**
```yaml
email:
  enabled: true
  smtp_host: "smtp.163.com"
  smtp_port: 465
  smtp_ssl: true
  username: "your@163.com"
  password: "your授权码"
```

### Telegram

1. 联系 [@BotFather](https://t.me/BotFather) 创建机器人
2. 获取 `bot_token`
3. 将机器人添加到群组，获取 `chat_id`（可以是个人或群组 ID）

### 企业微信

1. 企业微信 → 应用管理 → 创建应用
2. 获取应用 Secret 和 AgentId
3. 设置应用接收消息 → 获取 webhook URL

## 监控与日志

### 查看日志

```bash
# 实时查看日志
tail -f logs/news_collector.log

# 查看错误日志
grep "ERROR" logs/news_collector.log
```

### 数据库查询

```bash
# 进入 Python 环境
./venv/bin/python

# 查询示例
from src.database import db
from src.models import NewsArticle

# 今日资讯数量
stats = db.get_statistics()
print(f"今日: {stats['today_count']}, 总计: {stats['total_count']}")

# 获取最近资讯
articles = db.get_recent_articles(days=1)
for a in articles[:5]:
    print(f"- {a.title} ({a.source})")
```

## 常见问题

### 1. 爬取失败/超时

- 检查网络连接
- 某些网站可能有反爬虫机制
- 查看日志：`logs/news_collector.log`
- 调整 `config/config.yaml` 中的 `timeout` 和 `retry_times`

### 2. 邮件发送失败

- 检查 SMTP 配置是否正确
- 确认账号密码（ Gmail 需要应用专用密码）
- 检查防火墙是否阻止 SMTP 端口

### 3. 数据为空

- 检查 `config/websites.yaml` 中的选择器是否正确
- 尝试：`python main.py test --source 网站名称`
- 查看日志中的爬取过程

### 4. Playwright 安装

```bash
pip uninstall playwright -y
pip install playwright
playwright install --with-deps
```

## Linux/Mac 定时任务（可选）

如果不想用内置调度器，可以用 crontab：

```bash
# 编辑 crontab
crontab -e

# 添加定时任务（每天 8:00 执行）
0 8 * * * cd /path/to/financial-news-collector && ./venv/bin/python main.py run-once >> logs/cron.log 2>&1
```

## License

---

## GitHub Actions 自动部署

### 触发条件

| 触发方式 | 说明 |
|----------|------|
| **定时触发** | 每天 UTC 0:00（北京时间 8:00）自动运行 |
| **手动触发** | 在 Actions 页面点击 "Run workflow" |
| **代码推送** | 推送代码到 master 分支时自动触发（可禁用） |

### 运行流程

```
┌─────────────────────────────────────────────────────────────┐
│  GitHub Actions 自动流程                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Checkout                                                │
│     └─→ 检出代码仓库                                        │
│                                                             │
│  2. Set up Python 3.11                                      │
│     └─→ 配置 Python 环境（带 pip 缓存）                      │
│                                                             │
│  3. Install dependencies                                    │
│     ├─→ 升级 pip                                            │
│     ├─→ 安装 requirements.txt 中的依赖                      │
│     └─→ 安装 Playwright Chromium 浏览器                     │
│                                                             │
│  4. Run crawl                                               │
│     ├─→ 读取 config/websites.yaml 配置                      │
│     ├─→ 从各数据源爬取资讯                                  │
│     ├─→ 执行去重和内容处理                                  │
│     ├─→ AI 智能分析（MiniMax M2.1）                         │
│     └─→ 生成 outputs/news_YYYY-MM-DD.html                   │
│                                                             │
│  5. Verify outputs                                          │
│     └─→ 验证 outputs 目录文件                               │
│                                                             │
│  6. Upload artifact                                         │
│     └─→ 上传 outputs 目录作为 Pages artifact                │
│                                                             │
│  7. Deploy to GitHub Pages                                  │
│     └─→ 自动部署到 GitHub Pages                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 配置步骤

#### 步骤 1：添加 API Key Secret

1. 进入仓库 **Settings** → **Secrets and variables** → **Actions**
2. 点击 **New repository secret**
3. 配置：

| Name | Secret |
|------|--------|
| `ANTHROPIC_API_KEY` | `sk-ant-api03-你的密钥` |

#### 步骤 2：启用 GitHub Pages

1. 进入仓库 **Settings** → **Pages**
2. **Source** 选择 "GitHub Actions"
3. 保存设置

#### 步骤 3：访问报告

部署完成后，访问：`https://<你的用户名>.github.io/<仓库名>/`

会自动跳转到最新的每日报告：`news_YYYY-MM-DD.html`

### 查看运行状态

1. 进入仓库 **Actions** 标签
2. 查看 **Daily News Crawl & Pages** workflow
3. 点击具体的 run 查看日志

### 常见问题

| 问题 | 解决 |
|------|------|
| Actions 运行失败 | 检查 Settings → Secrets 是否配置正确 |
| 页面无法访问 | 确认 Settings → Pages → Source = GitHub Actions |
| 依赖安装超时 | 检查 requirements.txt 是否完整 |
| AI 分析失败 | 确认 ANTHROPIC_API_KEY 有效且额度充足 |

### 自定义触发时间

修改 `.github/workflows/daily-crawl.yml` 中的 cron 表达式：

```yaml
on:
  schedule:
    # 每天 UTC 0:00（北京时间 8:00）
    - cron: '0 0 * * *'
    # 每天 UTC 12:00（北京时间 20:00）
    # - cron: '0 12 * * *'
```

### 禁用自动推送触发（可选）

如需只保留定时触发，删除 workflow 中的 push 分支：

```yaml
on:
  schedule:
    - cron: '0 0 * * *'
  workflow_dispatch:  # 保留手动触发
  # push:
  #   branches: [master]  # 注释或删除这行
```

MIT License
