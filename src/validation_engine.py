"""
整合驗證引擎
結合 CLIP 相似度分析和 Ollama 現實性驗證的二階段驗證系統
"""

from typing import Dict, List, Optional, Callable, Any
from pathlib import Path
import time

from similarity_engine import SimilarityEngine
from ollama_validator import OllamaValidator
from config import config


class ValidationEngine:
    """整合驗證引擎"""
    
    def __init__(self):
        """初始化驗證引擎"""
        self.similarity_engine = None
        self.ollama_validator = None
        self.initialized = False
        
        # 驗證設定
        self.settings = {
            'ollama_enabled': False,
            'verification_threshold': config.get('ollama.verification_threshold', 0.6),
            'confidence_threshold': config.get('ollama.confidence_threshold', 0.7),
            'custom_prompt': None
        }
        
        # 統計資訊
        self.stats = {
            'total_images': 0,
            'clip_success': 0,
            'clip_failed': 0,
            'ollama_validated': 0,
            'ollama_skipped': 0,
            'final_accepted': 0,
            'final_rejected': 0
        }
    
    def initialize(self) -> bool:
        """
        初始化驗證引擎
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 初始化 CLIP 引擎
            self.similarity_engine = SimilarityEngine()
            if not self.similarity_engine.initialize_model():
                return False
            
            # 初始化 Ollama 驗證器
            self.ollama_validator = OllamaValidator()
            
            self.initialized = True
            return True
            
        except Exception as e:
            print(f"驗證引擎初始化失敗: {str(e)}")
            return False
    
    def update_settings(self, new_settings: Dict[str, Any]):
        """
        更新驗證設定
        
        Args:
            new_settings (Dict[str, Any]): 新的設定
        """
        self.settings.update(new_settings)
    
    def analyze_with_validation(self, 
                              image_paths: List[str], 
                              prompt: str,
                              progress_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """
        執行二階段驗證分析
        
        Args:
            image_paths (List[str]): 圖片路徑列表
            prompt (str): 文字提示
            progress_callback (Optional[Callable], optional): 進度回調函數
            
        Returns:
            List[Dict[str, Any]]: 驗證結果列表
        """
        if not self.initialized:
            raise RuntimeError("驗證引擎尚未初始化")
        
        results = []
        total_images = len(image_paths)
        self.stats['total_images'] = total_images
        
        # 階段一：CLIP 相似度分析
        if progress_callback:
            progress_callback(0.0, "開始 CLIP 相似度分析...")
        
        def clip_progress_callback(progress, message):
            # CLIP 階段佔總進度的 40%
            if progress_callback:
                progress_callback(progress * 0.4, f"CLIP 分析: {message}")
        
        clip_results = self.similarity_engine.calculate_batch_similarity(
            image_paths, prompt, clip_progress_callback
        )
        
        # 處理 CLIP 結果並準備二階段驗證
        images_for_validation = []
        
        for i, result in enumerate(clip_results):
            # 基本結果結構
            enhanced_result = {
                'image_path': result['image_path'],
                'image_name': Path(result['image_path']).name,
                'prompt': prompt,
                'similarity_score': result.get('similarity_score', 0.0),
                'clip_status': 'success' if result.get('success', False) else 'failed',
                'ollama_validation': {
                    'enabled': self.settings['ollama_enabled'],
                    'status': 'skipped',
                    'confidence': 0.0,
                    'details': '',
                    'issues': {
                        'physics': [],
                        'watermarks': [],
                        'quality': []
                    },
                    'processing_time': 0.0
                },
                'final_status': 'pending'
            }
            
            # 更新 CLIP 統計
            if enhanced_result['clip_status'] == 'success':
                self.stats['clip_success'] += 1
            else:
                self.stats['clip_failed'] += 1
            
            results.append(enhanced_result)
            
            # 判斷是否需要進行 Ollama 驗證
            if (self.settings['ollama_enabled'] and 
                enhanced_result['clip_status'] == 'success' and
                enhanced_result['similarity_score'] >= self.settings['verification_threshold']):
                images_for_validation.append(i)  # 記錄索引
        
        # 階段二：Ollama 現實性驗證
        if self.settings['ollama_enabled'] and images_for_validation:
            if progress_callback:
                progress_callback(0.4, f"開始 Ollama 現實性驗證 ({len(images_for_validation)} 張圖片)...")
            
            # 檢查 Ollama 連線
            connection_status = self.ollama_validator.check_connection()
            if not connection_status['connected']:
                # Ollama 無法連線，標記所有需要驗證的圖片
                for idx in images_for_validation:
                    results[idx]['ollama_validation']['status'] = 'error'
                    results[idx]['ollama_validation']['details'] = connection_status['message']
                    self.stats['ollama_skipped'] += 1
            else:
                # 執行 Ollama 驗證
                validation_prompt = self.settings.get('custom_prompt') or self.ollama_validator.default_prompt
                
                for i, result_idx in enumerate(images_for_validation):
                    # 更新進度
                    if progress_callback:
                        progress = 0.4 + (i + 1) / len(images_for_validation) * 0.6
                        image_name = results[result_idx]['image_name']
                        progress_callback(progress, f"Ollama 驗證: {i + 1}/{len(images_for_validation)} - {image_name}")
                    
                    # 驗證單張圖片
                    image_path = results[result_idx]['image_path']
                    validation_result = self.ollama_validator.validate_single_image(
                        image_path, validation_prompt
                    )
                    
                    # 更新結果
                    results[result_idx]['ollama_validation'].update({
                        'status': validation_result['status'],
                        'confidence': validation_result['confidence'],
                        'details': validation_result['details'],
                        'issues': validation_result['issues'],
                        'processing_time': validation_result['processing_time']
                    })
                    
                    self.stats['ollama_validated'] += 1
        
        # 決定最終狀態
        for result in results:
            result['final_status'] = self.determine_final_status(result)
            
            # 更新最終統計
            if result['final_status'] == 'accepted':
                self.stats['final_accepted'] += 1
            else:
                self.stats['final_rejected'] += 1
        
        if progress_callback:
            progress_callback(1.0, "驗證完成！")
        
        return results
    
    def determine_final_status(self, result: Dict[str, Any]) -> str:
        """
        決定最終驗證狀態
        
        Args:
            result (Dict[str, Any]): 驗證結果
            
        Returns:
            str: 最終狀態 ('accepted' 或 'rejected')
        """
        # CLIP 失敗直接拒絕
        if result['clip_status'] != 'success':
            return 'rejected'
        
        # 如果沒有啟用 Ollama，只依據 CLIP 結果
        if not self.settings['ollama_enabled']:
            return 'accepted'
        
        # 相似度低於門檻，跳過 Ollama 驗證但接受
        if result['similarity_score'] < self.settings['verification_threshold']:
            return 'accepted'
        
        # 檢查 Ollama 驗證結果
        ollama_status = result['ollama_validation']['status']
        ollama_confidence = result['ollama_validation']['confidence']
        
        # Ollama 驗證失敗或錯誤，降級為只看 CLIP 結果
        if ollama_status in ['error', 'skipped']:
            return 'accepted'
        
        # Ollama 判定為異常
        if ollama_status == 'abnormal':
            # 檢查信心度是否足夠
            if ollama_confidence >= self.settings['confidence_threshold']:
                return 'rejected'
            else:
                # 信心度不足，接受圖片
                return 'accepted'
        
        # Ollama 判定為正常
        return 'accepted'
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """
        取得驗證摘要
        
        Returns:
            Dict[str, Any]: 驗證摘要
        """
        summary = {
            'settings': self.settings.copy(),
            'stats': self.stats.copy(),
            'ollama_stats': None
        }
        
        # 加入 Ollama 統計（如果可用）
        if self.ollama_validator:
            summary['ollama_stats'] = self.ollama_validator.get_stats()
        
        return summary
    
    def reset_stats(self):
        """重置統計資訊"""
        self.stats = {
            'total_images': 0,
            'clip_success': 0,
            'clip_failed': 0,
            'ollama_validated': 0,
            'ollama_skipped': 0,
            'final_accepted': 0,
            'final_rejected': 0
        }
        
        if self.ollama_validator:
            self.ollama_validator.reset_stats()
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        取得模型資訊
        
        Returns:
            Dict[str, Any]: 模型資訊
        """
        info = {
            'initialized': self.initialized,
            'clip_model': None,
            'ollama_status': None
        }
        
        if self.similarity_engine:
            info['clip_model'] = self.similarity_engine.get_model_info()
        
        if self.ollama_validator:
            info['ollama_status'] = self.ollama_validator.check_connection()
        
        return info 