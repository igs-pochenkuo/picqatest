#!/usr/bin/env python3
"""
測試特定 URL 的腳本
"""

import requests
import json
import time

def test_url_access():
    """測試 URL 是否可以存取"""
    url = 'http://192.168.153.78:8005/txt2img-images/2025-06-30/thread_17pT1g5z5oRCTRnujkF3Xm9L_story_seg_1.png'
    
    print(f"🔍 測試 URL 存取性：")
    print(f"URL: {url}")
    
    try:
        # 測試 HEAD 請求
        print("\n📡 發送 HEAD 請求...")
        response = requests.head(url, timeout=15)
        print(f"✅ HEAD 狀態碼: {response.status_code}")
        print(f"📦 Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"📏 Content-Length: {response.headers.get('content-length', 'N/A')}")
        
        # 測試 GET 請求
        print("\n📥 發送 GET 請求...")
        response = requests.get(url, timeout=15)
        print(f"✅ GET 狀態碼: {response.status_code}")
        print(f"📦 Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"📏 實際大小: {len(response.content)} bytes")
        
        return True
        
    except requests.exceptions.Timeout:
        print("❌ 請求超時")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 連接錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他錯誤: {e}")
        return False

def test_api_with_url():
    """測試 API 處理該 URL"""
    
    # 先檢查 API 服務是否運行
    try:
        health_check = requests.get('http://localhost:5000/health', timeout=5)
        if health_check.status_code != 200:
            print("❌ API 服務未運行")
            return
    except:
        print("❌ 無法連接到 API 服務")
        return
    
    url = 'http://192.168.153.78:8005/txt2img-images/2025-06-30/thread_17pT1g5z5oRCTRnujkF3Xm9L_story_seg_1.png'
    
    print(f"\n🧪 測試 API 處理該 URL：")
    
    payload = {
        "image_url": url,
        "prompt": "A fat orange cat",
        "similarity_threshold": 0.3,
        "ollama_enabled": False  # 先測試不使用 Ollama
    }
    
    print(f"📤 發送 API 請求...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(
            'http://localhost:5000/api/v1/validate',
            json=payload,
            timeout=60  # 增加超時時間
        )
        request_time = time.time() - start_time
        
        print(f"⏱️  請求時間: {request_time:.2f}s")
        print(f"📊 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API 請求成功")
            print(f"🎯 最終狀態: {result.get('final_status', 'unknown')}")
            print(f"📈 相似度: {result.get('clip_analysis', {}).get('similarity_score', 'N/A'):.4f}")
            
            # 顯示詳細結果
            print(f"\n📋 詳細結果:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        elif response.status_code == 400:
            print(f"⚠️  400 錯誤 - 客戶端錯誤")
            try:
                error_data = response.json()
                print(f"錯誤訊息: {error_data.get('message', 'N/A')}")
                print(f"錯誤類型: {error_data.get('error', 'N/A')}")
                print(f"完整回應: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"無法解析錯誤回應: {response.text}")
        else:
            print(f"❌ API 錯誤，狀態碼: {response.status_code}")
            print(f"回應內容: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ API 請求超時")
    except Exception as e:
        print(f"❌ API 請求失敗: {e}")

def main():
    print("🚀 特定 URL 測試開始")
    print("="*50)
    
    # 測試 URL 存取
    url_accessible = test_url_access()
    
    # 如果 URL 可存取，測試 API
    if url_accessible:
        test_api_with_url()
    else:
        print("\n❌ URL 無法存取，跳過 API 測試")
    
    print("\n🏁 測試完成")

if __name__ == "__main__":
    main() 