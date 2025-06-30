"""
Ollama 多模態驗證引擎
處理與 Ollama API 的通訊和圖片現實性驗證
"""

import requests
import json
import base64
import time
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from PIL import Image
import io

from .config import config


class OllamaValidator:
    """Ollama 多模態驗證器"""
    
    def __init__(self):
        """初始化驗證器"""
        self.api_url = config.get('ollama.api_url', 'http://localhost:11434')
        self.model_name = config.get('ollama.model_name', 'phi4-mini')
        self.timeout = config.get('ollama.timeout', 30)
        self.default_prompt = config.get('ollama.default_prompt', '')
        
        # 驗證統計
        self.stats = {
            'total_validated': 0,
            'normal_count': 0,
            'abnormal_count': 0,
            'error_count': 0,
            'total_time': 0.0
        }
    
    def check_connection(self) -> Dict[str, Any]:
        """
        檢查 Ollama 服務連線狀態
        
        Returns:
            Dict[str, Any]: 連線狀態資訊
        """
        try:
            # 檢查服務狀態
            response = requests.get(f"{self.api_url}/api/tags", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                models = [model['name'] for model in data.get('models', [])]
                
                # 檢查目標模型是否存在
                model_available = any(self.model_name in model for model in models)
                
                return {
                    'connected': True,
                    'message': f"服務正常，發現 {len(models)} 個模型",
                    'models': models,
                    'target_model_available': model_available,
                    'target_model': self.model_name
                }
            else:
                return {
                    'connected': False,
                    'message': f"HTTP {response.status_code}",
                    'models': [],
                    'target_model_available': False
                }
                
        except requests.exceptions.ConnectionError:
            return {
                'connected': False,
                'message': "無法連接到 Ollama 服務",
                'models': [],
                'target_model_available': False
            }
        except requests.exceptions.Timeout:
            return {
                'connected': False,
                'message': "連線超時",
                'models': [],
                'target_model_available': False
            }
        except Exception as e:
            return {
                'connected': False,
                'message': f"未知錯誤: {str(e)}",
                'models': [],
                'target_model_available': False
            }
    
    def encode_image_to_base64(self, image_path: str) -> Optional[str]:
        """
        將圖片編碼為 base64
        
        Args:
            image_path (str): 圖片路徑
            
        Returns:
            Optional[str]: base64 編碼的圖片，失敗返回 None
        """
        try:
            # 開啟並處理圖片
            with Image.open(image_path) as img:
                # 轉換為 RGB 模式（如果不是的話）
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 限制圖片大小以提高處理速度
                max_size = config.get('processing.max_image_size', 1024)
                if max(img.size) > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # 轉換為 base64
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                return img_base64
                
        except Exception as e:
            print(f"圖片編碼失敗 {image_path}: {str(e)}")
            return None
    
    def validate_single_image(self, 
                            image_path: str, 
                            prompt: str = None,
                            custom_settings: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        驗證單張圖片
        
        Args:
            image_path (str): 圖片路徑
            prompt (str, optional): 自定義 prompt
            custom_settings (Dict[str, Any], optional): 自定義設定
            
        Returns:
            Dict[str, Any]: 驗證結果
        """
        start_time = time.time()
        image_name = Path(image_path).name
        
        # 預設結果結構
        result = {
            'image_path': image_path,
            'image_name': image_name,
            'status': 'error',
            'confidence': 0.0,
            'details': '',
            'issues': {
                'physics': [],
                'watermarks': [],
                'quality': []
            },
            'processing_time': 0.0,
            'raw_response': ''
        }
        
        try:
            # 編碼圖片
            img_base64 = self.encode_image_to_base64(image_path)
            if not img_base64:
                result['details'] = '圖片編碼失敗'
                return result
            
            # 準備 prompt
            if prompt is None:
                prompt = self.default_prompt
            
            # 格式化 prompt
            formatted_prompt = prompt.format(image_name=image_name)
            
            # 準備 API 請求
            payload = {
                "model": self.model_name,
                "prompt": formatted_prompt,
                "images": [img_base64],
                "stream": False
            }
            
            # 發送請求
            response = requests.post(
                f"{self.api_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                result['details'] = f"API 請求失敗: HTTP {response.status_code}"
                return result
            
            # 解析回應
            response_data = response.json()
            raw_response = response_data.get('response', '')
            result['raw_response'] = raw_response
            
            # 嘗試解析 JSON 回應
            parsed_result = self.parse_ollama_response(raw_response)
            
            if parsed_result:
                result.update(parsed_result)
                result['status'] = parsed_result.get('status', 'error')
            else:
                result['details'] = '無法解析 Ollama 回應'
                result['status'] = 'error'
            
        except requests.exceptions.Timeout:
            result['details'] = '請求超時'
        except requests.exceptions.ConnectionError:
            result['details'] = '連線錯誤'
        except Exception as e:
            result['details'] = f'驗證過程發生錯誤: {str(e)}'
        
        finally:
            # 記錄處理時間
            result['processing_time'] = time.time() - start_time
            
            # 更新統計
            self.update_stats(result)
        
        return result
    
    def parse_ollama_response(self, raw_response: str) -> Optional[Dict[str, Any]]:
        """
        解析 Ollama 的回應
        
        Args:
            raw_response (str): 原始回應文字
            
        Returns:
            Optional[Dict[str, Any]]: 解析後的結果，失敗返回 None
        """
        try:
            # 嘗試直接解析 JSON
            if raw_response.strip().startswith('{'):
                return json.loads(raw_response.strip())
            
            # 尋找 JSON 區塊 - 改良版本支援不同格式
            # 先嘗試從 ```json 標記中提取
            if '```json' in raw_response:
                start_idx = raw_response.find('```json') + 7
                end_idx = raw_response.find('```', start_idx)
                if end_idx > start_idx:
                    json_str = raw_response[start_idx:end_idx].strip()
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        pass
            
            # 原有的行解析邏輯作為備用
            lines = raw_response.split('\n')
            json_lines = []
            in_json = False
            
            for line in lines:
                line = line.strip()
                if line.startswith('{'):
                    in_json = True
                    json_lines.append(line)
                elif in_json:
                    json_lines.append(line)
                    if line.endswith('}'):
                        break
            
            if json_lines:
                json_str = '\n'.join(json_lines)
                return json.loads(json_str)
            
            # 如果找不到 JSON，嘗試從回應中提取資訊
            return self.extract_info_from_text(raw_response)
            
        except json.JSONDecodeError:
            # JSON 解析失敗，嘗試從文字中提取資訊
            return self.extract_info_from_text(raw_response)
        except Exception:
            return None
    
    def extract_info_from_text(self, text: str) -> Dict[str, Any]:
        """
        從文字回應中提取資訊（當 JSON 解析失敗時的備用方案）
        
        Args:
            text (str): 回應文字
            
        Returns:
            Dict[str, Any]: 提取的資訊
        """
        text_lower = text.lower()
        
        # 判斷狀態（避免誤判 JSON 格式回應中的關鍵字）
        # 如果包含 JSON 標記，不使用關鍵字檢測
        if 'json' in text_lower and ('status' in text_lower or 'confidence' in text_lower):
            # 包含 JSON 結構，使用預設值讓上級解析
            status = 'normal'
            confidence = 0.7
        elif any(word in text_lower for word in ['abnormal', 'unrealistic', 'impossible', 'floating']):
            # 只在非 JSON 回應中使用關鍵字檢測，且移除 'watermark' 避免誤判
            status = 'abnormal'
            confidence = 0.6
        else:
            status = 'normal'
            confidence = 0.7
        
        return {
            'status': status,
            'confidence': confidence,
            'details': text[:200] + '...' if len(text) > 200 else text,
            'issues': {
                'physics': [],
                'watermarks': [],
                'quality': []
            }
        }
    
    def validate_batch_images(self, 
                            image_paths: List[str],
                            prompt: str = None,
                            progress_callback: Optional[Callable] = None,
                            custom_settings: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        批次驗證圖片
        
        Args:
            image_paths (List[str]): 圖片路徑列表
            prompt (str, optional): 自定義 prompt
            progress_callback (Optional[Callable], optional): 進度回調函數
            custom_settings (Dict[str, Any], optional): 自定義設定
            
        Returns:
            List[Dict[str, Any]]: 驗證結果列表
        """
        results = []
        total_images = len(image_paths)
        
        for i, image_path in enumerate(image_paths):
            # 更新進度
            if progress_callback:
                progress = (i + 1) / total_images
                progress_callback(progress, f"驗證圖片 {i + 1}/{total_images}: {Path(image_path).name}")
            
            # 驗證單張圖片
            result = self.validate_single_image(image_path, prompt, custom_settings)
            results.append(result)
        
        return results
    
    def update_stats(self, result: Dict[str, Any]):
        """
        更新驗證統計
        
        Args:
            result (Dict[str, Any]): 驗證結果
        """
        self.stats['total_validated'] += 1
        self.stats['total_time'] += result.get('processing_time', 0)
        
        status = result.get('status', 'error')
        if status == 'normal':
            self.stats['normal_count'] += 1
        elif status == 'abnormal':
            self.stats['abnormal_count'] += 1
        else:
            self.stats['error_count'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """
        取得驗證統計資訊
        
        Returns:
            Dict[str, Any]: 統計資訊
        """
        stats = self.stats.copy()
        
        # 計算平均處理時間
        if stats['total_validated'] > 0:
            stats['avg_processing_time'] = stats['total_time'] / stats['total_validated']
        else:
            stats['avg_processing_time'] = 0.0
        
        return stats
    
    def reset_stats(self):
        """重置統計資訊"""
        self.stats = {
            'total_validated': 0,
            'normal_count': 0,
            'abnormal_count': 0,
            'error_count': 0,
            'total_time': 0.0
        } 