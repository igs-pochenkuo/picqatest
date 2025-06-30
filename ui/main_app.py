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
from components.validation_controls import render_validation_controls, render_validation_stats, render_validation_results_filter

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
    
    if 'validation_engine' not in st.session_state:
        st.session_state.validation_engine = None
    
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = DataManager()
    
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = []
    
    if 'validation_summary' not in st.session_state:
        st.session_state.validation_summary = None
    
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
        - 🤖 Ollama 多模態現實性驗證 (可選)
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
    """載入驗證引擎（包含 CLIP 和 Ollama）"""
    with st.spinner("正在載入驗證引擎..."):
        try:
            from src.validation_engine import ValidationEngine
            
            engine = ValidationEngine()
            success = engine.initialize()
            
            if success:
                st.session_state.validation_engine = engine
                st.session_state.similarity_engine = engine.similarity_engine  # 保持向後兼容
                st.session_state.model_initialized = True
                st.success("✅ 驗證引擎載入成功！")
                st.rerun()
            else:
                st.error("❌ 驗證引擎載入失敗")
                
        except Exception as e:
            st.error(f"載入驗證引擎時發生錯誤: {str(e)}")

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

def run_analysis(folder_path: str, prompt: str, validation_settings: dict = None):
    """執行分析（支援二階段驗證）"""
    if not st.session_state.model_initialized:
        st.error("❌ 請先載入模型")
        return
    
    # 取得圖片檔案列表
    supported_formats = config.get('processing.supported_formats', ['.png', '.jpg', '.jpeg', '.bmp', '.tiff'])
    image_files = get_supported_image_files(folder_path, supported_formats)
    
    if not image_files:
        st.error("❌ 資料夾中沒有找到支援的圖片檔案")
        return
    
    # 決定使用哪種分析方式
    use_validation = validation_settings and validation_settings.get('enabled', False)
    
    if use_validation and st.session_state.validation_engine:
        st.info(f"🚀 開始二階段驗證分析 {len(image_files)} 張圖片...")
        
        # 更新驗證引擎設定
        st.session_state.validation_engine.update_settings({
            'ollama_enabled': True,
            'verification_threshold': validation_settings.get('verification_threshold', 0.6),
            'confidence_threshold': validation_settings.get('confidence_threshold', 0.7),
            'custom_prompt': validation_settings.get('custom_prompt')
        })
        
        # 創建進度條
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def progress_callback(progress, message):
            progress_bar.progress(progress)
            status_text.text(message)
        
        try:
            # 執行二階段驗證分析
            results = st.session_state.validation_engine.analyze_with_validation(
                image_files, prompt, progress_callback
            )
            
            # 取得驗證摘要
            validation_summary = st.session_state.validation_engine.get_validation_summary()
            st.session_state.validation_summary = validation_summary
            
            # 儲存結果
            st.session_state.analysis_results = results
            
            # 顯示完成訊息
            accepted_count = len([r for r in results if r.get('final_status') == 'accepted'])
            rejected_count = len([r for r in results if r.get('final_status') == 'rejected'])
            
            st.success(f"✅ 二階段驗證完成！")
            st.info(f"📊 結果統計: {accepted_count} 張接受, {rejected_count} 張拒絕")
            
        except Exception as e:
            st.error(f"二階段驗證分析時發生錯誤: {str(e)}")
            return
    
    else:
        # 傳統 CLIP 分析
        if not st.session_state.similarity_engine:
            st.error("❌ 相似度引擎未初始化")
            return
        
        st.info(f"🚀 開始 CLIP 相似度分析 {len(image_files)} 張圖片...")
        
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
            
            # 轉換為統一格式（向後兼容）
            enhanced_results = []
            for result in results:
                enhanced_result = {
                    'image_path': result['image_path'],
                    'image_name': Path(result['image_path']).name,
                    'prompt': prompt,
                    'similarity_score': result.get('similarity_score', 0.0),
                    'clip_status': 'success' if result.get('success', False) else 'failed',
                    'ollama_validation': {
                        'enabled': False,
                        'status': 'skipped',
                        'confidence': 0.0,
                        'details': '',
                        'issues': {'physics': [], 'watermarks': [], 'quality': []},
                        'processing_time': 0.0
                    },
                    'final_status': 'accepted' if result.get('success', False) else 'rejected'
                }
                enhanced_results.append(enhanced_result)
            
            # 儲存結果
            st.session_state.analysis_results = enhanced_results
            
            # 顯示完成訊息
            successful_count = len([r for r in enhanced_results if r.get('clip_status') == 'success'])
            st.success(f"✅ CLIP 分析完成！成功處理 {successful_count}/{len(enhanced_results)} 張圖片")
            
        except Exception as e:
            st.error(f"CLIP 分析時發生錯誤: {str(e)}")
            return
    
    # 儲存到檔案
    try:
        model_info = st.session_state.similarity_engine.get_model_info() if st.session_state.similarity_engine else {}
        saved_path = st.session_state.data_manager.save_analysis_results(
            st.session_state.analysis_results, prompt, folder_path, model_info
        )
        
        # 添加到資料夾歷史
        add_to_folder_history(folder_path)
        
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
                    # 驗證控制
                    st.markdown("---")
                    validation_settings = render_validation_controls()
                    
                    # 分析按鈕
                    st.markdown("---")
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        button_text = "🚀 開始二階段驗證分析" if validation_settings.get('enabled') else "🚀 開始 CLIP 分析"
                        if st.button(button_text, type="primary", use_container_width=True):
                            if not st.session_state.model_initialized:
                                st.warning("⚠️ 模型尚未載入，正在自動載入...")
                                load_model()
                                if st.session_state.model_initialized:
                                    run_analysis(folder_path, prompt, validation_settings)
                            else:
                                run_analysis(folder_path, prompt, validation_settings)
                else:
                    st.error(f"❌ Prompt 驗證失敗: {error_message}")
    
    with tab2:
        st.header("📊 分析結果")
        
        if st.session_state.analysis_results:
            # 驗證結果過濾器（如果有驗證結果）
            has_validation = any(r.get('ollama_validation', {}).get('enabled', False) for r in st.session_state.analysis_results)
            
            if has_validation:
                filtered_by_validation = render_validation_results_filter(st.session_state.analysis_results)
            else:
                filtered_by_validation = st.session_state.analysis_results
            
            # 相似度過濾器
            similarity_threshold = render_similarity_filter(filtered_by_validation)
            
            # 過濾結果
            filtered_results = get_filtered_results(filtered_by_validation, similarity_threshold)
            
            # 過濾摘要
            render_filter_summary(filtered_by_validation, filtered_results, similarity_threshold)
            
            # 結果檢視器
            render_results_viewer(filtered_results, similarity_threshold)
            
            # 匯出選項
            render_export_options(st.session_state.analysis_results, filtered_results)
            
        else:
            st.info("📝 還沒有分析結果，請先在「分析」頁籤中進行分析")
    
    with tab3:
        st.header("📈 統計資訊")
        
        if st.session_state.analysis_results:
            # 驗證統計（如果有的話）
            if st.session_state.validation_summary:
                render_validation_stats(st.session_state.validation_summary)
                st.markdown("---")
            
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