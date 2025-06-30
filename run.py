"""
PictureQA Demo 啟動腳本
簡化應用程式啟動流程
"""

import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """檢查依賴套件是否已安裝"""
    # 套件名稱與實際導入名稱的映射
    package_import_map = {
        'streamlit': 'streamlit',
        'torch': 'torch', 
        'open-clip-torch': 'open_clip',  # 修正：open-clip-torch 的導入名稱是 open_clip
        'pillow': 'PIL',  # 修正：pillow 的導入名稱是 PIL
        'pandas': 'pandas',
        'plotly': 'plotly'
    }
    
    missing_packages = []
    
    for package_name, import_name in package_import_map.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print("❌ 缺少以下依賴套件:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n請執行以下命令安裝依賴套件:")
        print("pip install -r requirements.txt")
        return False
    
    print("✅ 所有依賴套件已安裝")
    return True

def check_directory_structure():
    """檢查專案目錄結構"""
    required_dirs = [
        'src',
        'ui',
        'ui/components',
        'data',
        'data/results',
        'data/exports',
        'data/cache'
    ]
    
    project_root = Path(__file__).parent
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            print(f"📁 創建目錄: {dir_path}")
            full_path.mkdir(parents=True, exist_ok=True)
    
    print("✅ 目錄結構檢查完成")

def run_streamlit_app():
    """啟動 Streamlit 應用程式"""
    app_path = Path(__file__).parent / "ui" / "main_app.py"
    
    if not app_path.exists():
        print(f"❌ 找不到應用程式檔案: {app_path}")
        return False
    
    print("🚀 正在啟動 PictureQA Demo...")
    print(f"📁 應用程式路徑: {app_path}")
    print("🌐 應用程式將在瀏覽器中自動開啟")
    print("📝 使用 Ctrl+C 停止應用程式")
    print("-" * 50)
    
    try:
        # 啟動 Streamlit 應用程式
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(app_path),
            "--server.headless", "false",
            "--server.enableCORS", "false",
            "--server.enableXsrfProtection", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 應用程式已停止")
    except Exception as e:
        print(f"❌ 啟動應用程式時發生錯誤: {e}")
        return False
    
    return True

def main():
    """主函數"""
    print("🖼️ PictureQA Demo - 圖片與文字相似度分析工具")
    print("=" * 50)
    
    # 檢查依賴套件
    if not check_dependencies():
        return
    
    # 檢查目錄結構
    check_directory_structure()
    
    # 啟動應用程式
    run_streamlit_app()

if __name__ == "__main__":
    main() 