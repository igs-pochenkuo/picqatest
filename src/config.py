"""
配置管理模組
負責載入和管理應用程式配置
"""

import yaml
import os
from pathlib import Path

class Config:
    """配置管理類別"""
    
    def __init__(self, config_path="config.yaml"):
        """
        初始化配置管理器
        
        Args:
            config_path (str): 配置檔案路徑
        """
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self):
        """載入配置檔案"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            print(f"配置檔案 {self.config_path} 不存在，使用預設配置")
            return self._get_default_config()
        except Exception as e:
            print(f"載入配置檔案時發生錯誤: {e}")
            return self._get_default_config()
    
    def _get_default_config(self):
        """取得預設配置"""
        return {
            'app': {
                'title': "PictureQA Demo - 圖片與文字相似度分析工具",
                'page_icon': "🖼️",
                'layout': "wide"
            },
            'model': {
                'name': "ViT-B-32",
                'pretrained': "laion2b_s34b_b79k"
            },
            'processing': {
                'batch_size': 32,
                'supported_formats': [".png", ".jpg", ".jpeg", ".bmp", ".tiff"],
                'max_image_size': 1024
            },
            'ui': {
                'similarity_threshold_default': 0.5,
                'similarity_threshold_min': 0.0,
                'similarity_threshold_max': 1.0,
                'similarity_threshold_step': 0.01,
                'images_per_row': 4,
                'max_images_display': 100
            },
            'cache': {
                'enabled': True,
                'cache_dir': "data/cache"
            },
            'export': {
                'results_dir': "data/results",
                'exports_dir': "data/exports"
            }
        }
    
    def get(self, key_path, default=None):
        """
        取得配置值
        
        Args:
            key_path (str): 配置鍵路徑，使用點號分隔 (例如: 'app.title')
            default: 預設值
            
        Returns:
            配置值
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def ensure_directories(self):
        """確保所需目錄存在"""
        dirs_to_create = [
            self.get('cache.cache_dir'),
            self.get('export.results_dir'),
            self.get('export.exports_dir')
        ]
        
        for dir_path in dirs_to_create:
            if dir_path:
                Path(dir_path).mkdir(parents=True, exist_ok=True)

# 全域配置實例
config = Config() 