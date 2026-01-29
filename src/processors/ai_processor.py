"""
AI 处理器模块 - 负责调用 LLM 进行深度内容分析
"""

import os
import json
import re
import logging
from typing import List, Dict, Any
import anthropic

from ..models import NewsArticle

logger = logging.getLogger(__name__)


class AIProcessor:
    """
    AI 财经研究员处理器 (基于 Anthropic SDK / MiniMax)
    角色：资深财经研究员 + 编辑总监
    功能：去重、聚类、观点提炼、市场综述
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', False)
        self.client = None
        self.model = config.get('model', 'MiniMax-M2.1')
        
        if self.enabled:
            self._init_client()

    def _init_client(self):
        """初始化 Anthropic 客户端"""
        try:
            api_key = self.config.get('api_key')
            base_url = self.config.get('base_url')
            
            # 处理环境变量占位符
            if api_key and api_key.startswith('${') and api_key.endswith('}'):
                env_var = api_key[2:-1]
                api_key = os.getenv(env_var)
            
            if not api_key:
                logger.warning("未配置 AI API Key，AI 功能将不可用")
                self.enabled = False
                return

            # 初始化客户端
            # 如果是 MiniMax 兼容 Anthropic 协议，可能需要指定 base_url
            # 如果未指定 base_url，则使用默认（通常是 api.anthropic.com，这对 MiniMax 可能不对，除非是通过 Router）
            # 用户示例中没有 base_url，但通常第三方兼容接口需要。这里暂且信任配置中的 base_url。
            kwargs = {"api_key": api_key}
            if base_url:
                kwargs["base_url"] = base_url

            self.client = anthropic.Anthropic(**kwargs)
            logger.info(f"AI 客户端初始化成功 (Model: {self.model})")
        except Exception as e:
            logger.error(f"AI 客户端初始化失败: {e}")
            self.enabled = False

    def process_daily_news(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """
        处理每日新闻，生成深度报告
        """
        if not self.enabled or not self.client:
            logger.info("AI 功能未启用或初始化失败，跳过智能处理")
            return None

        if not articles:
            return None

        try:
            # 1. 准备输入数据
            news_data = self._prepare_input_data(articles)
            
            # 2. 调用 LLM
            logger.info(f"正在调用 LLM ({self.model}) 进行深度分析，处理 {len(articles)} 条新闻...")
            response_json = self._call_llm_analysis(news_data)
            
            # 3. 结果校验与增强
            if response_json:
                logger.info("AI 分析完成，成功生成报告结构")
                # 将原始文章对象挂载回 ID，方便格式化器使用
                self._attach_articles_to_themes(response_json, articles)
                return response_json
            else:
                logger.error("AI 分析返回空结果")
                return None
                
        except Exception as e:
            logger.error(f"AI 处理过程中发生错误: {e}", exc_info=True)
            return None

    def _prepare_input_data(self, articles: List[NewsArticle]) -> str:
        """准备发送给 LLM 的轻量级 JSON 数据"""
        simple_list = []
        for i, art in enumerate(articles):
            art_id = i 
            content_preview = art.summary if art.summary else (art.content[:800] if art.content else "")
            
            simple_list.append({
                "id": art_id,
                "title": art.title,
                "source": art.source,
                "category": art.category,
                "content": content_preview,
                "time": art.publish_time.strftime("%H:%M") if art.publish_time else ""
            })
        
        return json.dumps(simple_list, ensure_ascii=False)

    def _call_llm_analysis(self, news_input: str) -> Dict[str, Any]:
        """调用 LLM 进行分析"""
        
        system_prompt = """
你是一位拥有20年经验的【资深财经研究员】和【编辑总监】。
你的任务是对当天采集的财经新闻进行深度梳理、去伪存真，并输出一份高质量的研报级摘要。

### 处理原则：
1. **去噪与去重**：剔除软文、重复通稿。归并同一事件报道。
2. **主题归并与洞察**：
   - 将碎片化新闻聚类为核心【主题/事件】。
   - 必须为每个主要主题提供【研究员洞察/点评】（Insight），揭示背后逻辑。
3. **市场综述**：提供简练的市场情绪与宏观综述。

### 输出格式：
必须严格返回合法的 **JSON** 格式。不要包含任何 Markdown 标记或 Thinking 过程（如果有）。

