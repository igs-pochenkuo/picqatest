"""
工具函數模組
提供各種輔助功能函數
"""

import os
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from PIL import Image

def get_supported_image_files(directory: str, supported_formats: List[str]) -> List[str]:
    """
    取得目錄中所有支援的圖片檔案
    
    Args:
        directory (str): 目錄路徑
        supported_formats (List[str]): 支援的檔案格式列表
        
    Returns:
        List[str]: 圖片檔案路徑列表
    """
    image_files = []
    directory_path = Path(directory)
    
    if not directory_path.exists():
        return image_files
    
    for file_path in directory_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in supported_formats:
            image_files.append(str(file_path))
    
    return sorted(image_files)

def generate_cache_key(image_path: str, prompt: str) -> str:
    """
    為圖片和 prompt 組合生成快取鍵
    
    Args:
        image_path (str): 圖片路徑
        prompt (str): 文字提示
        
    Returns:
        str: 快取鍵
    """
    combined_string = f"{image_path}_{prompt}"
    return hashlib.md5(combined_string.encode()).hexdigest()

def save_results_to_json(results: Dict[str, Any], output_path: str) -> bool:
    """
    將結果儲存為 JSON 檔案
    
    Args:
        results (Dict[str, Any]): 結果資料
        output_path (str): 輸出檔案路徑
        
    Returns:
        bool: 是否成功儲存
    """
    try:
        # 確保輸出目錄存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 添加時間戳記
        results['timestamp'] = datetime.now().isoformat()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"儲存 JSON 檔案時發生錯誤: {e}")
        return False

def load_results_from_json(file_path: str) -> Dict[str, Any]:
    """
    從 JSON 檔案載入結果
    
    Args:
        file_path (str): JSON 檔案路徑
        
    Returns:
        Dict[str, Any]: 結果資料
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"載入 JSON 檔案時發生錯誤: {e}")
        return {}

def resize_image_if_needed(image: Image.Image, max_size: int) -> Image.Image:
    """
    如果需要的話調整圖片大小
    
    Args:
        image (Image.Image): PIL 圖片物件
        max_size (int): 最大尺寸
        
    Returns:
        Image.Image: 調整後的圖片
    """
    width, height = image.size
    
    if max(width, height) > max_size:
        if width > height:
            new_width = max_size
            new_height = int(height * max_size / width)
        else:
            new_height = max_size
            new_width = int(width * max_size / height)
        
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    return image

def format_similarity_score(score: float, precision: int = 4) -> str:
    """
    格式化相似度分數
    
    Args:
        score (float): 相似度分數
        precision (int): 小數點位數
        
    Returns:
        str: 格式化後的分數字串
    """
    return f"{score:.{precision}f}"

def get_file_size_mb(file_path: str) -> float:
    """
    取得檔案大小（MB）
    
    Args:
        file_path (str): 檔案路徑
        
    Returns:
        float: 檔案大小（MB）
    """
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except OSError:
        return 0.0

def create_timestamp_filename(prefix: str, extension: str) -> str:
    """
    創建帶時間戳記的檔案名稱
    
    Args:
        prefix (str): 檔案名稱前綴
        extension (str): 副檔名
        
    Returns:
        str: 檔案名稱
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"

def validate_directory(directory_path: str) -> tuple[bool, str]:
    """
    驗證目錄是否有效
    
    Args:
        directory_path (str): 目錄路徑
        
    Returns:
        tuple[bool, str]: (是否有效, 錯誤訊息)
    """
    if not directory_path:
        return False, "請選擇一個目錄"
    
    path = Path(directory_path)
    
    if not path.exists():
        return False, "目錄不存在"
    
    if not path.is_dir():
        return False, "路徑不是目錄"
    
    return True, ""

def calculate_statistics(scores: List[float]) -> Dict[str, float]:
    """
    計算相似度分數的統計資料
    
    Args:
        scores (List[float]): 相似度分數列表
        
    Returns:
        Dict[str, float]: 統計資料
    """
    if not scores:
        return {
            'count': 0,
            'mean': 0.0,
            'median': 0.0,
            'min': 0.0,
            'max': 0.0,
            'std': 0.0
        }
    
    import statistics
    
    return {
        'count': len(scores),
        'mean': statistics.mean(scores),
        'median': statistics.median(scores),
        'min': min(scores),
        'max': max(scores),
        'std': statistics.stdev(scores) if len(scores) > 1 else 0.0
    } 