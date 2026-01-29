"""
配置加载模块
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """配置管理类"""

    _instance: Optional['Config'] = None
    _config: Dict[str, Any] = {}
    _websites: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._config:
            self.load_config()

    @classmethod
    def get_instance(cls) -> 'Config':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_config(self, config_path: str = None, websites_path: str = None):
        """加载配置文件"""
        import re

        base_dir = Path(__file__).parent.parent

        if config_path is None:
            config_path = base_dir / "config" / "config.yaml"
        else:
            config_path = Path(config_path)

        if websites_path is None:
            websites_path = base_dir / "config" / "websites.yaml"
        else:
            websites_path = Path(websites_path)

        # 解析环境变量的辅助函数
        def parse_env_vars(value):
            if isinstance(value, str):
                # 匹配 ${VAR_NAME} 格式
                pattern = r'\$\{([^}]+)\}'
                return re.sub(pattern, lambda m: os.environ.get(m.group(1), ''), value)
            elif isinstance(value, dict):
                return {k: parse_env_vars(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [parse_env_vars(item) for item in value]
            return value

        # 加载主配置
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                raw_config = yaml.safe_load(f) or {}
                self._config = parse_env_vars(raw_config)

        # 加载网站配置
        if websites_path.exists():
            with open(websites_path, 'r', encoding='utf-8') as f:
                self._websites = yaml.safe_load(f) or {}

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的路径"""
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return self._config.get('database', {'path': 'data/news.db'})

    def get_spider_config(self) -> Dict[str, Any]:
        """获取爬虫配置"""
        return self._config.get('spider', {
            'timeout': 30,
            'retry_times': 3,
            'delay': 1,
            'max_items_per_source': 50
        })

    def get_scheduler_config(self) -> Dict[str, Any]:
        """获取调度配置"""
        return self._config.get('scheduler', {
            'type': 'apscheduler',
            'trigger': 'cron',
            'hour': 8,
            'minute': 0
        })

    def get_notifiers_config(self) -> Dict[str, Any]:
        """获取通知配置"""
        return self._config.get('notifiers', {})

    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self._config.get('logging', {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file': 'logs/news_collector.log'
        })

    def get_websites(self) -> Dict[str, Any]:
        """获取所有网站配置"""
        return self._websites

    def get_websites_by_category(self, category: str) -> Dict[str, Any]:
        """按分类获取网站配置"""
        return self._websites.get(category, {})

    def get_all_website_list(self) -> list:
        """获取所有网站的扁平列表"""
        websites = []
        for category, sources in self._websites.items():
            for source_name, configs in sources.items():
                for config in configs:
                    config['category'] = category
                    config['source_type'] = source_name
                    websites.append(config)
        return websites

    def reload(self):
        """重新加载配置"""
        self._config = {}
        self._websites = {}
        self.load_config()


# 全局配置实例
config = Config.get_instance()
