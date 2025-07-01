#!/usr/bin/env python3
"""
資源管理測試腳本

測試 PictureQA 各個組件的資源清理是否正確
"""

import os
import sys
import psutil
import time
import gc
import requests
import json
from pathlib import Path

# 添加 src 目錄到 Python 路徑
current_dir = Path(__file__).parent
src_dir = current_dir / 'src'
sys.path.insert(0, str(src_dir))

from similarity_engine import SimilarityEngine
from validation_engine import ValidationEngine
from ollama_validator import OllamaValidator
from image_downloader import ImageDownloader

def get_process_memory():
    """取得當前進程的記憶體使用量 (MB)"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def test_similarity_engine_memory():
    """測試 SimilarityEngine 的記憶體管理"""
    print("\n🔍 測試 SimilarityEngine 記憶體管理...")
    
    initial_memory = get_process_memory()
    print(f"初始記憶體: {initial_memory:.1f} MB")
    
    # 建立多個 SimilarityEngine 實例
    engines = []
    for i in range(3):
        print(f"建立 SimilarityEngine {i+1}/3...")
        engine = SimilarityEngine()
        success = engine.initialize_model()
        if success:
            engines.append(engine)
            memory_after_init = get_process_memory()
            print(f"初始化後記憶體: {memory_after_init:.1f} MB")
        else:
            print(f"SimilarityEngine {i+1} 初始化失敗")
    
    # 測試計算相似度（如果有測試圖片）
    test_image_path = "testPic/3餅乾"
    if os.path.exists(test_image_path):
        image_files = [f for f in os.listdir(test_image_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if image_files and engines:
            test_image = os.path.join(test_image_path, image_files[0])
            print(f"使用測試圖片: {test_image}")
            
            for i, engine in enumerate(engines):
                similarity = engine.calculate_similarity(test_image, "cookies")
                memory_after_calc = get_process_memory()
                print(f"Engine {i+1} 計算後記憶體: {memory_after_calc:.1f} MB (相似度: {similarity:.3f})")
    
    peak_memory = get_process_memory()
    print(f"峰值記憶體: {peak_memory:.1f} MB")
    
    # 清理資源
    print("清理 SimilarityEngine 資源...")
    for i, engine in enumerate(engines):
        engine.cleanup_resources()
        del engine
        memory_after_cleanup = get_process_memory()
        print(f"Engine {i+1} 清理後記憶體: {memory_after_cleanup:.1f} MB")
    
    # 強制垃圾回收
    engines.clear()
    gc.collect()
    
    final_memory = get_process_memory()
    print(f"最終記憶體: {final_memory:.1f} MB")
    print(f"記憶體差異: {final_memory - initial_memory:.1f} MB")
    
    return final_memory - initial_memory

def test_ollama_connection_management():
    """測試 Ollama 連接管理"""
    print("\n🔍 測試 Ollama 連接管理...")
    
    initial_memory = get_process_memory()
    print(f"初始記憶體: {initial_memory:.1f} MB")
    
    # 建立多個 Ollama 驗證器並測試連接
    validators = []
    for i in range(5):
        print(f"建立 OllamaValidator {i+1}/5...")
        validator = OllamaValidator()
        
        # 測試連接
        connection_status = validator.check_connection()
        print(f"連接狀態: {connection_status['connected']}")
        
        validators.append(validator)
        memory_after_creation = get_process_memory()
        print(f"Validator {i+1} 建立後記憶體: {memory_after_creation:.1f} MB")
    
    peak_memory = get_process_memory()
    print(f"峰值記憶體: {peak_memory:.1f} MB")
    
    # 清理
    print("清理 OllamaValidator...")
    for i, validator in enumerate(validators):
        del validator
        memory_after_cleanup = get_process_memory()
        print(f"Validator {i+1} 清理後記憶體: {memory_after_cleanup:.1f} MB")
    
    validators.clear()
    gc.collect()
    
    final_memory = get_process_memory()
    print(f"最終記憶體: {final_memory:.1f} MB")
    print(f"記憶體差異: {final_memory - initial_memory:.1f} MB")
    
    return final_memory - initial_memory

def test_image_downloader_memory():
    """測試 ImageDownloader 記憶體管理"""
    print("\n🔍 測試 ImageDownloader 記憶體管理...")
    
    initial_memory = get_process_memory()
    print(f"初始記憶體: {initial_memory:.1f} MB")
    
    # 測試圖片 URLs
    test_urls = [
        "https://images.unsplash.com/photo-1574158622682-e40e69881006?w=400",
        "https://images.unsplash.com/photo-1552053831-71594a27632d?w=400",
        "https://images.unsplash.com/photo-1601758228041-f3b2795255f1?w=400"
    ]
    
    downloader = ImageDownloader(max_file_size=10*1024*1024, timeout=15)
    downloaded_files = []
    
    for i, url in enumerate(test_urls):
        print(f"下載圖片 {i+1}/{len(test_urls)}: {url[:50]}...")
        
        success, temp_path, message = downloader.download_image(url)
        
        if success:
            downloaded_files.append(temp_path)
            print(f"下載成功: {temp_path}")
        else:
            print(f"下載失敗: {message}")
        
        memory_after_download = get_process_memory()
        print(f"下載後記憶體: {memory_after_download:.1f} MB")
    
    peak_memory = get_process_memory()
    print(f"峰值記憶體: {peak_memory:.1f} MB")
    
    # 清理下載的檔案
    print("清理下載的檔案...")
    for file_path in downloaded_files:
        downloader.cleanup_temp_file(file_path)
    
    del downloader
    gc.collect()
    
    final_memory = get_process_memory()
    print(f"最終記憶體: {final_memory:.1f} MB")
    print(f"記憶體差異: {final_memory - initial_memory:.1f} MB")
    
    return final_memory - initial_memory

def test_full_validation_cycle():
    """測試完整驗證循環的記憶體管理"""
    print("\n🔍 測試完整驗證循環記憶體管理...")
    
    initial_memory = get_process_memory()
    print(f"初始記憶體: {initial_memory:.1f} MB")
    
    # 建立 ValidationEngine
    engine = ValidationEngine()
    success = engine.initialize()
    
    if not success:
        print("ValidationEngine 初始化失敗")
        return 0
    
    memory_after_init = get_process_memory()
    print(f"初始化後記憶體: {memory_after_init:.1f} MB")
    
    # 測試圖片路徑
    test_image_path = "testPic/3餅乾"
    if os.path.exists(test_image_path):
        image_files = [f for f in os.listdir(test_image_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        if image_files:
            # 執行多次驗證
            for cycle in range(3):
                print(f"\n驗證循環 {cycle+1}/3...")
                
                test_image = os.path.join(test_image_path, image_files[0])
                
                # 設定引擎參數
                engine.update_settings({
                    'ollama_enabled': True,
                    'verification_threshold': 0.3,
                    'confidence_threshold': 0.7
                })
                
                # 執行驗證
                results = engine.analyze_with_validation([test_image], "cookies and snacks")
                
                if results:
                    result = results[0]
                    print(f"驗證結果: {result['final_status']} (相似度: {result['similarity_score']:.3f})")
                
                memory_after_validation = get_process_memory()
                print(f"驗證後記憶體: {memory_after_validation:.1f} MB")
                
                # 強制垃圾回收
                gc.collect()
    
    peak_memory = get_process_memory()
    print(f"峰值記憶體: {peak_memory:.1f} MB")
    
    # 清理 ValidationEngine
    print("清理 ValidationEngine...")
    engine.cleanup_resources()
    del engine
    gc.collect()
    
    final_memory = get_process_memory()
    print(f"最終記憶體: {final_memory:.1f} MB")
    print(f"記憶體差異: {final_memory - initial_memory:.1f} MB")
    
    return final_memory - initial_memory

def test_api_request_simulation():
    """模擬 API 請求測試記憶體洩漏"""
    print("\n🔍 模擬 API 請求測試...")
    
    # 檢查 API 是否運行
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code != 200:
            print("API 服務未運行，跳過 API 測試")
            return 0
    except:
        print("API 服務未運行，跳過 API 測試")
        return 0
    
    initial_memory = get_process_memory()
    print(f"初始記憶體: {initial_memory:.1f} MB")
    
    test_url = "https://images.unsplash.com/photo-1574158622682-e40e69881006?w=400"
    
    # 模擬多次 API 請求
    for i in range(5):
        print(f"API 請求 {i+1}/5...")
        
        try:
            payload = {
                "image_url": test_url,
                "prompt": "cookies and snacks",
                "similarity_threshold": 0.3,
                "ollama_enabled": False  # 避免 Ollama 影響測試
            }
            
            response = requests.post(
                "http://localhost:5000/api/v1/validate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"API 回應: {result['final_status']} (相似度: {result['clip_analysis']['similarity_score']:.3f})")
            else:
                print(f"API 錯誤: {response.status_code}")
                
        except Exception as e:
            print(f"API 請求失敗: {str(e)}")
        
        memory_after_request = get_process_memory()
        print(f"請求後記憶體: {memory_after_request:.1f} MB")
        
        # 等待一下讓系統處理
        time.sleep(1)
    
    final_memory = get_process_memory()
    print(f"最終記憶體: {final_memory:.1f} MB")
    print(f"記憶體差異: {final_memory - initial_memory:.1f} MB")
    
    return final_memory - initial_memory

def main():
    """主測試函數"""
    print("🚀 PictureQA 資源管理測試開始")
    print(f"當前進程 PID: {os.getpid()}")
    print(f"初始系統記憶體: {get_process_memory():.1f} MB")
    
    results = {}
    
    # 各項測試
    try:
        results['similarity_engine'] = test_similarity_engine_memory()
    except Exception as e:
        print(f"SimilarityEngine 測試失敗: {e}")
        results['similarity_engine'] = None
    
    try:
        results['ollama_validator'] = test_ollama_connection_management()
    except Exception as e:
        print(f"OllamaValidator 測試失敗: {e}")
        results['ollama_validator'] = None
    
    try:
        results['image_downloader'] = test_image_downloader_memory()
    except Exception as e:
        print(f"ImageDownloader 測試失敗: {e}")
        results['image_downloader'] = None
    
    try:
        results['validation_cycle'] = test_full_validation_cycle()
    except Exception as e:
        print(f"ValidationEngine 測試失敗: {e}")
        results['validation_cycle'] = None
    
    try:
        results['api_simulation'] = test_api_request_simulation()
    except Exception as e:
        print(f"API 模擬測試失敗: {e}")
        results['api_simulation'] = None
    
    # 總結
    print("\n" + "="*60)
    print("📊 資源管理測試總結")
    print("="*60)
    
    for test_name, memory_diff in results.items():
        if memory_diff is not None:
            status = "✅ 良好" if abs(memory_diff) < 50 else "⚠️  需注意" if abs(memory_diff) < 100 else "❌ 可能洩漏"
            print(f"{test_name:20s}: {memory_diff:+6.1f} MB - {status}")
        else:
            print(f"{test_name:20s}: 測試失敗")
    
    print("\n💡 建議：")
    print("- 記憶體差異在 ±50MB 內屬正常範圍")
    print("- 超過 100MB 可能存在記憶體洩漏")
    print("- 如有持續洩漏，檢查是否有資源未正確釋放")

if __name__ == "__main__":
    main() 