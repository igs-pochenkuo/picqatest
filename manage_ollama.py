#!/usr/bin/env python3
"""
Ollama 服務管理腳本

提供啟動、停止、重啟 Ollama 服務的功能
"""

import subprocess
import time
import sys
import psutil
import requests

def get_ollama_processes():
    """取得所有 Ollama 相關進程"""
    ollama_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            if 'ollama' in proc.info['name'].lower():
                ollama_processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'memory_mb': proc.info['memory_info'].rss / 1024 / 1024
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return ollama_processes

def check_ollama_service():
    """檢查 Ollama 服務狀態"""
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        return response.status_code == 200
    except:
        return False

def stop_ollama():
    """停止 Ollama 服務"""
    print("🛑 停止 Ollama 服務...")
    
    processes = get_ollama_processes()
    if not processes:
        print("✅ 沒有發現 Ollama 進程")
        return True
    
    # 顯示找到的進程
    print(f"🔍 發現 {len(processes)} 個 Ollama 進程:")
    for proc in processes:
        print(f"  - PID: {proc['pid']}, 名稱: {proc['name']}, 記憶體: {proc['memory_mb']:.1f} MB")
    
    # 第一步：嘗試優雅關閉所有 ollama 相關進程
    ollama_executables = ['ollama.exe', 'ollama app.exe', 'ollama_app.exe']
    
    for exe_name in ollama_executables:
        try:
            print(f"🔄 嘗試優雅關閉 {exe_name}...")
            result = subprocess.run(['taskkill', '/IM', exe_name, '/T'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ {exe_name} 已優雅關閉")
            else:
                print(f"⚠️ {exe_name} 優雅關閉失敗: {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            print(f"⚠️ {exe_name} 優雅關閉超時")
        except Exception as e:
            print(f"⚠️ {exe_name} 優雅關閉異常: {e}")
    
    # 等待一下讓進程有時間關閉
    time.sleep(2)
    
    # 檢查剩餘進程
    remaining_processes = get_ollama_processes()
    if not remaining_processes:
        print("✅ 所有 Ollama 進程已停止")
        return True
    
    # 第二步：強制終止剩餘進程
    print("⚠️ 優雅關閉失敗，嘗試強制終止...")
    
    for exe_name in ollama_executables:
        try:
            print(f"💀 強制終止 {exe_name}...")
            result = subprocess.run(['taskkill', '/IM', exe_name, '/F'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ {exe_name} 已強制終止")
        except Exception as e:
            print(f"⚠️ 強制終止 {exe_name} 失敗: {e}")
    
    # 第三步：按 PID 強制終止剩餘進程
    remaining_processes = get_ollama_processes()
    if remaining_processes:
        print("🎯 按 PID 強制終止剩餘進程...")
        for proc in remaining_processes:
            try:
                print(f"💀 強制終止 PID {proc['pid']} ({proc['name']})...")
                result = subprocess.run(['taskkill', '/PID', str(proc['pid']), '/F'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print(f"✅ PID {proc['pid']} 已終止")
                else:
                    print(f"⚠️ PID {proc['pid']} 終止失敗: {result.stderr.strip()}")
            except Exception as e:
                print(f"⚠️ 終止 PID {proc['pid']} 異常: {e}")
    
    # 最終檢查
    time.sleep(3)
    final_processes = get_ollama_processes()
    if final_processes:
        print(f"❌ 仍有 {len(final_processes)} 個進程未停止:")
        for proc in final_processes:
            print(f"  - PID: {proc['pid']}, 名稱: {proc['name']}")
        print("💡 提示：某些進程可能需要管理員權限才能終止")
        return False
    else:
        print("✅ 所有 Ollama 進程已停止")
        return True

def start_ollama():
    """啟動 Ollama 服務"""
    print("🚀 啟動 Ollama 服務...")
    
    # 檢查是否已經運行
    if check_ollama_service():
        print("✅ Ollama 服務已在運行")
        return True
    
    try:
        # 啟動 Ollama 服務 (在背景執行)
        subprocess.Popen(['ollama', 'serve'], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        
        # 等待服務啟動
        print("⏳ 等待服務啟動...")
        for i in range(30):  # 最多等待 30 秒
            time.sleep(1)
            if check_ollama_service():
                print("✅ Ollama 服務啟動成功")
                return True
            if i % 5 == 4:
                print(f"   等待中... ({i+1}/30)")
        
        print("❌ Ollama 服務啟動超時")
        return False
        
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")
        return False

def restart_ollama():
    """重啟 Ollama 服務"""
    print("🔄 重啟 Ollama 服務...")
    
    # 先停止
    stop_success = stop_ollama()
    if not stop_success:
        print("❌ 停止服務失敗，無法重啟")
        return False
    
    # 等待一下
    time.sleep(2)
    
    # 再啟動
    start_success = start_ollama()
    return start_success

def show_status():
    """顯示 Ollama 狀態"""
    print("📊 Ollama 服務狀態")
    print("="*40)
    
    # 檢查服務狀態
    service_running = check_ollama_service()
    print(f"🔗 API 服務: {'✅ 運行中' if service_running else '❌ 未運行'}")
    
    # 檢查進程
    processes = get_ollama_processes()
    print(f"🔍 進程數量: {len(processes)}")
    
    if processes:
        total_memory = sum(p['memory_mb'] for p in processes)
        print(f"💾 總記憶體使用: {total_memory:.1f} MB")
        print("\n進程詳情:")
        for proc in processes:
            print(f"  PID {proc['pid']:>8} | {proc['name']:<15} | {proc['memory_mb']:>8.1f} MB")

def main():
    """主函數"""
    if len(sys.argv) < 2:
        print("🔧 Ollama 服務管理工具")
        print("="*30)
        print("使用方式:")
        print("  python manage_ollama.py status   - 顯示狀態")
        print("  python manage_ollama.py start    - 啟動服務")
        print("  python manage_ollama.py stop     - 停止服務")
        print("  python manage_ollama.py restart  - 重啟服務")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'status':
        show_status()
    elif command == 'start':
        start_ollama()
    elif command == 'stop':
        stop_ollama()
    elif command == 'restart':
        restart_ollama()
    else:
        print(f"❌ 未知命令: {command}")
        print("支援的命令: status, start, stop, restart")

if __name__ == "__main__":
    main() 