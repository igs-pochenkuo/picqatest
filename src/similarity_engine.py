"""
核心相似度計算引擎
使用 CLIP 模型計算圖片與文字的相似度
"""

import torch
import open_clip
from PIL import Image
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from pathlib import Path
import pickle
import os

from .config import config
from .utils import generate_cache_key, resize_image_if_needed

class SimilarityEngine:
    """相似度計算引擎"""
    
    def __init__(self):
        """初始化相似度引擎"""
        self.model = None
        self.preprocess = None
        self.tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.cache_enabled = config.get('cache.enabled', True)
        self.cache_dir = config.get('cache.cache_dir', 'data/cache')
        self._cache = {}
        
        # 確保快取目錄存在
        if self.cache_enabled:
            Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
    
    def initialize_model(self) -> bool:
        """
        初始化 CLIP 模型
        
        Returns:
            bool: 是否成功初始化
        """
        try:
            model_name = config.get('model.name', 'ViT-B-32')
            pretrained = config.get('model.pretrained', 'laion2b_s34b_b79k')
            
            print(f"正在載入模型: {model_name} ({pretrained})")
            
            # 載入模型
            self.model, _, self.preprocess = open_clip.create_model_and_transforms(
                model_name, 
                pretrained=pretrained,
                device=self.device
            )
            self.tokenizer = open_clip.get_tokenizer(model_name)
            
            # 設置為評估模式
            self.model.eval()
            
            print(f"模型已載入到設備: {self.device}")
            return True
            
        except Exception as e:
            print(f"載入模型時發生錯誤: {e}")
            return False
    
    def _load_cache(self):
        """載入快取"""
        if not self.cache_enabled:
            return
        
        cache_file = os.path.join(self.cache_dir, 'similarity_cache.pkl')
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'rb') as f:
                    self._cache = pickle.load(f)
                print(f"已載入 {len(self._cache)} 個快取項目")
        except Exception as e:
            print(f"載入快取時發生錯誤: {e}")
            self._cache = {}
    
    def _save_cache(self):
        """儲存快取"""
        if not self.cache_enabled:
            return
        
        cache_file = os.path.join(self.cache_dir, 'similarity_cache.pkl')
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(self._cache, f)
        except Exception as e:
            print(f"儲存快取時發生錯誤: {e}")
    
    def _get_cached_similarity(self, image_path: str, prompt: str) -> Optional[float]:
        """
        從快取取得相似度
        
        Args:
            image_path (str): 圖片路徑
            prompt (str): 文字提示
            
        Returns:
            Optional[float]: 快取的相似度分數，如果沒有則返回 None
        """
        if not self.cache_enabled:
            return None
        
        cache_key = generate_cache_key(image_path, prompt)
        return self._cache.get(cache_key)
    
    def _set_cached_similarity(self, image_path: str, prompt: str, similarity: float):
        """
        設置快取的相似度
        
        Args:
            image_path (str): 圖片路徑
            prompt (str): 文字提示
            similarity (float): 相似度分數
        """
        if not self.cache_enabled:
            return
        
        cache_key = generate_cache_key(image_path, prompt)
        self._cache[cache_key] = similarity
    
    def preprocess_image(self, image_path: str) -> Optional[torch.Tensor]:
        """
        預處理圖片
        
        Args:
            image_path (str): 圖片路徑
            
        Returns:
            Optional[torch.Tensor]: 預處理後的圖片張量
        """
        try:
            # 載入圖片
            image = Image.open(image_path).convert('RGB')
            
            # 如果需要的話調整大小
            max_size = config.get('processing.max_image_size', 1024)
            image = resize_image_if_needed(image, max_size)
            
            # 預處理
            image_tensor = self.preprocess(image).unsqueeze(0)
            return image_tensor.to(self.device)
            
        except Exception as e:
            print(f"預處理圖片 {image_path} 時發生錯誤: {e}")
            return None
    
    def preprocess_text(self, prompt: str) -> Optional[torch.Tensor]:
        """
        預處理文字
        
        Args:
            prompt (str): 文字提示
            
        Returns:
            Optional[torch.Tensor]: 預處理後的文字張量
        """
        try:
            text_tensor = self.tokenizer([prompt])
            return text_tensor.to(self.device)
        except Exception as e:
            print(f"預處理文字時發生錯誤: {e}")
            return None
    
    def calculate_similarity(self, image_path: str, prompt: str) -> Optional[float]:
        """
        計算單張圖片與文字的相似度
        
        Args:
            image_path (str): 圖片路徑
            prompt (str): 文字提示
            
        Returns:
            Optional[float]: 相似度分數 (0-1)
        """
        # 檢查快取
        cached_similarity = self._get_cached_similarity(image_path, prompt)
        if cached_similarity is not None:
            return cached_similarity
        
        # 檢查模型是否已初始化
        if self.model is None:
            print("模型尚未初始化")
            return None
        
        try:
            # 預處理圖片和文字
            image_tensor = self.preprocess_image(image_path)
            text_tensor = self.preprocess_text(prompt)
            
            if image_tensor is None or text_tensor is None:
                return None
            
            # 計算相似度
            with torch.no_grad():
                image_features = self.model.encode_image(image_tensor)
                text_features = self.model.encode_text(text_tensor)
                
                # 正規化特徵向量
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                
                # 計算餘弦相似度
                similarity = torch.cosine_similarity(image_features, text_features).item()
            
            # 快取結果
            self._set_cached_similarity(image_path, prompt, similarity)
            
            return similarity
            
        except Exception as e:
            print(f"計算相似度時發生錯誤: {e}")
            return None
    
    def calculate_batch_similarity(self, image_paths: List[str], prompt: str, 
                                 progress_callback=None) -> List[Dict[str, Any]]:
        """
        批次計算多張圖片與文字的相似度
        
        Args:
            image_paths (List[str]): 圖片路徑列表
            prompt (str): 文字提示
            progress_callback: 進度回調函數
            
        Returns:
            List[Dict[str, Any]]: 結果列表
        """
        results = []
        total_images = len(image_paths)
        
        # 載入快取
        self._load_cache()
        
        for i, image_path in enumerate(image_paths):
            try:
                similarity = self.calculate_similarity(image_path, prompt)
                
                result = {
                    'image_path': image_path,
                    'prompt': prompt,
                    'similarity_score': similarity,
                    'image_name': Path(image_path).name,
                    'success': similarity is not None
                }
                
                results.append(result)
                
                # 呼叫進度回調
                if progress_callback:
                    progress = (i + 1) / total_images
                    progress_callback(progress, f"處理中: {result['image_name']}")
                    
            except Exception as e:
                print(f"處理圖片 {image_path} 時發生錯誤: {e}")
                results.append({
                    'image_path': image_path,
                    'prompt': prompt,
                    'similarity_score': None,
                    'image_name': Path(image_path).name,
                    'success': False,
                    'error': str(e)
                })
        
        # 儲存快取
        self._save_cache()
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        取得模型資訊
        
        Returns:
            Dict[str, Any]: 模型資訊
        """
        return {
            'model_name': config.get('model.name', 'ViT-B-32'),
            'pretrained': config.get('model.pretrained', 'laion2b_s34b_b79k'),
            'device': str(self.device),
            'cache_enabled': self.cache_enabled,
            'cache_size': len(self._cache) if self.cache_enabled else 0
        }
    
    def clear_cache(self):
        """清除快取"""
        self._cache = {}
        cache_file = os.path.join(self.cache_dir, 'similarity_cache.pkl')
        if os.path.exists(cache_file):
            os.remove(cache_file)
        print("快取已清除")
    
    def __del__(self):
        """析構函數，儲存快取"""
        if hasattr(self, '_cache') and self.cache_enabled:
            self._save_cache() 