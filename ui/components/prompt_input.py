"""
Prompt 輸入元件
提供文字提示輸入和管理功能
"""

import streamlit as st
from typing import Optional, List

def render_prompt_input() -> Optional[str]:
    """
    渲染 Prompt 輸入介面
    
    Returns:
        Optional[str]: 輸入的 prompt 文字
    """
    st.subheader("📝 輸入文字提示 (Prompt)")
    
    # 提供一些範例 prompts
    example_prompts = [
        "cookies on a plate",
        "a red apple on the table",
        "a book on a wooden desk",
        "a plastic water bottle",
        "jam jar on kitchen counter",
        "breakfast cereal in a bowl",
        "cheese on cutting board",
        "bread loaf on counter",
        "cooking pot with lid",
        "mouse trap device"
    ]
    
    # 範例選擇
    with st.expander("💡 範例 Prompts", expanded=False):
        st.write("點擊下方範例可以快速填入:")
        
        # 使用列來顯示範例
        cols = st.columns(2)
        for i, example in enumerate(example_prompts):
            with cols[i % 2]:
                if st.button(f"📋 {example}", key=f"example_{i}"):
                    st.session_state.prompt_input = example
    
    # 主要輸入區域
    prompt = st.text_area(
        "Prompt 文字",
        value=st.session_state.get('prompt_input', ''),
        height=100,
        placeholder="請輸入英文描述，例如: 'cookies on a plate'",
        help="建議使用簡潔明確的英文描述，這將用於與圖片進行相似度比較",
        key="prompt_input"
    )
    
    # Prompt 驗證和提示
    if prompt:
        prompt = prompt.strip()
        
        # 基本驗證
        if len(prompt) < 3:
            st.warning("⚠️ Prompt 太短，建議至少3個字元")
            return None
        
        if len(prompt) > 1000:
            st.warning("⚠️ Prompt 太長，建議不超過1000個字元")
            return None
        
        # 顯示 Prompt 資訊
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("字元數", len(prompt))
        with col2:
            st.metric("單詞數", len(prompt.split()))
        with col3:
            # 簡單的語言檢測（檢查是否包含中文字元）
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in prompt)
            language = "中文/混合" if has_chinese else "英文"
            st.metric("語言", language)
        
        # 語言建議
        if has_chinese:
            st.info("💡 建議使用英文 Prompt 以獲得更好的效果，因為 CLIP 模型主要在英文資料上訓練")
        
        # 顯示處理後的 Prompt
        st.success(f"✅ 將使用的 Prompt: \"{prompt}\"")
        
        # 添加到歷史記錄
        add_to_prompt_history(prompt)
        
        return prompt
    
    return None

def render_prompt_history():
    """渲染 Prompt 歷史記錄"""
    if 'prompt_history' not in st.session_state:
        st.session_state.prompt_history = []
    
    if st.session_state.prompt_history:
        st.subheader("📚 最近使用的 Prompts")
        
        for i, historical_prompt in enumerate(st.session_state.prompt_history[-10:]):  # 顯示最近10個
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.write(f"📝 {historical_prompt}")
            
            with col2:
                if st.button("使用", key=f"use_history_{i}"):
                    st.session_state.prompt_input = historical_prompt
                    st.rerun()

def add_to_prompt_history(prompt: str):
    """
    添加 Prompt 到歷史記錄
    
    Args:
        prompt (str): Prompt 文字
    """
    if 'prompt_history' not in st.session_state:
        st.session_state.prompt_history = []
    
    # 移除重複項目
    if prompt in st.session_state.prompt_history:
        st.session_state.prompt_history.remove(prompt)
    
    # 添加到開頭
    st.session_state.prompt_history.insert(0, prompt)
    
    # 限制歷史記錄數量
    st.session_state.prompt_history = st.session_state.prompt_history[:20]

def get_prompt_suggestions(folder_name: str) -> List[str]:
    """
    根據資料夾名稱提供 Prompt 建議
    
    Args:
        folder_name (str): 資料夾名稱
        
    Returns:
        List[str]: 建議的 Prompts
    """
    # 資料夾名稱到英文描述的映射
    folder_to_prompt = {
        '餅乾': ['cookies', 'biscuits', 'sweet cookies on plate', 'chocolate chip cookies'],
        '陷阱': ['trap', 'mouse trap', 'animal trap device', 'mechanical trap'],
        '鍋蓋': ['pot lid', 'cooking pot cover', 'kitchen pot lid', 'metal pot cover'],
        '書本': ['book', 'books on table', 'open book', 'reading book'],
        '塑膠水壺': ['plastic water bottle', 'water bottle', 'plastic bottle', 'drinking bottle'],
        '果醬': ['jam jar', 'fruit jam', 'jam on table', 'glass jar with jam'],
        '麥片': ['cereal', 'breakfast cereal', 'cereal in bowl', 'oat cereal'],
        '起司': ['cheese', 'cheese on board', 'sliced cheese', 'cheese block'],
        '麵包': ['bread', 'bread loaf', 'sliced bread', 'fresh bread'],
        '果醬麵包': ['jam bread', 'bread with jam', 'jam sandwich', 'jam on bread']
    }
    
    suggestions = []
    
    # 檢查資料夾名稱是否包含已知的關鍵詞
    for key, prompts in folder_to_prompt.items():
        if key in folder_name:
            suggestions.extend(prompts)
    
    # 如果沒有找到匹配的，提供通用建議
    if not suggestions:
        suggestions = [
            f"object in the image",
            f"item on table",
            f"food item",
            f"kitchen item"
        ]
    
    return suggestions[:5]  # 最多返回5個建議

def render_prompt_suggestions(folder_path: str):
    """
    根據資料夾路徑渲染 Prompt 建議
    
    Args:
        folder_path (str): 資料夾路徑
    """
    if not folder_path:
        return
    
    from pathlib import Path
    folder_name = Path(folder_path).name
    
    suggestions = get_prompt_suggestions(folder_name)
    
    if suggestions:
        st.subheader("🎯 智慧建議")
        st.write(f"根據資料夾名稱 \"{folder_name}\" 的建議:")
        
        cols = st.columns(min(len(suggestions), 3))
        for i, suggestion in enumerate(suggestions):
            with cols[i % 3]:
                if st.button(f"🎯 {suggestion}", key=f"suggestion_{i}"):
                    st.session_state.prompt_input = suggestion
                    st.rerun()

def validate_prompt(prompt: str) -> tuple[bool, str]:
    """
    驗證 Prompt 是否有效
    
    Args:
        prompt (str): 要驗證的 Prompt
        
    Returns:
        tuple[bool, str]: (是否有效, 錯誤訊息)
    """
    if not prompt or not prompt.strip():
        return False, "Prompt 不能為空"
    
    prompt = prompt.strip()
    
    if len(prompt) < 3:
        return False, "Prompt 太短，至少需要3個字元"
    
    if len(prompt) > 1000:
        return False, "Prompt 太長，不能超過1000個字元"
    
    # 檢查是否包含特殊字元（可能會影響處理）
    import re
    if re.search(r'[<>{}[\]\\|`~]', prompt):
        return False, "Prompt 包含不支援的特殊字元"
    
    return True, "" 