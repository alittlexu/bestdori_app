"""
配置管理器 - 用于管理应用程序配置
"""
import os
import json
import logging


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path=None):
        # 获取项目根目录
        if config_path is None:
            # 从当前文件位置计算项目根目录
            # src/utils/config_manager.py -> src/utils -> src -> project_root
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            config_path = os.path.join(project_root, 'config', 'config.json')
        
        self.config_path = config_path
        # 先初始化 logger，因为 _load_config() 中可能会使用它
        self.logger = logging.getLogger('ConfigManager')
        self.config = self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        default_config = {
            "window": {
                "size": "800x600",
                "min_size": [800, 600],
                "title": "Bestdori 多功能工具"
            },
            "theme": {
                "name": "default",
                "font_family": "微软雅黑",
                "font_sizes": {
                    "small": 9,
                    "normal": 10,
                    "large": 12,
                    "title": 16
                }
            },
            "language": "zh_CN",
            "paths": {
                "downloads": "",  # 下载根路径
                "cache": "",
                "logs": ""
            },
            "download": {
                "default_speed": 1.0,
                "max_speed": 5.0,
                "min_speed": 0.1,
                "timeout": 10
            }
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并默认配置和加载的配置
                    default_config.update(loaded_config)
                    # 确保 paths 字段存在
                    if 'paths' not in default_config:
                        default_config['paths'] = {}
                    if 'downloads' not in default_config['paths']:
                        default_config['paths']['downloads'] = ""
            else:
                # 如果配置文件不存在，创建默认配置
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, ensure_ascii=False, indent=4)
                # 只有在 logger 已初始化时才记录日志
                if hasattr(self, 'logger') and self.logger:
                    self.logger.info(f"创建默认配置文件: {self.config_path}")
        except Exception as e:
            # 只有在 logger 已初始化时才记录日志，否则使用 print
            if hasattr(self, 'logger') and self.logger:
                self.logger.error(f"加载配置文件失败: {e}，使用默认配置")
            else:
                print(f"警告: 加载配置文件失败: {e}，使用默认配置")
        
        return default_config
    
    def save_config(self):
        """保存配置到文件"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            self.logger.info(f"配置已保存: {self.config_path}")
            return True
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
            return False
    
    def get_download_root_path(self):
        """获取下载根路径"""
        path = self.config.get('paths', {}).get('downloads', '')
        if not path:
            # 如果未设置，返回默认路径（用户主目录）
            return os.path.expanduser("~")
        return path
    
    def set_download_root_path(self, path):
        """设置下载根路径"""
        if 'paths' not in self.config:
            self.config['paths'] = {}
        self.config['paths']['downloads'] = path
        return self.save_config()
    
    def get(self, key, default=None):
        """获取配置值（支持点号分隔的键路径）"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value if value is not None else default
    
    def set(self, key, value):
        """设置配置值（支持点号分隔的键路径）"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        return self.save_config()


# 全局配置管理器实例
_config_manager = None

def get_config_manager():
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

