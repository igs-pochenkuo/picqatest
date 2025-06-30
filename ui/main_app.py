"""
主要的 Streamlit 應用程式
整合所有功能模組提供完整的使用者介面
"""

import streamlit as st
import sys
import os
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 導入核心模組
from src.config import config
from src.similarity_engine import SimilarityEngine
from src.data_manager import DataManager
from src.utils import get_supported_image_files

# 導入 UI 元件
from components.folder_selector import render_folder_selector, add_to_folder_history
from components.prompt_input import render_prompt_input, validate_prompt, render_prompt_suggestions
from components.similarity_filter import render_similarity_filter, get_filtered_results, render_filter_summary
from components.result_viewer import render_results_viewer, render_results_summary, render_export_options

def initialize_app():
    """初始化應用程式"""
    # 設置頁面配置
    st.set_page_config(
        page_title=config.get('app.title', 'PictureQA Demo'),
        page_icon=config.get('app.page_icon', '🖼️'),
        layout=config.get('app.layout', 'wide'),
        initial_sidebar_state="expanded"
    )
    
    # 確保必要目錄存在
    config.ensure_directories()
    
    # 初始化 session state
    if 'similarity_engine' not in st.session_state:
        st.session_state.similarity_engine = None
    
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = DataManager()
    
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = []
    
    if 'model_initialized' not in st.session_state:
        st.session_state.model_initialized = False

def render_header():
    """渲染頁面頭部"""
    st.title(config.get('app.title', 'PictureQA Demo'))
    st.markdown("---")
    
    # 顯示應用程式資訊
    with st.expander("ℹ️ 關於此應用程式", expanded=False):
        st.markdown("""
        **PictureQA Demo** 是一個基於 CLIP 模型的圖片與文字相似度分析工具。
        
        **主要功能:**
        - 🖼️ 批次分析圖片與文字的相似度
        - 🎚️ 即時調整相似度閾值過濾結果
        - 📊 視覺化相似度分佈統計
        - 💾 匯出分析結果為 CSV 格式
        - 🚀 支援 GPU 加速和結果快取
        
        **使用步驟:**
        1. 選擇包含圖片的資料夾
        2. 輸入英文描述 (Prompt)
        3. 開始分析並等待完成
        4. 調整相似度閾值查看結果
        5. 匯出需要的結果資料
        """)

def render_sidebar():
    """渲染側邊欄"""
    with st.sidebar:
        st.header("🛠️ 控制面板")
        
        # 模型狀態
        st.subheader("🤖 模型狀態")
        if st.session_state.model_initialized:
            st.success("✅ 模型已載入")
            
            # 顯示模型資訊
            if st.session_state.similarity_engine:
                model_info = st.session_state.similarity_engine.get_model_info()
                st.write(f"**模型:** {model_info.get('model_name', 'N/A')}")
                st.write(f"**設備:** {model_info.get('device', 'N/A')}")
                st.write(f"**快取:** {model_info.get('cache_size', 0)} 項目")
        else:
            st.warning("⚠️ 模型尚未載入")
            if st.button("🚀 載入模型"):
                load_model()
        
        # 分析狀態
        st.subheader("📊 分析狀態")
        if st.session_state.analysis_results:
            total_results = len(st.session_state.analysis_results)
            successful_results = len([r for r in st.session_state.analysis_results if r.get('success', False)])
            st.write(f"**總圖片:** {total_results}")
            st.write(f"**成功分析:** {successful_results}")
            st.write(f"**成功率:** {successful_results/total_results*100:.1f}%")
        else:
            st.info("尚無分析結果")
        
        # 快速操作
        st.subheader("⚡ 快速操作")
        
        if st.button("🗑️ 清除結果"):
            st.session_state.analysis_results = []
            st.rerun()
        
        if st.button("🧹 清除快取"):
            if st.session_state.similarity_engine:
                st.session_state.similarity_engine.clear_cache()
                st.success("快取已清除")
        
        # 最近結果
        st.subheader("📚 最近結果")
        recent_results = st.session_state.data_manager.get_recent_results(5)
        
        if recent_results:
            for result_info in recent_results:
                with st.expander(f"📄 {result_info['filename'][:20]}...", expanded=False):
                    st.write(f"**時間:** {result_info['timestamp'][:19]}")
                    st.write(f"**Prompt:** {result_info['prompt'][:30]}...")
                    st.write(f"**圖片數:** {result_info['total_images']}")
                    
                    if st.button("載入此結果", key=f"load_{result_info['filename']}"):
                        load_previous_results(result_info['file_path'])
        else:
            st.info("沒有最近的結果")

def load_model():
    """載入 CLIP 模型"""
    with st.spinner("正在載入 CLIP 模型..."):
        try:
            engine = SimilarityEngine()
            success = engine.initialize_model()
            
            if success:
                st.session_state.similarity_engine = engine
                st.session_state.model_initialized = True
                st.success("✅ 模型載入成功！")
                st.rerun()
            else:
                st.error("❌ 模型載入失敗")
                
        except Exception as e:
            st.error(f"載入模型時發生錯誤: {str(e)}")

