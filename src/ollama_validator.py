"""
Ollama 多模態驗證引擎
處理與 Ollama API 的通訊和圖片現實性驗證
"""

import requests
import json
import base64
import time
import subprocess
import psutil
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from PIL import Image
import io

from config import config


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
            # 檢查服務狀態 (使用 session 管理連接)
            with requests.Session() as session:
                response = session.get(f"{self.api_url}/api/tags", timeout=5)
            
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
            
            # 發送請求 (使用 session 來確保連接被正確管理)
            with requests.Session() as session:
                response = session.post(
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

    def stop(self, force: bool = False, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        停止 Ollama 服務 (簡化版本，用於快速調用)
        
        Args:
            force (bool): 是否強制終止，預設為 False（優雅關閉）
            progress_callback (Optional[Callable], optional): 進度回調函數
            
        Returns:
            Dict[str, Any]: 停止操作結果
        """
        return self.stop_ollama(force=force, progress_callback=progress_callback)

    def start_service(self, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        啟動 Ollama 服務 (對外接口)
        
        Args:
            progress_callback (Optional[Callable], optional): 進度回調函數
            
        Returns:
            Dict[str, Any]: 啟動操作結果
        """
        result = {
            'success': False,
            'message': '',
            'method_used': '',
            'connection_status': None
        }
        
        try:
            if progress_callback:
                progress_callback(0.1, "檢查 Ollama 服務狀態...")
            
            # 第一步：檢查服務是否已經在運行
            connection_status = self.check_connection()
            result['connection_status'] = connection_status
            
            if connection_status['connected']:
                result.update({
                    'success': True,
                    'message': f'Ollama 服務已在運行。{connection_status["message"]}',
                    'method_used': 'already_running'
                })
                if progress_callback:
                    progress_callback(1.0, "服務已在運行")
                return result
            
            if progress_callback:
                progress_callback(0.2, "服務未運行，準備啟動...")
            
            # 第二步：嘗試啟動服務
            startup_success = self._start_ollama_service(progress_callback)
            
            if startup_success:
                # 第三步：再次檢查連接狀態
                if progress_callback:
                    progress_callback(0.95, "驗證服務啟動狀態...")
                
                final_connection = self.check_connection()
                result['connection_status'] = final_connection
                
                if final_connection['connected']:
                    result.update({
                        'success': True,
                        'message': f'Ollama 服務啟動成功！{final_connection["message"]}',
                        'method_used': 'started'
                    })
                else:
                    result.update({
                        'success': False,
                        'message': f'服務啟動但連接檢查失敗: {final_connection["message"]}',
                        'method_used': 'started_but_not_connected'
                    })
            else:
                result.update({
                    'success': False,
                    'message': '無法啟動 Ollama 服務。請檢查 Ollama 是否正確安裝',
                    'method_used': 'failed_to_start'
                })
            
            if progress_callback:
                progress_callback(1.0, "啟動操作完成")
                
        except Exception as e:
            result.update({
                'success': False,
                'message': f'啟動 Ollama 時發生錯誤: {str(e)}',
                'method_used': 'error'
            })
            
            if progress_callback:
                progress_callback(1.0, f"啟動操作失敗: {str(e)}")
        
        return result

    def stop_ollama(self, force: bool = False, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        停止 Ollama 服務
        
        Args:
            force (bool): 是否強制終止，預設為 False（優雅關閉）
            progress_callback (Optional[Callable], optional): 進度回調函數
            
        Returns:
            Dict[str, Any]: 停止操作結果
        """
        result = {
            'success': False,
            'message': '',
            'processes_found': 0,
            'processes_stopped': 0,
            'method_used': ''
        }
        
        try:
            if progress_callback:
                progress_callback(0.1, "正在搜尋 Ollama 進程...")
            
            # 第一步：檢查服務是否正在運行
            connection_status = self.check_connection()
            if not connection_status['connected']:
                result.update({
                    'success': True,
                    'message': 'Ollama 服務未運行或已經停止',
                    'method_used': 'not_running'
                })
                return result
            
            if progress_callback:
                progress_callback(0.2, "發現 Ollama 服務正在運行，開始停止程序...")
            
            # 第二步：尋找 Ollama 相關進程
            ollama_processes = []
            ollama_executables = ['ollama.exe', 'ollama', 'ollama app.exe', 'ollama serve']
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_info = proc.info
                    proc_name = proc_info['name'].lower() if proc_info['name'] else ''
                    proc_cmdline = ' '.join(proc_info['cmdline']).lower() if proc_info['cmdline'] else ''
                    
                    # 檢查是否為 Ollama 相關進程
                    if any(exec_name.lower() in proc_name for exec_name in ollama_executables) or \
                       any(exec_name.lower() in proc_cmdline for exec_name in ollama_executables):
                        ollama_processes.append(proc)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            result['processes_found'] = len(ollama_processes)
            
            if not ollama_processes:
                result.update({
                    'success': True,
                    'message': '沒有找到 Ollama 進程，可能已經停止',
                    'method_used': 'no_processes'
                })
                return result
            
            if progress_callback:
                progress_callback(0.4, f"找到 {len(ollama_processes)} 個 Ollama 進程，開始停止...")
            
            # 第三步：停止進程
            stopped_count = 0
            
            if not force:
                # 優雅關閉：先嘗試 SIGTERM
                if progress_callback:
                    progress_callback(0.5, "嘗試優雅關閉 Ollama 進程...")
                
                for i, proc in enumerate(ollama_processes):
                    try:
                        proc.terminate()  # 發送 SIGTERM
                        if progress_callback:
                            progress_callback(0.5 + (i + 1) / len(ollama_processes) * 0.2, 
                                            f"正在停止進程 {proc.pid}...")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # 等待進程優雅退出
                if progress_callback:
                    progress_callback(0.7, "等待進程退出...")
                
                time.sleep(3)
                
                # 檢查哪些進程已經停止
                remaining_processes = []
                for proc in ollama_processes:
                    try:
                        if proc.is_running():
                            remaining_processes.append(proc)
                        else:
                            stopped_count += 1
                    except psutil.NoSuchProcess:
                        stopped_count += 1
                
                ollama_processes = remaining_processes
                result['method_used'] = 'graceful'
            
            # 第四步：強制終止剩餘進程（如果需要）
            if ollama_processes and (force or len(ollama_processes) > 0):
                if progress_callback:
                    progress_callback(0.8, f"強制終止剩餘的 {len(ollama_processes)} 個進程...")
                
                for i, proc in enumerate(ollama_processes):
                    try:
                        proc.kill()  # 發送 SIGKILL
                        stopped_count += 1
                        if progress_callback:
                            progress_callback(0.8 + (i + 1) / len(ollama_processes) * 0.15, 
                                            f"強制停止進程 {proc.pid}...")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                if result['method_used'] == '':
                    result['method_used'] = 'forced'
                else:
                    result['method_used'] += '_then_forced'
                
                # 再等待一下
                time.sleep(1)
            
            result['processes_stopped'] = stopped_count
            
            # 第五步：最終驗證
            if progress_callback:
                progress_callback(0.95, "驗證服務是否已停止...")
            
            time.sleep(1)  # 給服務一點時間完全停止
            final_connection = self.check_connection()
            
            if not final_connection['connected']:
                result.update({
                    'success': True,
                    'message': f'Ollama 服務已成功停止。共處理 {result["processes_found"]} 個進程，停止了 {stopped_count} 個'
                })
            else:
                result.update({
                    'success': False,
                    'message': f'部分進程可能仍在運行。共找到 {result["processes_found"]} 個進程，停止了 {stopped_count} 個，但服務似乎仍可連接'
                })
            
            if progress_callback:
                progress_callback(1.0, "停止操作完成")
            
        except Exception as e:
            result.update({
                'success': False,
                'message': f'停止 Ollama 時發生錯誤: {str(e)}',
                'method_used': 'error'
            })
            
            if progress_callback:
                progress_callback(1.0, f"停止操作失敗: {str(e)}")
        
        return result

    def restart_ollama(self, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        重新啟動 Ollama 服務
        
        Args:
            progress_callback (Optional[Callable], optional): 進度回調函數
            
        Returns:
            Dict[str, Any]: 重啟操作結果
        """
        result = {
            'success': False,
            'message': '',
            'stop_result': None,
            'start_result': None
        }
        
        try:
            # 第一步：停止服務
            if progress_callback:
                def stop_progress(progress, message):
                    progress_callback(progress * 0.6, f"停止階段: {message}")
                
                stop_result = self.stop_ollama(force=False, progress_callback=stop_progress)
            else:
                stop_result = self.stop_ollama(force=False)
            
            result['stop_result'] = stop_result
            
            if not stop_result['success']:
                result['message'] = f"停止 Ollama 失敗: {stop_result['message']}"
                return result
            
            # 等待一下確保完全停止
            time.sleep(2)
            
            # 第二步：啟動服務
            if progress_callback:
                progress_callback(0.7, "開始啟動 Ollama 服務...")
            
            start_success = self._start_ollama_service(progress_callback)
            
            if start_success:
                result.update({
                    'success': True,
                    'message': 'Ollama 服務重啟成功'
                })
            else:
                result.update({
                    'success': False,
                    'message': 'Ollama 停止成功，但重新啟動失敗'
                })
            
        except Exception as e:
            result.update({
                'success': False,
                'message': f'重啟 Ollama 時發生錯誤: {str(e)}'
            })
        
        return result

    def _start_ollama_service(self, progress_callback: Optional[Callable] = None) -> bool:
        """
        啟動 Ollama 服務（內部方法）
        
        Args:
            progress_callback (Optional[Callable], optional): 進度回調函數
            
        Returns:
            bool: 啟動是否成功
        """
        try:
            # 檢查是否已經運行
            if progress_callback:
                progress_callback(0.8, "檢查服務狀態...")
            
            connection_status = self.check_connection()
            if connection_status['connected']:
                if progress_callback:
                    progress_callback(1.0, "服務已在運行")
                return True
            
            if progress_callback:
                progress_callback(0.85, "尋找 Ollama 執行檔...")
            
            # 尋找 Ollama 執行檔
            ollama_path = self._find_ollama_executable()
            if not ollama_path:
                return False
            
            if progress_callback:
                progress_callback(0.9, "啟動 Ollama 服務...")
            
            # 啟動服務
            if sys.platform == "win32":
                # Windows: 在背景啟動
                subprocess.Popen([ollama_path, "serve"], 
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                # Linux/Mac: 在背景啟動
                subprocess.Popen([ollama_path, "serve"], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
            
            # 等待服務啟動
            if progress_callback:
                progress_callback(0.95, "等待服務啟動...")
            
            for i in range(10):  # 最多等待 10 秒
                time.sleep(1)
                connection_status = self.check_connection()
                if connection_status['connected']:
                    if progress_callback:
                        progress_callback(1.0, "服務啟動成功")
                    return True
            
            return False
            
        except Exception as e:
            print(f"啟動 Ollama 服務失敗: {str(e)}")
            return False

    def _find_ollama_executable(self) -> Optional[str]:
        """
        尋找 Ollama 執行檔路徑
        
        Returns:
            Optional[str]: 執行檔路徑，找不到返回 None
        """
        # 常見的 Ollama 執行檔位置
        possible_paths = []
        
        if sys.platform == "win32":
            # Windows 路徑
            possible_paths.extend([
                "ollama.exe",
                "C:\\Program Files\\Ollama\\ollama.exe",
                "C:\\Program Files (x86)\\Ollama\\ollama.exe",
                os.path.join(os.path.expanduser("~"), "AppData", "Local", "Programs", "Ollama", "ollama.exe"),
            ])
        else:
            # Linux/Mac 路徑
            possible_paths.extend([
                "ollama",
                "/usr/local/bin/ollama",
                "/usr/bin/ollama",
                "/opt/ollama/bin/ollama",
                os.path.join(os.path.expanduser("~"), "bin", "ollama"),
            ])
        
        # 檢查每個可能的路徑
        for path in possible_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
        
        # 嘗試在 PATH 中尋找
        import shutil
        ollama_in_path = shutil.which("ollama")
        if ollama_in_path:
            return ollama_in_path
        
        return None 