"""
驗證控制元件
提供 Ollama 多模態驗證的控制介面
"""

import streamlit as st
from typing import Optional, Dict, Any
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.config import config


def render_validation_controls() -> Dict[str, Any]:
    """
    渲染驗證控制介面
    
    Returns:
        Dict[str, Any]: 驗證設定
    """
    st.subheader("🤖 多模態現實性驗證")
    
    # 啟用/停用切換
    ollama_enabled = st.checkbox(
        "啟用 Ollama 現實性檢測",
        value=st.session_state.get('ollama_enabled', False),
        help="使用本地 Ollama 模型檢測圖片的物理合理性和品質問題"
    )
    
    if ollama_enabled:
        # 檢查 Ollama 連線狀態
        render_ollama_status()
        
        # 驗證門檻設定
        verification_threshold = st.slider(
            "二階段驗證門檻",
            min_value=0.0,
            max_value=1.0,
            value=config.get('ollama.verification_threshold', 0.6),
            step=0.01,
            help="只有 CLIP 相似度超過此值的圖片才會進行 Ollama 驗證"
        )
        
        # Prompt 編輯區域
        render_prompt_editor()
        
        # 進階設定
        with st.expander("⚙️ 進階設定", expanded=False):
            model_name = st.text_input(
                "Ollama 模型名稱",
                value=config.get('ollama.model_name', 'phi4-mini'),
                help="確保此模型已在 Ollama 中安裝"
            )
            
            timeout = st.number_input(
                "請求超時時間 (秒)",
                min_value=5,
                max_value=120,
                value=config.get('ollama.timeout', 30),
                step=5
            )
            
            confidence_threshold = st.slider(
                "最低信心度要求",
                min_value=0.0,
                max_value=1.0,
                value=config.get('ollama.confidence_threshold', 0.7),
                step=0.1,
                help="只接受信心度超過此值的驗證結果"
            )
        
        # 儲存設定到 session state
        st.session_state.ollama_enabled = True
        st.session_state.verification_threshold = verification_threshold
        st.session_state.ollama_model_name = model_name
        st.session_state.ollama_timeout = timeout
        st.session_state.confidence_threshold = confidence_threshold
        
        return {
            'enabled': True,
            'verification_threshold': verification_threshold,
            'model_name': model_name,
            'timeout': timeout,
            'confidence_threshold': confidence_threshold,
            'custom_prompt': st.session_state.get('custom_prompt', get_default_prompt())
        }
    
    else:
        st.session_state.ollama_enabled = False
        return {'enabled': False}


