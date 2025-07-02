#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PictureQA Flask API 服務
提供圖片品質驗證的 REST API 接口
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import traceback
from datetime import datetime
import os
import sys
import time
import atexit

# 添加 src 目錄到 Python 路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 導入核心模組
from config import Config
from validation_engine import ValidationEngine
from image_downloader import ImageDownloader

# 初始化 Flask 應用
app = Flask(__name__)
CORS(app)  # 允許跨域請求

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全域變數
config = None
validation_engine = None
image_downloader = None

def initialize_services():
    """初始化服務組件"""
    global config, validation_engine, image_downloader
    
    try:
        # 載入配置
        config = Config()
        logger.info("配置載入成功")
        
        # 初始化驗證引擎
        validation_engine = ValidationEngine()
        if not validation_engine.initialize():
            raise Exception("驗證引擎初始化失敗")
        logger.info("驗證引擎初始化成功")
        
        # 初始化圖片下載器
        image_downloader = ImageDownloader(
            max_file_size=20 * 1024 * 1024,  # 20MB
            timeout=30
        )
        logger.info("圖片下載器初始化成功")
        
        return True
    except Exception as e:
        logger.error(f"服務初始化失敗: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def cleanup_application():
    """應用程式關閉時的資源清理"""
    try:
        global validation_engine
        if 'validation_engine' in globals() and validation_engine:
            logger.info("開始清理驗證引擎資源...")
            # 清理 SimilarityEngine 資源
            if hasattr(validation_engine, 'similarity_engine') and validation_engine.similarity_engine:
                validation_engine.similarity_engine.cleanup_resources()
            
            # 清理 ValidationEngine 本身
            if hasattr(validation_engine, 'cleanup_resources'):
                validation_engine.cleanup_resources()
                
        logger.info("應用程式資源清理完成")
    except Exception as e:
        logger.error(f"清理應用程式資源時發生錯誤: {str(e)}")

# 註冊應用程式關閉時的清理函數
atexit.register(cleanup_application)

@app.route('/health', methods=['GET'])
def health_check():
    """健康檢查端點"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'PictureQA API',
        'version': '1.0.0'
    })

@app.route('/api/v1/validate', methods=['POST'])
def validate_image():
    """圖片驗證主要端點"""
    try:
        # 檢查請求格式
        if not request.is_json:
            return jsonify({
                'error': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        
        # 驗證必要參數
        if 'image_url' not in data:
            return jsonify({
                'error': 'Missing required parameter: image_url'
            }), 400
            
        if 'prompt' not in data:
            return jsonify({
                'error': 'Missing required parameter: prompt'
            }), 400
        
        # 提取參數
        image_url = data['image_url']
        prompt = data['prompt']
        
        # 提取可選參數（使用預設值）
        similarity_threshold = data.get('similarity_threshold', 0.36)
        ollama_enabled = data.get('ollama_enabled', True)
        confidence_threshold = data.get('confidence_threshold', 0.7)
        
        logger.info(f"開始驗證圖片: {image_url}")
        logger.info(f"使用提示: {prompt[:100]}...")
        
        start_time = datetime.now()
        temp_image_path = None
        
        try:
            # 第一步：下載圖片
            logger.info("步驟 1: 下載圖片...")
            download_start = time.time()
            
            success, temp_image_path, download_message = image_downloader.download_image(image_url)
            download_time = time.time() - download_start
            
            if not success:
                return jsonify({
                    'success': False,
                    'error': 'image_download_failed',
                    'message': download_message,
                    'image_url': image_url,
                    'prompt': prompt,
                    'processing_time': download_time,
                    'timestamp': datetime.now().isoformat()
                }), 400
            
            logger.info(f"圖片下載成功: {temp_image_path} ({download_time:.2f}s)")
            
            # 取得圖片資訊
            image_info = image_downloader.get_image_info(temp_image_path)
            
            # 第二步：CLIP 相似度分析
            logger.info("步驟 2: CLIP 相似度分析...")
            clip_start = time.time()
            
            # 設定驗證引擎參數
            validation_engine.update_settings({
                'ollama_enabled': ollama_enabled,
                'verification_threshold': similarity_threshold,
                'confidence_threshold': confidence_threshold
            })
            
            # 執行驗證 (單一圖片)
            validation_results = validation_engine.analyze_with_validation(
                [temp_image_path], 
                prompt
            )
            
            if not validation_results:
                return jsonify({
                    'success': False,
                    'error': 'validation_failed',
                    'message': '驗證過程失敗',
                    'image_url': image_url,
                    'prompt': prompt,
                    'timestamp': datetime.now().isoformat()
                }), 500
            
            # 取得驗證結果
            result_data = validation_results[0]
            total_time = (datetime.now() - start_time).total_seconds()
            
            # 印出驗證結果資料以便除錯
            print("=== 驗證結果資料 ===")
            print(f"完整 result_data: {result_data}")
            print(f"相似度分數: {result_data.get('similarity_score', 'N/A')}")
            print(f"CLIP 狀態: {result_data.get('clip_status', 'N/A')}")
            print(f"Ollama 驗證: {result_data.get('ollama_validation', 'N/A')}")
            print(f"最終狀態: {result_data.get('final_status', 'N/A')}")
            print("==================")

            # 建構回應
            result = {
                'success': True,
                'image_url': image_url,
                'prompt': prompt,
                'parameters': {
                    'similarity_threshold': similarity_threshold,
                    'ollama_enabled': ollama_enabled,
                    'confidence_threshold': confidence_threshold
                },
                'image_info': image_info,
                'download_info': {
                    'status': 'success',
                    'processing_time': download_time,
                    'message': download_message
                },
                'clip_analysis': {
                    'similarity_score': result_data.get('similarity_score', 0.0),
                    'status': result_data.get('clip_status', 'failed'),
                    'processing_time': total_time * 0.6  # 估算 CLIP 處理時間
                },
                'ollama_validation': result_data.get('ollama_validation', {
                    'enabled': False,
                    'status': 'skipped',
                    'confidence': 0.0,
                    'details': '',
                    'processing_time': 0.0
                }),
                'final_status': result_data.get('final_status', 'rejected'),
                'total_processing_time': total_time,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"驗證完成，結果: {result['final_status']} (相似度: {result['clip_analysis']['similarity_score']:.3f})")
            return jsonify(result)
            
        finally:
            # 清理臨時檔案
            if temp_image_path:
                image_downloader.cleanup_temp_file(temp_image_path)
                
            # 額外的資源清理
            try:
                # 清理 GPU 快取
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
                # 強制垃圾回收
                import gc
                gc.collect()
                
            except Exception as e:
                logger.warning(f"額外資源清理時發生警告: {str(e)}")
        
    except Exception as e:
        logger.error(f"驗證過程發生錯誤: {str(e)}")
        logger.error(traceback.format_exc())
        
        return jsonify({
            'error': 'Internal server error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.errorhandler(404)
def not_found(error):
    """404 錯誤處理"""
    return jsonify({
        'error': 'Endpoint not found',
        'message': 'The requested endpoint does not exist',
        'timestamp': datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500 錯誤處理"""
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred',
        'timestamp': datetime.now().isoformat()
    }), 500

if __name__ == '__main__':
    # 初始化服務
    if not initialize_services():
        logger.error("無法啟動服務，初始化失敗")
        sys.exit(1)
    
    # 啟動 Flask 應用
    logger.info("啟動 PictureQA API 服務...")
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    ) 