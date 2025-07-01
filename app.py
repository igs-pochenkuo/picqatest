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

# 添加 src 目錄到 Python 路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 導入核心模組
from config import Config
from validation_engine import ValidationEngine

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

def initialize_services():
    """初始化服務組件"""
    global config, validation_engine
    
    try:
        # 載入配置
        config = Config()
        logger.info("配置載入成功")
        
        # 初始化驗證引擎
        validation_engine = ValidationEngine()
        if not validation_engine.initialize():
            raise Exception("驗證引擎初始化失敗")
        logger.info("驗證引擎初始化成功")
        
        return True
    except Exception as e:
        logger.error(f"服務初始化失敗: {str(e)}")
        logger.error(traceback.format_exc())
        return False

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
        similarity_threshold = data.get('similarity_threshold', 0.38)
        ollama_enabled = data.get('ollama_enabled', True)
        confidence_threshold = data.get('confidence_threshold', 0.7)
        
        logger.info(f"開始驗證圖片: {image_url}")
        logger.info(f"使用提示: {prompt[:100]}...")
        
        # TODO: 實現實際的驗證邏輯
        # 目前返回測試回應
        result = {
            'success': True,
            'image_url': image_url,
            'prompt': prompt,
            'parameters': {
                'similarity_threshold': similarity_threshold,
                'ollama_enabled': ollama_enabled,
                'confidence_threshold': confidence_threshold
            },
            'clip_analysis': {
                'similarity_score': 0.42,  # 測試值
                'status': 'success',
                'processing_time': 1.5
            },
            'ollama_validation': {
                'enabled': ollama_enabled,
                'status': 'normal',
                'confidence': 0.85,
                'details': 'Image appears to be high quality with no apparent issues.',
                'processing_time': 3.2
            },
            'final_status': 'accepted',
            'total_processing_time': 4.7,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"驗證完成，結果: {result['final_status']}")
        return jsonify(result)
        
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