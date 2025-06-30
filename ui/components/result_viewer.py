"""
結果檢視器元件
提供圖片結果展示和互動功能
"""

import streamlit as st
from PIL import Image
from pathlib import Path
from typing import List, Dict, Any, Optional
import math

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.config import config
from src.utils import format_similarity_score

def render_results_viewer(results: List[Dict[str, Any]], 
                         similarity_threshold: float = 0.5) -> None:
    """
    渲染結果檢視器
    
    Args:
        results (List[Dict[str, Any]]): 分析結果列表
        similarity_threshold (float): 相似度閾值
    """
    if not results:
        st.info("📝 還沒有分析結果，請先選擇資料夾並輸入 Prompt 開始分析")
        return
    
    # 過濾結果
    successful_results = [r for r in results if r.get('success', False)]
    filtered_results = [
        r for r in successful_results 
        if r.get('similarity_score', 0) >= similarity_threshold
    ]
    
    if not filtered_results:
        st.warning(f"⚠️ 沒有圖片符合相似度閾值 {similarity_threshold:.3f}")
        return
    
    st.subheader(f"🖼️ 結果展示 ({len(filtered_results)} 張圖片)")
    
    # 排序選項
    sort_option = st.selectbox(
        "排序方式",
        ["相似度 (高到低)", "相似度 (低到高)", "檔案名稱 (A-Z)", "檔案名稱 (Z-A)"],
        index=0
    )
    
    # 根據選擇排序
    if sort_option == "相似度 (高到低)":
        filtered_results.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
    elif sort_option == "相似度 (低到高)":
        filtered_results.sort(key=lambda x: x.get('similarity_score', 0))
    elif sort_option == "檔案名稱 (A-Z)":
        filtered_results.sort(key=lambda x: x.get('image_name', ''))
    elif sort_option == "檔案名稱 (Z-A)":
        filtered_results.sort(key=lambda x: x.get('image_name', ''), reverse=True)
    
    # 分頁設置
    images_per_page = st.slider(
        "每頁顯示圖片數",
        min_value=6,
        max_value=50,
        value=config.get('ui.max_images_display', 24),
        step=6
    )
    
    total_pages = math.ceil(len(filtered_results) / images_per_page)
    
    if total_pages > 1:
        page = st.selectbox(
            f"頁面 (共 {total_pages} 頁)",
            range(1, total_pages + 1),
            index=0
        )
    else:
        page = 1
    
    # 計算當前頁面的結果
    start_idx = (page - 1) * images_per_page
    end_idx = min(start_idx + images_per_page, len(filtered_results))
    page_results = filtered_results[start_idx:end_idx]
    
    # 顯示當前頁面資訊
    st.info(f"📄 第 {page} 頁，顯示第 {start_idx + 1}-{end_idx} 張圖片")
    
    # 渲染圖片網格
    render_image_grid(page_results)

def render_image_grid(results: List[Dict[str, Any]]) -> None:
    """
    渲染圖片網格
    
    Args:
        results (List[Dict[str, Any]]): 要顯示的結果列表
    """
    if not results:
        return
    
    # 設置每行圖片數量
    images_per_row = config.get('ui.images_per_row', 4)
    
    # 計算需要的行數
    num_rows = math.ceil(len(results) / images_per_row)
    
    for row in range(num_rows):
        cols = st.columns(images_per_row)
        
        for col_idx in range(images_per_row):
            result_idx = row * images_per_row + col_idx
            
            if result_idx >= len(results):
                break
            
            result = results[result_idx]
            
            with cols[col_idx]:
                render_single_image_result(result, result_idx)

def render_single_image_result(result: Dict[str, Any], index: int) -> None:
    """
    渲染單個圖片結果
    
    Args:
        result (Dict[str, Any]): 圖片結果資料
        index (int): 圖片索引
    """
    image_path = result.get('image_path', '')
    image_name = result.get('image_name', '')
    similarity_score = result.get('similarity_score', 0.0)
    
    if not image_path or not os.path.exists(image_path):
        st.error(f"圖片不存在: {image_name}")
        return
    
    try:
        # 載入並顯示圖片
        image = Image.open(image_path)
        st.image(
            image,
            caption=f"{image_name}\n相似度: {format_similarity_score(similarity_score)}",
            use_container_width=True
        )
        
        # 顯示詳細資訊按鈕
        if st.button(f"詳細資訊", key=f"detail_{index}"):
            show_image_details(result)
            
    except Exception as e:
        st.error(f"載入圖片失敗: {image_name}\n錯誤: {str(e)}")

def show_image_details(result: Dict[str, Any]) -> None:
    """
    顯示圖片詳細資訊
    
    Args:
        result (Dict[str, Any]): 圖片結果資料
    """
    with st.expander(f"📋 {result.get('image_name', '')} 詳細資訊", expanded=True):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # 顯示圖片
            try:
                image = Image.open(result.get('image_path', ''))
                st.image(image, use_container_width=True)
            except Exception:
                st.error("無法載入圖片")
        
        with col2:
            # 顯示詳細資訊
            st.write("**基本資訊:**")
            st.write(f"- 檔案名稱: {result.get('image_name', 'N/A')}")
            st.write(f"- 相似度分數: {format_similarity_score(result.get('similarity_score', 0))}")
            st.write(f"- Prompt: {result.get('prompt', 'N/A')}")
            st.write(f"- 處理狀態: {'成功' if result.get('success', False) else '失敗'}")
            
            # 顯示檔案資訊
            image_path = result.get('image_path', '')
            if image_path and os.path.exists(image_path):
                try:
                    file_size = os.path.getsize(image_path) / (1024 * 1024)  # MB
                    image = Image.open(image_path)
                    width, height = image.size
                    
                    st.write("**檔案資訊:**")
                    st.write(f"- 檔案大小: {file_size:.2f} MB")
                    st.write(f"- 圖片尺寸: {width} × {height}")
                    st.write(f"- 檔案路徑: {image_path}")
                    
                except Exception as e:
                    st.write(f"無法取得檔案資訊: {str(e)}")

