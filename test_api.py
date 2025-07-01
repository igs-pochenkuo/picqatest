#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PictureQA Flask API 測試腳本
用於驗證 API 端點的基本功能
"""

import requests
import json
import time

# API 基礎 URL
BASE_URL = "http://localhost:5000"

def test_health_check():
    """測試健康檢查端點"""
    print("🔍 測試健康檢查端點...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"狀態碼: {response.status_code}")
        print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            print("✅ 健康檢查測試通過")
            return True
        else:
            print("❌ 健康檢查測試失敗")
            return False
            
    except Exception as e:
        print(f"❌ 健康檢查測試錯誤: {str(e)}")
        return False

def test_validate_api_basic():
    """測試基本的驗證 API"""
    print("\n🔍 測試基本驗證 API...")
    
    # 測試資料
    test_data = {
        "image_url": "https://example.com/test-image.jpg",
        "prompt": "A realistic photo of a cat sitting on a table"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/validate",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"狀態碼: {response.status_code}")
        print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            result = response.json()
            if 'success' in result and result['success']:
                print("✅ 基本驗證 API 測試通過")
                return True
            else:
                print("❌ 基本驗證 API 測試失敗 - 回應格式不正確")
                return False
        else:
            print("❌ 基本驗證 API 測試失敗")
            return False
            
    except Exception as e:
        print(f"❌ 基本驗證 API 測試錯誤: {str(e)}")
        return False

def test_validate_api_with_params():
    """測試帶參數的驗證 API"""
    print("\n🔍 測試帶參數的驗證 API...")
    
    # 測試資料
    test_data = {
        "image_url": "https://example.com/test-image2.jpg",
        "prompt": "A realistic photo of a dog playing in the park",
        "similarity_threshold": 0.35,
        "ollama_enabled": True,
        "confidence_threshold": 0.8
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/validate",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"狀態碼: {response.status_code}")
        result = response.json()
        print(f"回應: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            # 檢查參數是否正確傳遞
            if 'parameters' in result:
                params = result['parameters']
                if (params.get('similarity_threshold') == 0.35 and
                    params.get('ollama_enabled') == True and
                    params.get('confidence_threshold') == 0.8):
                    print("✅ 帶參數驗證 API 測試通過")
                    return True
                else:
                    print("❌ 帶參數驗證 API 測試失敗 - 參數傳遞不正確")
                    return False
            else:
                print("❌ 帶參數驗證 API 測試失敗 - 缺少參數資訊")
                return False
        else:
            print("❌ 帶參數驗證 API 測試失敗")
            return False
            
    except Exception as e:
        print(f"❌ 帶參數驗證 API 測試錯誤: {str(e)}")
        return False

def test_error_cases():
    """測試錯誤情況"""
    print("\n🔍 測試錯誤情況...")
    
    test1_passed = False
    test2_passed = False
    
    # 測試缺少必要參數
    print("測試缺少 image_url...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/validate",
            json={"prompt": "test"},
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 400:
            print("✅ 缺少 image_url 錯誤處理正確")
            test1_passed = True
        else:
            print(f"❌ 缺少 image_url 錯誤處理失敗，狀態碼: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 錯誤測試異常: {str(e)}")
    
    # 測試缺少 prompt
    print("測試缺少 prompt...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/validate",
            json={"image_url": "http://example.com/test.jpg"},
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 400:
            print("✅ 缺少 prompt 錯誤處理正確")
            test2_passed = True
        else:
            print(f"❌ 缺少 prompt 錯誤處理失敗，狀態碼: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 錯誤測試異常: {str(e)}")
    
    # 兩個子測試都通過才算通過
    if test1_passed and test2_passed:
        print("✅ 錯誤情況測試通過")
        return True
    else:
        print("❌ 錯誤情況測試失敗")
        return False

def test_404_endpoint():
    """測試不存在的端點"""
    print("\n🔍 測試 404 端點...")
    
    try:
        response = requests.get(f"{BASE_URL}/nonexistent")
        
        if response.status_code == 404:
            print("✅ 404 錯誤處理正確")
            return True
        else:
            print(f"❌ 404 錯誤處理失敗，狀態碼: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 404 測試異常: {str(e)}")
        return False

def main():
    """執行所有測試"""
    print("🚀 開始 PictureQA API 測試")
    print("=" * 50)
    
    # 等待伺服器啟動
    print("等待伺服器啟動...")
    time.sleep(2)
    
    # 執行測試
    tests = [
        test_health_check,
        test_validate_api_basic,
        test_validate_api_with_params,
        test_error_cases,
        test_404_endpoint
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ 測試執行異常: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"🏁 測試完成: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 所有測試通過！")
    else:
        print("⚠️  部分測試失敗，請檢查伺服器狀態")

if __name__ == "__main__":
    main() 