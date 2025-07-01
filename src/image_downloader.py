#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
圖片下載處理模組
支援從 URL 下載圖片並進行基本驗證和預處理
"""

import requests
import tempfile
import os
from PIL import Image
import io
import logging
from typing import Optional, Tuple
from pathlib import Path
import hashlib
import time

logger = logging.getLogger(__name__)

class ImageDownloader:
    """圖片下載器"""
    
    def __init__(self, 
                 max_file_size: int = 50 * 1024 * 1024,  # 50MB
                 timeout: int = 30,
                 temp_dir: Optional[str] = None):
        """
        初始化圖片下載器
        
        Args:
            max_file_size (int): 最大檔案大小 (bytes)
            timeout (int): 下載超時時間 (秒)
            temp_dir (Optional[str]): 臨時目錄路徑
        """
        self.max_file_size = max_file_size
        self.timeout = timeout
        self.temp_dir = temp_dir or tempfile.gettempdir()
        
        # 支援的圖片格式
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
        
        # HTTP 請求標頭
        self.headers = {
            'User-Agent': 'PictureQA-API/1.0 (Image Validation Service)',
            'Accept': 'image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
        }
    
    def validate_url(self, url: str) -> bool:
        """
        驗證 URL 格式
        
        Args:
            url (str): 圖片 URL
            
        Returns:
            bool: URL 是否有效
        """
        if not url or not isinstance(url, str):
            return False
            
        # 基本 URL 格式檢查
        if not (url.startswith('http://') or url.startswith('https://')):
            return False
            
        # 檢查是否包含圖片副檔名或來自已知圖片服務
        url_lower = url.lower()
        
        # 檢查傳統圖片副檔名
        has_image_extension = any(ext in url_lower for ext in self.supported_formats)
        
        # 檢查已知圖片服務域名
        image_services = [
            'images.unsplash.com',
            'unsplash.com',
            'pixabay.com',
            'pexels.com',
            'imgur.com',
            'i.imgur.com',
            'cdn.pixabay.com',
            'images.pexels.com'
        ]
        
        is_image_service = any(service in url_lower for service in image_services)
        
        return has_image_extension or is_image_service
    
    def download_image(self, url: str) -> Tuple[bool, Optional[str], str]:
        """
        下載圖片到臨時檔案
        
        Args:
            url (str): 圖片 URL
            
        Returns:
            Tuple[bool, Optional[str], str]: (成功, 檔案路徑, 錯誤訊息)
        """
        try:
            # 驗證 URL
            if not self.validate_url(url):
                return False, None, "無效的圖片 URL 格式"
            
            logger.info(f"開始下載圖片: {url}")
            start_time = time.time()
            
            # 發送 HEAD 請求檢查檔案大小
            try:
                head_response = requests.head(url, headers=self.headers, timeout=10)
                if head_response.status_code == 200:
                    content_length = head_response.headers.get('content-length')
                    if content_length and int(content_length) > self.max_file_size:
                        return False, None, f"檔案過大: {content_length} bytes (最大: {self.max_file_size} bytes)"
            except Exception as e:
                logger.warning(f"HEAD 請求失敗，繼續下載: {str(e)}")
            
            # 下載圖片
            response = requests.get(url, headers=self.headers, timeout=self.timeout, stream=True)
            response.raise_for_status()
            
            # 檢查 Content-Type
            content_type = response.headers.get('content-type', '').lower()
            if not content_type.startswith('image/'):
                return False, None, f"不是圖片檔案: Content-Type = {content_type}"
            
            # 產生臨時檔案名稱
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            timestamp = int(time.time())
            
            # 從 URL 或 Content-Type 推斷副檔名
            file_ext = self._get_file_extension(url, content_type)
            temp_filename = f"img_{timestamp}_{url_hash}{file_ext}"
            temp_filepath = os.path.join(self.temp_dir, temp_filename)
            
            # 下載並儲存檔案
            downloaded_size = 0
            with open(temp_filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        downloaded_size += len(chunk)
                        if downloaded_size > self.max_file_size:
                            f.close()
                            os.unlink(temp_filepath)
                            return False, None, f"檔案過大: {downloaded_size} bytes"
                        f.write(chunk)
            
            download_time = time.time() - start_time
            logger.info(f"圖片下載完成: {temp_filepath} ({downloaded_size} bytes, {download_time:.2f}s)")
            
            # 驗證圖片檔案
            if not self._validate_image_file(temp_filepath):
                os.unlink(temp_filepath)
                return False, None, "下載的檔案不是有效的圖片"
            
            return True, temp_filepath, "下載成功"
            
        except requests.exceptions.Timeout:
            return False, None, f"下載超時 ({self.timeout}s)"
        except requests.exceptions.RequestException as e:
            return False, None, f"下載失敗: {str(e)}"
        except Exception as e:
            logger.error(f"下載圖片時發生未預期錯誤: {str(e)}")
            return False, None, f"下載失敗: {str(e)}"
    
    def _get_file_extension(self, url: str, content_type: str) -> str:
        """
        從 URL 或 Content-Type 推斷檔案副檔名
        
        Args:
            url (str): 圖片 URL
            content_type (str): HTTP Content-Type
            
        Returns:
            str: 檔案副檔名
        """
        # 先從 URL 嘗試取得副檔名
        url_path = url.split('?')[0]  # 移除查詢參數
        url_ext = Path(url_path).suffix.lower()
        if url_ext in self.supported_formats:
            return url_ext
        
        # 從 Content-Type 推斷
        content_type_map = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/webp': '.webp',
            'image/bmp': '.bmp',
            'image/tiff': '.tiff',
            'image/tif': '.tiff'
        }
        
        return content_type_map.get(content_type.lower(), '.jpg')
    
    def _validate_image_file(self, filepath: str) -> bool:
        """
        驗證圖片檔案是否有效
        
        Args:
            filepath (str): 圖片檔案路徑
            
        Returns:
            bool: 檔案是否為有效圖片
        """
        try:
            with Image.open(filepath) as img:
                # 嘗試載入圖片資訊
                img.verify()
                
            # 重新開啟檢查是否能正常讀取
            with Image.open(filepath) as img:
                width, height = img.size
                if width < 1 or height < 1:
                    return False
                    
                # 檢查圖片不能太小或太大
                if width > 10000 or height > 10000:
                    logger.warning(f"圖片尺寸過大: {width}x{height}")
                    return False
                    
                if width < 10 or height < 10:
                    logger.warning(f"圖片尺寸過小: {width}x{height}")
                    return False
                
            return True
            
        except Exception as e:
            logger.error(f"圖片檔案驗證失敗: {str(e)}")
            return False
    
    def cleanup_temp_file(self, filepath: str) -> bool:
        """
        清理臨時檔案
        
        Args:
            filepath (str): 檔案路徑
            
        Returns:
            bool: 清理是否成功
        """
        try:
            if filepath and os.path.exists(filepath):
                os.unlink(filepath)
                logger.debug(f"臨時檔案已清理: {filepath}")
                return True
            return True
        except Exception as e:
            logger.error(f"清理臨時檔案失敗: {str(e)}")
            return False
    
    def get_image_info(self, filepath: str) -> Optional[dict]:
        """
        取得圖片基本資訊
        
        Args:
            filepath (str): 圖片檔案路徑
            
        Returns:
            Optional[dict]: 圖片資訊
        """
        try:
            with Image.open(filepath) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'size_bytes': os.path.getsize(filepath)
                }
        except Exception as e:
            logger.error(f"取得圖片資訊失敗: {str(e)}")
            return None 