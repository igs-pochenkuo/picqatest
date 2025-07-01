#!/usr/bin/env python3
"""
測試 Ollama 路徑查找功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from validation_engine import ValidationEngine

def test_ollama_path():
    """測試 Ollama 路徑查找"""
    print("🔍 測試 Ollama 路徑查找...")
    
    ve = ValidationEngine()
    ollama_path = ve._find_ollama_executable()
    
    if ollama_path:
        print(f"✅ 找到 Ollama: {ollama_path}")
        
        # 檢查檔案是否存在
        if os.path.exists(ollama_path):
            print("✅ 檔案存在")
            
            # 嘗試執行版本檢查
            import subprocess
            try:
                result = subprocess.run([ollama_path, '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print(f"✅ 版本資訊: {result.stdout.strip()}")
                else:
                    print(f"⚠️ 版本檢查失敗: {result.stderr.strip()}")
            except Exception as e:
                print(f"⚠️ 版本檢查異常: {str(e)}")
        else:
            print("❌ 檔案不存在")
    else:
        print("❌ 找不到 Ollama")

if __name__ == "__main__":
    test_ollama_path() 