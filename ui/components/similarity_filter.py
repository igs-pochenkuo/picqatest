"""
相似度過濾器元件
提供相似度閾值調整和即時過濾功能
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any, Optional
import pandas as pd

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.config import config

def render_similarity_filter(results: List[Dict[str, Any]]) -> float:
    """
    渲染相似度過濾器
    
    Args:
        results (List[Dict[str, Any]]): 分析結果列表
        
    Returns:
        float: 選擇的相似度閾值
    """
    if not results:
        return config.get('ui.similarity_threshold_default', 0.5)
    
    st.subheader("🎚️ 相似度過濾器")
    
    # 取得成功的相似度分數
    similarity_scores = [
        result['similarity_score'] 
        for result in results 
        if result.get('success', False) and result.get('similarity_score') is not None
    ]
    
    if not similarity_scores:
        st.warning("⚠️ 沒有有效的相似度分數可以過濾")
        return config.get('ui.similarity_threshold_default', 0.5)
    
    # 計算統計資料
    min_score = min(similarity_scores)
    max_score = max(similarity_scores)
    mean_score = sum(similarity_scores) / len(similarity_scores)
    
    # 顯示統計資訊
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("總圖片數", len(results))
    with col2:
        st.metric("有效分數", len(similarity_scores))
    with col3:
        st.metric("平均相似度", f"{mean_score:.3f}")
    with col4:
        st.metric("分數範圍", f"{min_score:.3f} - {max_score:.3f}")
    
    # 相似度閾值滑桿
    threshold = st.slider(
        "相似度閾值",
        min_value=config.get('ui.similarity_threshold_min', 0.0),
        max_value=config.get('ui.similarity_threshold_max', 1.0),
        value=config.get('ui.similarity_threshold_default', 0.5),
        step=config.get('ui.similarity_threshold_step', 0.01),
        format="%.3f",
        help="調整此滑桿來過濾顯示符合相似度要求的圖片"
    )
    
    # 計算過濾後的結果
    filtered_results = [
        result for result in results
        if result.get('success', False) and 
           result.get('similarity_score', 0) >= threshold
    ]
    
    # 顯示過濾結果統計
    filtered_count = len(filtered_results)
    total_count = len(similarity_scores)
    percentage = (filtered_count / total_count * 100) if total_count > 0 else 0
    
    st.info(f"📊 符合閾值 {threshold:.3f} 的圖片: **{filtered_count}** 張 ({percentage:.1f}%)")
    
    # 顯示分佈圖表
    render_similarity_distribution(similarity_scores, threshold)
    
    return threshold

def render_similarity_distribution(scores: List[float], threshold: float):
    """
    渲染相似度分佈圖表
    
    Args:
        scores (List[float]): 相似度分數列表
        threshold (float): 當前閾值
    """
    if not scores:
        return
    
    st.subheader("📊 相似度分佈圖")
    
    # 創建直方圖
    fig = go.Figure()
    
    # 添加直方圖
    fig.add_trace(go.Histogram(
        x=scores,
        nbinsx=30,
        name='相似度分佈',
        marker_color='lightblue',
        opacity=0.7
    ))
    
    # 添加閾值線
    fig.add_vline(
        x=threshold,
        line_dash="dash",
        line_color="red",
        annotation_text=f"閾值: {threshold:.3f}",
        annotation_position="top"
    )
    
    # 設置圖表布局
    fig.update_layout(
        title="相似度分數分佈",
        xaxis_title="相似度分數",
        yaxis_title="圖片數量",
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 顯示閾值統計表
    render_threshold_statistics(scores)

def render_threshold_statistics(scores: List[float]):
    """
    渲染不同閾值的統計表
    
    Args:
        scores (List[float]): 相似度分數列表
    """
    if not scores:
        return
    
    with st.expander("📈 不同閾值統計", expanded=False):
        # 預設閾值
        thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        
        # 計算每個閾值的統計
        stats_data = []
        total_count = len(scores)
        
        for threshold in thresholds:
            passed_count = sum(1 for score in scores if score >= threshold)
            percentage = (passed_count / total_count * 100) if total_count > 0 else 0
            
            stats_data.append({
                '閾值': f"{threshold:.1f}",
                '通過圖片數': passed_count,
                '通過率': f"{percentage:.1f}%"
            })
        
        # 顯示表格
        df = pd.DataFrame(stats_data)
        st.dataframe(df, use_container_width=True)

def render_quick_filters(results: List[Dict[str, Any]]) -> Optional[float]:
    """
    渲染快速過濾器按鈕
    
    Args:
        results (List[Dict[str, Any]]): 分析結果列表
        
    Returns:
        Optional[float]: 選擇的閾值，如果沒有選擇則返回 None
    """
    if not results:
        return None
    
    st.subheader("⚡ 快速過濾")
    
    # 快速過濾選項
    quick_filters = [
        ("顯示全部", 0.0),
        ("低相似度", 0.2),
        ("中等相似度", 0.5),
        ("高相似度", 0.7),
        ("極高相似度", 0.9)
    ]
    
    cols = st.columns(len(quick_filters))
    
    for i, (label, threshold) in enumerate(quick_filters):
        with cols[i]:
            if st.button(f"{label}\n(≥{threshold:.1f})", key=f"quick_filter_{i}"):
                return threshold
    
    return None

def calculate_optimal_threshold(scores: List[float], target_percentage: float = 0.5) -> float:
    """
    計算最佳閾值
    
    Args:
        scores (List[float]): 相似度分數列表
        target_percentage (float): 目標通過率 (0-1)
        
    Returns:
        float: 建議的閾值
    """
    if not scores:
        return 0.5
    
    sorted_scores = sorted(scores, reverse=True)
    target_index = int(len(sorted_scores) * target_percentage)
    
    if target_index >= len(sorted_scores):
        return min(scores)
    
    return sorted_scores[target_index]

def render_optimal_threshold_suggestion(scores: List[float]):
    """
    渲染最佳閾值建議
    
    Args:
        scores (List[float]): 相似度分數列表
    """
    if not scores:
        return
    
    with st.expander("🎯 智慧閾值建議", expanded=False):
        st.write("根據分數分佈的建議閾值:")
        
        suggestions = [
            ("保留前 10%", calculate_optimal_threshold(scores, 0.1)),
            ("保留前 25%", calculate_optimal_threshold(scores, 0.25)),
            ("保留前 50%", calculate_optimal_threshold(scores, 0.5)),
            ("保留前 75%", calculate_optimal_threshold(scores, 0.75))
        ]
        
        cols = st.columns(2)
        for i, (description, threshold) in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(f"{description}: {threshold:.3f}", key=f"suggestion_{i}"):
                    st.session_state.similarity_threshold = threshold
                    st.rerun()

def get_filtered_results(results: List[Dict[str, Any]], threshold: float) -> List[Dict[str, Any]]:
    """
    根據閾值過濾結果
    
    Args:
        results (List[Dict[str, Any]]): 原始結果列表
        threshold (float): 相似度閾值
        
    Returns:
        List[Dict[str, Any]]: 過濾後的結果列表
    """
    return [
        result for result in results
        if result.get('success', False) and 
           result.get('similarity_score', 0) >= threshold
    ]

def render_filter_summary(original_results: List[Dict[str, Any]], 
                         filtered_results: List[Dict[str, Any]], 
                         threshold: float):
    """
    渲染過濾摘要
    
    Args:
        original_results (List[Dict[str, Any]]): 原始結果列表
        filtered_results (List[Dict[str, Any]]): 過濾後結果列表
        threshold (float): 使用的閾值
    """
    if not original_results:
        return
    
    # 計算統計
    total_count = len(original_results)
    filtered_count = len(filtered_results)
    removed_count = total_count - filtered_count
    
    # 顯示摘要卡片
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "原始圖片",
            total_count,
            help="處理的總圖片數量"
        )
    
    with col2:
        st.metric(
            "符合條件",
            filtered_count,
            help=f"相似度 ≥ {threshold:.3f} 的圖片數量"
        )
    
    with col3:
        st.metric(
            "被過濾",
            removed_count,
            delta=f"-{removed_count}",
            delta_color="inverse",
            help="被過濾掉的圖片數量"
        )
    
    with col4:
        percentage = (filtered_count / total_count * 100) if total_count > 0 else 0
        st.metric(
            "通過率",
            f"{percentage:.1f}%",
            help="符合閾值條件的圖片比例"
        ) 