def render_ollama_status():
    """渲染 Ollama 連線狀態"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.write("**Ollama 服務狀態:**")
    
    with col2:
        if st.button("🔄 檢查連線", key="check_ollama"):
            check_ollama_connection()
    
    # 顯示狀態
    if 'ollama_status' in st.session_state:
        status = st.session_state.ollama_status
        if status['connected']:
            st.success(f"✅ 已連接 - {status['message']}")
            
            # 顯示目標模型狀態
            if status.get('target_model_available'):
                st.info(f"🎯 目標模型 '{status['target_model']}' 可用")
            else:
                st.warning(f"⚠️ 目標模型 '{status['target_model']}' 未找到")
            
            # 顯示可用模型
            if 'models' in status and status['models']:
                with st.expander("📋 可用模型", expanded=False):
                    for model in status['models']:
                        st.write(f"- {model}")
        else:
            st.error(f"❌ 連線失敗 - {status['message']}")
            st.info("💡 請確保 Ollama 服務已啟動，並執行: `ollama run phi4-mini`")


def check_ollama_connection():
    """檢查 Ollama 連線狀態"""
    try:
        # 動態導入以避免啟動時的依賴問題
        from src.ollama_validator import OllamaValidator
        
        validator = OllamaValidator()
        status = validator.check_connection()
        st.session_state.ollama_status = status
        
    except Exception as e:
        st.session_state.ollama_status = {
            'connected': False,
            'message': f"檢查連線時發生錯誤: {str(e)}",
            'models': [],
            'target_model_available': False
        }


def render_prompt_editor():
    """渲染 Prompt 編輯器"""
    st.subheader("📝 驗證 Prompt 設定")
    
    # 預設/自定義切換
    use_default = st.radio(
        "Prompt 來源",
        ["使用預設 Prompt", "自定義 Prompt"],
        index=0 if st.session_state.get('use_default_prompt', True) else 1,
        horizontal=True
    )
    
    if use_default == "使用預設 Prompt":
        st.session_state.use_default_prompt = True
        
        # 顯示預設 Prompt
        default_prompt = get_default_prompt()
        
        with st.expander("👁️ 預設 Prompt 內容", expanded=False):
            st.code(default_prompt, language="text")
        
        st.info("💡 預設 Prompt 會檢測物理不合理性、浮水印和印刷文字")
        
        # 儲存預設 Prompt
        st.session_state.custom_prompt = default_prompt
        
    else:
        st.session_state.use_default_prompt = False
        
        # 自定義 Prompt 編輯器
        st.write("**自定義 Prompt:**")
        
        # 提供範本按鈕
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📋 載入預設範本", key="load_default"):
                st.session_state.custom_prompt = get_default_prompt()
                st.rerun()
        
        with col2:
            if st.button("🧹 清空", key="clear_prompt"):
                st.session_state.custom_prompt = ""
                st.rerun()
        
        with col3:
            if st.button("💡 顯示說明", key="show_help"):
                st.session_state.show_prompt_help = not st.session_state.get('show_prompt_help', False)
        
        # 說明文字
        if st.session_state.get('show_prompt_help', False):
            st.info("""
            **Prompt 編寫提示:**
            - 使用 `{image_name}` 作為圖片名稱佔位符
            - 要求回應為 JSON 格式以便程式解析
            - 包含 `status`、`confidence`、`details` 等必要欄位
            - 可以加入特定的檢測項目（如浮水印、文字等）
            """)
        
        # Prompt 文字區域
        custom_prompt = st.text_area(
            "Prompt 內容",
            value=st.session_state.get('custom_prompt', get_default_prompt()),
            height=300,
            help="編輯 Ollama 驗證時使用的 Prompt",
            key="prompt_editor"
        )
        
        # 儲存自定義 Prompt
        st.session_state.custom_prompt = custom_prompt
        
        # Prompt 預覽
        if custom_prompt:
            with st.expander("👁️ Prompt 預覽 (填入範例參數)", expanded=False):
                try:
                    preview = custom_prompt.format(image_name="example_image.png")
                    st.code(preview, language="text")
                except Exception as e:
                    st.error(f"Prompt 格式錯誤: {str(e)}")


def get_default_prompt() -> str:
    """取得預設 Prompt"""
    return config.get('ollama.default_prompt', '''
Analyze for quality and realism issues:

- Impossible object interactions (body parts passing through solid surfaces, incorrect occlusion)
- Biological errors (mixed animal parts, deformed anatomy, unnatural tails, incorrect limb connections)
- Unrealistic physics (unsupported structures, floating objects, impossible gravity, missing shadows)
- Any visible text not physically part of the scene (logos, floating words, AI marks, hidden signatures)

Be VERY STRICT — minor, faint, or partial errors still count as abnormal. Assume high standards of realism unless text clearly belongs to packaging, signage, or natural labels.

Reply ONLY in JSON format:
{
  "image": "{image_name}",
  "status": "normal" or "abnormal",
  "confidence": 0.0-1.0,
  "details": "brief explanation of main issues",
  "issues": {
    "physics": ["list", "of", "physics", "problems"],
    "watermarks": ["list", "of", "text/watermark", "issues"],
    "quality": ["other", "quality", "issues"]
  }
}
'''.strip())


def render_validation_stats(validation_summary: Dict[str, Any]):
    """
    渲染驗證統計資訊
    
    Args:
        validation_summary (Dict[str, Any]): 驗證摘要
    """
    if not validation_summary or 'stats' not in validation_summary:
        return
    
    st.subheader("📊 驗證統計")
    
    stats = validation_summary['stats']
    
    # 基本統計
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("總圖片數", stats.get('total_images', 0))
    
    with col2:
        clip_success = stats.get('clip_success', 0)
        clip_total = stats.get('total_images', 0)
        clip_rate = (clip_success / clip_total * 100) if clip_total > 0 else 0
        st.metric("CLIP 成功", clip_success, f"{clip_rate:.1f}%")
    
    with col3:
        ollama_validated = stats.get('ollama_validated', 0)
        st.metric("Ollama 驗證", ollama_validated)
    
    with col4:
        final_accepted = stats.get('final_accepted', 0)
        final_total = stats.get('total_images', 0)
        accept_rate = (final_accepted / final_total * 100) if final_total > 0 else 0
        st.metric("最終接受", final_accepted, f"{accept_rate:.1f}%")
    
    # Ollama 詳細統計
    if 'ollama_stats' in validation_summary and validation_summary['ollama_stats']:
        ollama_stats = validation_summary['ollama_stats']
        
        with st.expander("🤖 Ollama 詳細統計", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("正常判定", ollama_stats.get('normal_count', 0))
            
            with col2:
                st.metric("異常判定", ollama_stats.get('abnormal_count', 0))
            
            with col3:
                avg_time = ollama_stats.get('avg_processing_time', 0)
                st.metric("平均處理時間", f"{avg_time:.2f}s")


def render_validation_results_filter(results: list) -> list:
    """
    渲染驗證結果過濾器
    
    Args:
        results (list): 驗證結果列表
        
    Returns:
        list: 過濾後的結果列表
    """
    if not results:
        return results
    
    st.subheader("🔍 驗證結果過濾")
    
    # 過濾選項
    col1, col2, col3 = st.columns(3)
    
    with col1:
        show_accepted = st.checkbox("顯示接受的圖片", value=True)
    
    with col2:
        show_rejected = st.checkbox("顯示拒絕的圖片", value=True)
    
    with col3:
        show_ollama_only = st.checkbox("只顯示 Ollama 驗證的圖片", value=False)
    
    # 應用過濾
    filtered_results = []
    
    for result in results:
        final_status = result.get('final_status', 'pending')
        ollama_status = result.get('ollama_validation', {}).get('status', 'skipped')
        
        # 狀態過濾
        if final_status == 'accepted' and not show_accepted:
            continue
        if final_status == 'rejected' and not show_rejected:
            continue
        
        # Ollama 過濾
        if show_ollama_only and ollama_status in ['skipped', 'error']:
            continue
        
        filtered_results.append(result)
    
    # 顯示過濾統計
    st.info(f"📋 顯示 {len(filtered_results)} / {len(results)} 筆結果")
    
    return filtered_results 