Structure:
{
  "market_sentiment": "150字综述...",
  "themes": [
    {
       "title": "主题名称",
       "importance": "高/中/低",
       "summary": "事件核心事实",
       "insight": "深度点评...",
       "related_article_ids": [0, 1]
    }
  ],
  "news_flash": [
     { "id": 2, "title": "标题", "one_sentence_comment": "点评" }
  ]
}
"""
        
        user_content = f"这是今日采集的原始财经新闻列表（JSON格式）：\n\n{news_input}\n\n请分析并输出 JSON。"

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_content
                            }
                        ]
                    }
                ]
            )
            
            # 解析响应
            # MiniMax M2.1 用 Anthropic SDK 时，可能会返回 text 或 thinking 块
            # 我们需要提取 text 块中的 JSON
            
            full_text = ""
            # Handle list of ContentBlock objects (Anthropic SDK)
            if isinstance(message.content, list):
                for block in message.content:
                    if hasattr(block, 'text'):
                        full_text += block.text
                    elif isinstance(block, dict) and 'text' in block:
                        full_text += block['text']
            else:
                # Fallback if it's just a string or other format
                full_text = str(message.content)
            
            logger.info(f"LLM Raw Response: {full_text[:500]}...") # Log first 500 chars

            # 清理 Markdown
            content = full_text.replace("```json", "").replace("```", "").strip()

            # 尝试找到 JSON 起止
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end != -1:
                content = content[start:end]

            logger.info(f"Extracted JSON Content: {content[:200]}...")

            # 尝试多种方法解析JSON
            return self._try_parse_json(content)
            
        except Exception as e:
            logger.error(f"LLM 调用异常: {e}")
            raise e

    def _fix_json_content(self, content: str) -> str:
        """
        修复JSON内容中的常见问题：
        1. 未转义的换行符（在字符串值内）
        2. 未转义的引号
        3. 注释内容
        4. 多余的逗号
        """
        # 1. 移除行内换行符（在引号内的）
        # 匹配 "key": "value with \n newlines"
        def replace_newlines_in_strings(match):
            prefix = match.group(1)
            value = match.group(2)
            suffix = match.group(3)
            # 将换行替换为空格
            cleaned_value = value.replace('\n', ' ').replace('\r', ' ').strip()
            # 移除多余空格
            cleaned_value = re.sub(r'\s+', ' ', cleaned_value)
            return prefix + cleaned_value + suffix

        # 更激进的方法：直接移除所有换行（简单但有效）
        lines = content.split('\n')
        cleaned_lines = []
        in_string = False
        for line in lines:
            # 移除行尾注释
            if not in_string:
                line = re.sub(r'//.*$', '', line)
                line = re.sub(r'#.*$', '', line)

            cleaned_line = []
            for i, char in enumerate(line):
                if char == '"' and (i == 0 or line[i-1] != '\\'):
                    in_string = not in_string
                if in_string and char == '\n':
                    continue  # 跳过字符串内的换行
                cleaned_line.append(char)
            cleaned_lines.append(''.join(cleaned_line))

        content = '\n'.join(cleaned_lines)

        # 2. 移除数组/对象末尾的逗号
        content = re.sub(r',(\s*[}\]])', r'\1', content)

        # 3. 处理 Windows 换行符
        content = content.replace('\r\n', '\n').replace('\r', '\n')

        # 4. 修复未转义的引号（简化处理）
        # 使用更简单的方法：匹配 "key": "value" 模式
        content = re.sub(r':\s*"([^"]*)"([",}\]])', lambda m: ': "' + m.group(1).replace('"', '\\"') + '"' + m.group(2), content)

        # 5. 清理多余的空格
        content = re.sub(r'\s+', ' ', content)

        return content

    def _try_parse_json(self, content: str) -> Dict[str, Any]:
        """
        尝试多种方法解析JSON，优先使用标准库
        """
        # 方法1：直接解析
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.debug(f"标准JSON解析失败: {e}")

        # 方法2：尝试修复后解析
        fixed = self._fix_json_content(content)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError as e:
            logger.debug(f"修复后JSON解析失败: {e}")

        # 方法3：使用正则提取关键字段（最后手段）
        return self._extract_json_fields(content)

    def _extract_json_fields(self, content: str) -> Dict[str, Any]:
        """
        从损坏的JSON中提取关键字段（兜底方案）
        """
        result = {}

        # 提取 market_sentiment
        match = re.search(r'"market_sentiment":\s*"([^"]*)"', content, re.DOTALL)
        if match:
            result['market_sentiment'] = match.group(1).replace('\n', ' ').replace('\\n', ' ')

        # 提取 themes
        themes = []
        theme_pattern = r'"title":\s*"([^"]+)".*?"importance":\s*"([^"]+)".*?"summary":\s*"([^"]+)".*?"insight":\s*"([^"]+)"'
        for m in re.finditer(theme_pattern, content, re.DOTALL):
            themes.append({
                'title': m.group(1),
                'importance': m.group(2),
                'summary': m.group(3),
                'insight': m.group(4)
            })
        if themes:
            result['themes'] = themes

        # 提取 news_flash
        flash_items = []
        flash_pattern = r'"title":\s*"([^"]+)".*?"one_sentence_comment":\s*"([^"]+)"'
        for m in re.finditer(flash_pattern, content, re.DOTALL):
            flash_items.append({
                'title': m.group(1),
                'one_sentence_comment': m.group(2)
            })
        if flash_items:
            result['news_flash'] = flash_items

        if result:
            logger.info(f"从损坏的JSON中提取到 {len(result)} 个字段")
        else:
            logger.error("无法从响应中提取任何有效JSON字段")

        return result

    def _attach_articles_to_themes(self, report_data: Dict, original_articles: List[NewsArticle]):
        """挂载原始文章"""
        if "themes" in report_data:
            for theme in report_data["themes"]:
                ids = theme.get("related_article_ids", [])
                theme["articles"] = []
                for aid in ids:
                    if isinstance(aid, int) and 0 <= aid < len(original_articles):
                        theme["articles"].append(original_articles[aid])
        
        if "news_flash" in report_data:
            for flash in report_data["news_flash"]:
                aid = flash.get("id")
                if isinstance(aid, int) and 0 <= aid < len(original_articles):
                    flash["article"] = original_articles[aid]
