#!/usr/bin/env python3
import requests
import time

url = "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=800"
prompt = "A realistic photo of a cat sitting"

print("🧪 簡化測試開始")
print(f"圖片 URL: {url}")
print(f"提示: {prompt}")

data = {
    "image_url": url,
    "prompt": prompt,
    "similarity_threshold": 0.25,
    "ollama_enabled": False  # 先關閉 Ollama 以加快測試
}

print("\n⏳ 發送請求...")
start_time = time.time()

try:
    response = requests.post(
        "http://localhost:5000/api/v1/validate",
        json=data,
        timeout=120
    )
    
    elapsed = time.time() - start_time
    print(f"⏱️  請求時間: {elapsed:.2f}s")
    print(f"📊 狀態碼: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ 請求成功")
        print(f"🎯 最終狀態: {result.get('final_status')}")
        print(f"📈 相似度: {result.get('clip_analysis', {}).get('similarity_score', 0):.4f}")
        
        if 'image_info' in result:
            info = result['image_info']
            print(f"🖼️  圖片: {info.get('width')}x{info.get('height')}, {info.get('size_bytes')/1024:.1f}KB")
    else:
        print("❌ 請求失敗")
        print(f"回應: {response.text}")
        
except Exception as e:
    print(f"❌ 錯誤: {str(e)}")

print("\n🏁 測試完成") 