"""
資料夾選擇器元件
提供資料夾選擇和驗證功能
"""

import streamlit as st
import os
from pathlib import Path
from typing import Optional, Tuple

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.utils import get_supported_image_files, validate_directory
from src.config import config

def render_folder_selector() -> Tuple[Optional[str], int]:
    """
    渲染資料夾選擇器
    
    Returns:
        Tuple[Optional[str], int]: (選擇的資料夾路徑, 圖片數量)
    """
    st.subheader("📁 選擇圖片資料夾")
    
    # 資料夾路徑輸入
    folder_path = st.text_input(
        "資料夾路徑",
        value="",
        placeholder="請輸入或貼上資料夾路徑，例如: E:/AI/pictureQA/testPic/3餅乾",
        help="支援拖放資料夾路徑到此輸入框"
    )
    
    # 瀏覽按鈕（注意：Streamlit 的檔案選擇器不支援資料夾選擇）
    st.info("💡 提示：你可以直接複製資料夾路徑並貼上到上方輸入框中")
    
    # 驗證資料夾
    if folder_path:
        is_valid, error_message = validate_directory(folder_path)
        
        if not is_valid:
            st.error(f"❌ {error_message}")
            return None, 0
        
        # 取得支援的圖片檔案
        supported_formats = config.get('processing.supported_formats', ['.png', '.jpg', '.jpeg', '.bmp', '.tiff'])
        image_files = get_supported_image_files(folder_path, supported_formats)
        
        if not image_files:
            st.warning("⚠️ 此資料夾中沒有找到支援的圖片檔案")
            st.info(f"支援的格式: {', '.join(supported_formats)}")
            return None, 0
        
        # 顯示資料夾資訊
        st.success(f"✅ 找到 {len(image_files)} 張圖片")
        
        # 顯示資料夾詳細資訊
        with st.expander("📋 資料夾詳細資訊", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**資料夾路徑:**")
                st.code(folder_path)
                
                st.write("**圖片數量:**")
                st.write(f"{len(image_files)} 張")
            
            with col2:
                st.write("**支援的格式:**")
                for fmt in supported_formats:
                    count = sum(1 for f in image_files if f.lower().endswith(fmt.lower()))
                    if count > 0:
                        st.write(f"- {fmt}: {count} 張")
        
        # 顯示部分圖片預覽
        if st.checkbox("🖼️ 預覽部分圖片", value=False):
            preview_count = min(6, len(image_files))
            st.write(f"顯示前 {preview_count} 張圖片:")
            
            # 使用列來顯示圖片
            cols = st.columns(3)
            for i in range(preview_count):
                with cols[i % 3]:
                    try:
                        st.image(
                            image_files[i], 
                            caption=Path(image_files[i]).name,
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"無法載入圖片: {Path(image_files[i]).name}")
        
        return folder_path, len(image_files)
    
    return None, 0

def render_folder_history():
    """渲染資料夾歷史記錄"""
    if 'folder_history' not in st.session_state:
        st.session_state.folder_history = []
    
    if st.session_state.folder_history:
        st.subheader("📚 最近使用的資料夾")
        
        for i, folder_path in enumerate(st.session_state.folder_history[-5:]):  # 顯示最近5個
            if st.button(f"📁 {folder_path}", key=f"history_{i}"):
                return folder_path
    
    return None

def add_to_folder_history(folder_path: str):
    """
    添加資料夾到歷史記錄
    
    Args:
        folder_path (str): 資料夾路徑
    """
    if 'folder_history' not in st.session_state:
        st.session_state.folder_history = []
    
    # 移除重複項目
    if folder_path in st.session_state.folder_history:
        st.session_state.folder_history.remove(folder_path)
    
    # 添加到開頭
    st.session_state.folder_history.insert(0, folder_path)
    
    # 限制歷史記錄數量
    st.session_state.folder_history = st.session_state.folder_history[:10]

def get_folder_info(folder_path: str) -> dict:
    """
    取得資料夾詳細資訊
    
    Args:
        folder_path (str): 資料夾路徑
        
    Returns:
        dict: 資料夾資訊
    """
    if not folder_path or not os.path.exists(folder_path):
        return {}
    
    supported_formats = config.get('processing.supported_formats', ['.png', '.jpg', '.jpeg', '.bmp', '.tiff'])
    image_files = get_supported_image_files(folder_path, supported_formats)
    
    # 計算檔案大小
    total_size = 0
    format_counts = {}
    
    for image_file in image_files:
        try:
            file_size = os.path.getsize(image_file)
            total_size += file_size
            
            # 統計格式
            ext = Path(image_file).suffix.lower()
            format_counts[ext] = format_counts.get(ext, 0) + 1
            
        except OSError:
            continue
    
    return {
        'path': folder_path,
        'image_count': len(image_files),
        'total_size_mb': total_size / (1024 * 1024),
        'format_counts': format_counts,
        'image_files': image_files
    } 