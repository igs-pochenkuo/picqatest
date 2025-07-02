#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
實際驗證測試腳本
測試完整的圖片下載和驗證流程
"""

import requests
import json
import time

# API 基礎 URL
BASE_URL = "http://localhost:5000"

# 測試用的真實圖片 URL
TEST_IMAGES = [
    # {
    #     "name": "貓咪圖片",
    #     "url": "http://192.168.153.78:8005/txt2img-images/2025-06-30/thread_17pT1g5z5oRCTRnujkF3Xm9L_story_seg_1.png",
    #     "prompt": "The fat orange cat stands in the park, plump with fluffy orange-and-cream fur, round cheeks, oversized green eyes, and a tiny blue hoodie barely stretching over his belly. His short, stubby paws are at his sides, and his tail is tucked in surprise. Facial expression: wide-eyed, mouth agape. In the background, his slender, stylish ex-girlfriend (a silver tabby with a pink bow) nuzzles a lean, muscular white tabby. The scene features sunlight filtering through city trees and a fallen donut beside fat orange cat."
    # },
    {
        "name": "貓咪圖片",
        "url": "http://192.168.153.78:8005/txt2img-images/2025-07-02/thread_1JpoizUF4rmMidmuBM09lbZC_story_seg_1.png",
        "prompt": "Da Pang Mao, a chubby, oversized orange tabby cat with a round face, fluffy cheeks, small triangular ears, and tiny blue eyes, is sprawled lazily on a sunlit windowsill. She wears a tiny, tight white T-shirt with a cartoon fish print barely fitting her belly, her striped tail drooped down. Her facial expression instantly shifts to wide-eyed panic and an open mouth, while her body stiffens up in a half-sit posture. The room is a cozy living room with potted plants and a scratch post in the background.",
        "similarity_threshold": 0.3
    },
    # {
    #     "name": "風景圖片 (不匹配)",
    #     "url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800", 
    #     "prompt": "A realistic photo of a cat"
    # }
]

def test_real_validation():
    """測試實際的圖片驗證"""
    print("🧪 開始實際圖片驗證測試")
    print("=" * 60)
    
    for i, test_case in enumerate(TEST_IMAGES, 1):
        print(f"\n📸 測試 {i}: {test_case['name']}")
        print(f"URL: {test_case['url'][:80]}...")
        print(f"Prompt: {test_case['prompt']}")
        
        # 準備測試資料
        test_data = {
            "image_url": test_case['url'],
            "prompt": test_case['prompt'],
            "similarity_threshold": 0.25,  # 較低的閾值以便觀察差異
            "ollama_enabled": True,
            "confidence_threshold": 0.7
        }
        
        try:
            print("⏳ 發送驗證請求...")
            start_time = time.time()
            
            response = requests.post(
                f"{BASE_URL}/api/v1/validate",
                json=test_data,
                headers={'Content-Type': 'application/json'},
                timeout=60  # 增加超時時間
            )
            
            request_time = time.time() - start_time
            
            print(f"⏱️  請求時間: {request_time:.2f}s")
            print(f"📊 狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # 顯示關鍵結果
                print("✅ 驗證成功")
                print(f"🎯 最終狀態: {result.get('final_status', 'unknown')}")
                print(f"📈 相似度分數: {result.get('clip_analysis', {}).get('similarity_score', 0.0):.4f}")
                
                # 圖片資訊
                if 'image_info' in result:
                    img_info = result['image_info']
                    print(f"🖼️  圖片尺寸: {img_info.get('width', 0)}x{img_info.get('height', 0)}")
                    print(f"📦 檔案大小: {img_info.get('size_bytes', 0) / 1024:.1f} KB")
                
                # CLIP 分析結果
                clip_analysis = result.get('clip_analysis', {})
                print(f"🔍 CLIP 狀態: {clip_analysis.get('status', 'unknown')}")
                print(f"⏱️  CLIP 處理時間: {clip_analysis.get('processing_time', 0):.2f}s")
                
                # Ollama 驗證結果
                ollama_validation = result.get('ollama_validation', {})
                if ollama_validation.get('enabled', False):
                    print(f"🤖 Ollama 狀態: {ollama_validation.get('status', 'unknown')}")
                    print(f"🎯 Ollama 信心度: {ollama_validation.get('confidence', 0.0):.2f}")
                    print(f"💬 Ollama 詳情: {ollama_validation.get('details', 'N/A')[:100]}...")
                    print(f"⏱️  Ollama 處理時間: {ollama_validation.get('processing_time', 0):.2f}s")
                else:
                    print("🤖 Ollama 驗證: 已停用")
                
                print(f"⏱️  總處理時間: {result.get('total_processing_time', 0):.2f}s")
                
            else:
                print("❌ 驗證失敗")
                try:
                    error_info = response.json()
                    print(f"錯誤: {error_info.get('error', 'unknown')}")
                    print(f"訊息: {error_info.get('message', 'no message')}")
                except:
                    print(f"回應內容: {response.text[:200]}...")
            
        except requests.exceptions.Timeout:
            print("❌ 請求超時")
        except Exception as e:
            print(f"❌ 測試錯誤: {str(e)}")
        
        print("-" * 60)

def test_invalid_urls():
    """測試無效的 URL"""
    print("\n🚫 測試無效 URL 處理")
    print("=" * 60)
    
    invalid_urls = [
        "not-a-url",
        "http://nonexistent-domain-12345.com/image.jpg",
        "https://httpbin.org/status/404",  # 404 錯誤
        "https://httpbin.org/html",  # 非圖片內容
    ]
    
    for i, url in enumerate(invalid_urls, 1):
        print(f"\n❌ 測試 {i}: {url}")
        
        test_data = {
            "image_url": url,
            "prompt": "A test image",
            "similarity_threshold": 0.3
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/validate",
                json=test_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            print(f"狀態碼: {response.status_code}")
            
            if response.status_code != 200:
                error_info = response.json()
                print(f"✅ 正確處理錯誤: {error_info.get('error', 'unknown')}")
                print(f"訊息: {error_info.get('message', 'no message')}")
            else:
                print("⚠️  意外成功 - 可能需要檢查驗證邏輯")
                
        except Exception as e:
            print(f"測試異常: {str(e)}")

def main():
    """執行所有測試"""
    print("🚀 PictureQA 實際驗證測試")
    
    # 檢查服務是否運行
    try:
        print("🔗 正在連接服務...")
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code != 200:
            print("❌ 服務未運行，請先啟動 Flask 應用")
            return
        else:
            print(f"✅ 服務連接正常 - {response.json().get('service', 'Unknown')}")
    except Exception as e:
        print(f"❌ 無法連接到服務: {str(e)}")
        print("請確認 Flask 應用正在運行")
        return
    
    print("✅ 服務連接正常")
    
    # 執行測試
    test_real_validation()
    test_invalid_urls()
    
    print("\n🏁 測試完成")

if __name__ == "__main__":
    main() 