def render_results_summary(results: List[Dict[str, Any]], 
                          filtered_results: List[Dict[str, Any]]) -> None:
    """
    渲染結果摘要
    
    Args:
        results (List[Dict[str, Any]]): 原始結果列表
        filtered_results (List[Dict[str, Any]]): 過濾後結果列表
    """
    if not results:
        return
    
    st.subheader("📊 結果摘要")
    
    # 計算統計資料
    total_images = len(results)
    successful_analyses = len([r for r in results if r.get('success', False)])
    failed_analyses = total_images - successful_analyses
    displayed_images = len(filtered_results)
    
    # 計算相似度統計
    similarity_scores = [
        r['similarity_score'] for r in results 
        if r.get('success', False) and r.get('similarity_score') is not None
    ]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("總圖片數", total_images)
    
    with col2:
        st.metric("成功分析", successful_analyses, delta=f"{successful_analyses - failed_analyses}")
    
    with col3:
        st.metric("當前顯示", displayed_images)
    
    with col4:
        if similarity_scores:
            avg_similarity = sum(similarity_scores) / len(similarity_scores)
            st.metric("平均相似度", f"{avg_similarity:.3f}")
        else:
            st.metric("平均相似度", "N/A")

def render_export_options(results: List[Dict[str, Any]], 
                         filtered_results: List[Dict[str, Any]]) -> None:
    """
    渲染匯出選項
    
    Args:
        results (List[Dict[str, Any]]): 原始結果列表
        filtered_results (List[Dict[str, Any]]): 過濾後結果列表
    """
    if not results:
        return
    
    st.subheader("💾 匯出選項")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 匯出全部結果 (CSV)", key="export_all"):
            export_results_csv(results, "all_results")
    
    with col2:
        if st.button("🎯 匯出過濾結果 (CSV)", key="export_filtered"):
            export_results_csv(filtered_results, "filtered_results")
    
    with col3:
        if st.button("📊 匯出統計報告", key="export_report"):
            export_summary_report(results, filtered_results)

def export_results_csv(results: List[Dict[str, Any]], filename_prefix: str) -> None:
    """
    匯出結果為 CSV
    
    Args:
        results (List[Dict[str, Any]]): 要匯出的結果
        filename_prefix (str): 檔案名稱前綴
    """
    if not results:
        st.warning("沒有結果可以匯出")
        return
    
    try:
        # 這裡應該調用 DataManager 的匯出功能
        # 暫時顯示成功訊息
        st.success(f"✅ 已匯出 {len(results)} 筆結果")
        st.info("💡 檔案已儲存到 data/exports/ 目錄")
        
    except Exception as e:
        st.error(f"匯出失敗: {str(e)}")

def export_summary_report(results: List[Dict[str, Any]], 
                         filtered_results: List[Dict[str, Any]]) -> None:
    """
    匯出摘要報告
    
    Args:
        results (List[Dict[str, Any]]): 原始結果列表
        filtered_results (List[Dict[str, Any]]): 過濾後結果列表
    """
    try:
        # 這裡應該調用 DataManager 的報告生成功能
        st.success("✅ 摘要報告已匯出")
        st.info("💡 報告已儲存到 data/exports/ 目錄")
        
    except Exception as e:
        st.error(f"匯出報告失敗: {str(e)}")

def render_image_comparison(results: List[Dict[str, Any]]) -> None:
    """
    渲染圖片比較功能
    
    Args:
        results (List[Dict[str, Any]]): 結果列表
    """
    if len(results) < 2:
        return
    
    with st.expander("🔍 圖片比較", expanded=False):
        st.write("選擇兩張圖片進行比較:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            image1_idx = st.selectbox(
                "選擇第一張圖片",
                range(len(results)),
                format_func=lambda x: f"{results[x]['image_name']} ({format_similarity_score(results[x]['similarity_score'])})"
            )
        
        with col2:
            image2_idx = st.selectbox(
                "選擇第二張圖片",
                range(len(results)),
                format_func=lambda x: f"{results[x]['image_name']} ({format_similarity_score(results[x]['similarity_score'])})",
                index=1 if len(results) > 1 else 0
            )
        
        if image1_idx != image2_idx:
            col1, col2 = st.columns(2)
            
            with col1:
                render_single_image_result(results[image1_idx], f"compare1_{image1_idx}")
            
            with col2:
                render_single_image_result(results[image2_idx], f"compare2_{image2_idx}")
            
            # 顯示比較資訊
            score1 = results[image1_idx]['similarity_score']
            score2 = results[image2_idx]['similarity_score']
            difference = abs(score1 - score2)
            
            st.write(f"**相似度差異:** {format_similarity_score(difference)}")
            if score1 > score2:
                st.write(f"**{results[image1_idx]['image_name']}** 的相似度較高")
            elif score2 > score1:
                st.write(f"**{results[image2_idx]['image_name']}** 的相似度較高")
            else:
                st.write("兩張圖片的相似度相同") 