def load_previous_results(file_path: str):
    """載入之前的分析結果"""
    try:
        data = st.session_state.data_manager.load_analysis_results(file_path)
        if data and 'results' in data:
            st.session_state.analysis_results = data['results']
            st.success(f"✅ 已載入 {len(data['results'])} 筆結果")
            st.rerun()
        else:
            st.error("載入結果失敗：檔案格式不正確")
    except Exception as e:
        st.error(f"載入結果時發生錯誤: {str(e)}")

def run_analysis(folder_path: str, prompt: str):
    """執行分析"""
    if not st.session_state.model_initialized:
        st.error("❌ 請先載入模型")
        return
    
    if not st.session_state.similarity_engine:
        st.error("❌ 相似度引擎未初始化")
        return
    
    # 取得圖片檔案列表
    supported_formats = config.get('processing.supported_formats', ['.png', '.jpg', '.jpeg', '.bmp', '.tiff'])
    image_files = get_supported_image_files(folder_path, supported_formats)
    
    if not image_files:
        st.error("❌ 資料夾中沒有找到支援的圖片檔案")
        return
    
    st.info(f"🚀 開始分析 {len(image_files)} 張圖片...")
    
    # 創建進度條
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def progress_callback(progress, message):
        progress_bar.progress(progress)
        status_text.text(message)
    
    try:
        # 執行批次分析
        results = st.session_state.similarity_engine.calculate_batch_similarity(
            image_files, prompt, progress_callback
        )
        
        # 儲存結果
        st.session_state.analysis_results = results
        
        # 儲存到檔案
        model_info = st.session_state.similarity_engine.get_model_info()
        saved_path = st.session_state.data_manager.save_analysis_results(
            results, prompt, folder_path, model_info
        )
        
        # 添加到資料夾歷史
        add_to_folder_history(folder_path)
        
        # 顯示完成訊息
        successful_count = len([r for r in results if r.get('success', False)])
        st.success(f"✅ 分析完成！成功處理 {successful_count}/{len(results)} 張圖片")
        
        if saved_path:
            st.info(f"💾 結果已儲存至: {saved_path}")
        
        progress_bar.empty()
        status_text.empty()
        
    except Exception as e:
        st.error(f"分析過程中發生錯誤: {str(e)}")
        progress_bar.empty()
        status_text.empty()

def main():
    """主函數"""
    # 初始化應用程式
    initialize_app()
    
    # 渲染頁面
    render_header()
    render_sidebar()
    
    # 主要內容區域
    tab1, tab2, tab3 = st.tabs(["🔍 分析", "📊 結果", "📈 統計"])
    
    with tab1:
        st.header("🔍 圖片相似度分析")
        
        # 資料夾選擇
        folder_path, image_count = render_folder_selector()
        
        if folder_path:
            # 智慧建議
            render_prompt_suggestions(folder_path)
            
            # Prompt 輸入
            prompt = render_prompt_input()
            
            if prompt:
                # 驗證 prompt
                is_valid, error_message = validate_prompt(prompt)
                
                if is_valid:
                    # 分析按鈕
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        if st.button("🚀 開始分析", type="primary", use_container_width=True):
                            if not st.session_state.model_initialized:
                                st.warning("⚠️ 模型尚未載入，正在自動載入...")
                                load_model()
                                if st.session_state.model_initialized:
                                    run_analysis(folder_path, prompt)
                            else:
                                run_analysis(folder_path, prompt)
                else:
                    st.error(f"❌ Prompt 驗證失敗: {error_message}")
    
    with tab2:
        st.header("📊 分析結果")
        
        if st.session_state.analysis_results:
            # 相似度過濾器
            similarity_threshold = render_similarity_filter(st.session_state.analysis_results)
            
            # 過濾結果
            filtered_results = get_filtered_results(st.session_state.analysis_results, similarity_threshold)
            
            # 過濾摘要
            render_filter_summary(st.session_state.analysis_results, filtered_results, similarity_threshold)
            
            # 結果檢視器
            render_results_viewer(filtered_results, similarity_threshold)
            
            # 匯出選項
            render_export_options(st.session_state.analysis_results, filtered_results)
            
        else:
            st.info("📝 還沒有分析結果，請先在「分析」頁籤中進行分析")
    
    with tab3:
        st.header("📈 統計資訊")
        
        if st.session_state.analysis_results:
            # 結果摘要
            filtered_results = get_filtered_results(
                st.session_state.analysis_results, 
                st.session_state.get('similarity_threshold', 0.5)
            )
            render_results_summary(st.session_state.analysis_results, filtered_results)
            
            # 顯示詳細統計報告
            with st.expander("📋 詳細統計報告", expanded=False):
                if st.session_state.analysis_results:
                    # 這裡可以顯示更詳細的統計資訊
                    results = st.session_state.analysis_results
                    successful_results = [r for r in results if r.get('success', False)]
                    
                    if successful_results:
                        scores = [r['similarity_score'] for r in successful_results]
                        
                        st.write("**分數分佈統計:**")
                        st.write(f"- 最高分數: {max(scores):.4f}")
                        st.write(f"- 最低分數: {min(scores):.4f}")
                        st.write(f"- 平均分數: {sum(scores)/len(scores):.4f}")
                        
                        import statistics
                        st.write(f"- 中位數: {statistics.median(scores):.4f}")
                        if len(scores) > 1:
                            st.write(f"- 標準差: {statistics.stdev(scores):.4f}")
        else:
            st.info("📝 還沒有分析結果，請先進行分析")

if __name__ == "__main__":
    main() 