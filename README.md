# PictureQA Demo - 圖片與文字相似度分析工具 (二階段驗證版)

基於 CLIP 模型的圖片與文字相似度分析工具，現在支援 **Ollama 多模態現實性驗證**！提供直觀的 Web 介面來批次處理圖片，不僅分析語義相似度，還能檢測圖片的物理合理性。

## 🌟 主要功能

### 核心分析功能
- 🖼️ **批次分析**: 一次處理整個資料夾的圖片
- 🎚️ **即時過濾**: 調整相似度閾值即時查看結果
- 📊 **視覺化統計**: 相似度分佈圖表和統計資訊
- 💾 **結果匯出**: 支援 CSV 格式匯出
- 🚀 **效能優化**: GPU 加速和智慧快取
- 🎯 **智慧建議**: 根據資料夾名稱提供 Prompt 建議

### 🆕 二階段驗證功能
- 🤖 **Ollama 整合**: 使用本地多模態模型進行現實性檢測
- 🔍 **物理合理性檢測**: 識別浮空物體、違反重力等不合理現象
- 🏷️ **浮水印檢測**: 過濾含有浮水印、版權標記的圖片
- 📰 **印刷文字檢測**: 識別雜誌封面、商品包裝上的不當文字
- ⚙️ **可配置驗證**: 自定義驗證門檻和 Prompt
- 📈 **詳細統計**: 提供二階段驗證的完整統計報告

## 🛠️ 技術架構

- **後端**: Python 3.8+
- **AI 模型**: 
  - OpenCLIP (ViT-B-32) - 語義相似度分析
  - Ollama (phi4-mini) - 現實性驗證
- **前端介面**: Streamlit
- **資料處理**: PyTorch, PIL, Pandas
- **視覺化**: Matplotlib, Plotly
- **API 通訊**: Requests (Ollama API)

## 📦 安裝說明

### 1. 環境需求

- Python 3.8 或更高版本
- CUDA (可選，用於 GPU 加速)
- Ollama (用於二階段驗證，可選)

### 2. 安裝 Python 依賴套件

```bash
pip install -r requirements.txt
```

### 3. 安裝 Ollama (可選)

如果要使用二階段驗證功能，需要安裝 Ollama：

#### Windows/macOS/Linux:
```bash
# 下載並安裝 Ollama
# 訪問 https://ollama.ai 下載安裝程式

# 安裝 phi4-mini 模型
ollama pull phi4-mini
```

### 4. 驗證安裝

```bash
# 驗證 Python 套件
python -c "import torch; import open_clip; print('Python 套件安裝成功！')"

# 驗證 Ollama (可選)
ollama list
```

## 🚀 使用方法

### 1. 啟動應用程式

```bash
streamlit run ui/main_app.py
```

或使用啟動腳本：

```bash
python run.py
```

應用程式將在瀏覽器中自動開啟，預設地址為 `http://localhost:8501`

### 2. 基本使用步驟

#### 傳統 CLIP 分析模式
1. **選擇資料夾**: 輸入或貼上包含圖片的資料夾路徑
2. **輸入 Prompt**: 輸入英文描述，例如 "cookies on a plate"
3. **開始分析**: 點擊「開始 CLIP 分析」按鈕
4. **查看結果**: 在「結果」頁籤中調整相似度閾值查看過濾結果
5. **匯出資料**: 將結果匯出為 CSV 格式

#### 🆕 二階段驗證模式
1. **選擇資料夾**: 輸入包含圖片的資料夾路徑
2. **輸入 Prompt**: 輸入英文描述
3. **啟用多模態驗證**: 勾選「啟用 Ollama 現實性檢測」
4. **配置驗證設定**:
   - 設定二階段驗證門檻 (建議 0.6)
   - 選擇使用預設或自定義 Prompt
   - 調整進階設定 (可選)
5. **開始分析**: 點擊「開始二階段驗證分析」按鈕
6. **查看結果**: 檢視 CLIP 相似度和 Ollama 驗證結果
7. **統計分析**: 在「統計」頁籤查看詳細驗證報告

### 3. 範例使用

假設你有一個包含餅乾圖片的資料夾：

```
E:/AI/pictureQA/testPic/3餅乾/
├── ComfyUI_00224_.png  (正常餅乾圖片)
├── ComfyUI_00225_.png  (有浮水印的圖片)
├── ComfyUI_00226_.png  (物理不合理的圖片)
└── ...
```

**二階段驗證流程**:
1. 資料夾路徑: `E:/AI/pictureQA/testPic/3餅乾`
2. Prompt: `cookies on a plate`
3. 啟用 Ollama 驗證，門檻設為 0.6
4. 系統會先用 CLIP 分析相似度
5. 對相似度 ≥ 0.6 的圖片進行 Ollama 現實性檢測
6. 最終只保留物理合理且無浮水印的圖片

## 📁 專案結構

```
pictureQA/
├── src/                          # 核心功能模組
│   ├── config.py                # 配置管理
│   ├── similarity_engine.py     # CLIP 相似度計算引擎
│   ├── ollama_validator.py      # 🆕 Ollama 驗證引擎
│   ├── validation_engine.py     # 🆕 二階段驗證整合引擎
│   ├── data_manager.py          # 資料管理器
│   └── utils.py                 # 工具函數
├── ui/                           # 使用者介面
│   ├── main_app.py              # 主應用程式
│   └── components/              # UI 元件
│       ├── folder_selector.py
│       ├── prompt_input.py
│       ├── similarity_filter.py
│       ├── result_viewer.py
│       └── validation_controls.py  # 🆕 驗證控制介面
├── data/                         # 資料目錄
│   ├── results/                 # 分析結果
│   ├── exports/                 # 匯出檔案
│   └── cache/                   # 快取檔案
├── testPic/                      # 測試圖片
├── config.yaml                  # 應用配置 (含 Ollama 設定)
├── requirements.txt             # 依賴套件
├── run.py                       # 啟動腳本
└── README.md                    # 說明文件
```

## ⚙️ 配置選項

編輯 `config.yaml` 檔案來自訂應用程式設定：

```yaml
# CLIP 模型設定
model:
  name: "ViT-B-32"
  pretrained: "laion2b_s34b_b79k"

# 🆕 Ollama 多模態驗證配置
ollama:
  enabled: false                    # 預設關閉
  model_name: "phi4-mini"          # Ollama 模型名稱
  api_url: "http://localhost:11434" # Ollama API 地址
  timeout: 30                       # 請求超時時間
  verification_threshold: 0.6       # 二階段驗證門檻
  confidence_threshold: 0.7         # 最低信心度要求
  
  # 預設驗證 Prompt
  default_prompt: |
    Analyze this image for quality and realism issues. Check for:
    
    Physical Realism:
    - Objects floating without proper support
    - Impossible physics or gravity violations
    - Unrealistic proportions or scaling
    - Contradictory lighting or shadows
    
    Image Quality Issues:
    - Watermarks or copyright marks
    - Magazine-style text overlays
    - Publisher logos or branding
    - Stock photo watermarks
    - Any printed text that shouldn't be part of the actual object/scene
    
    Reply ONLY in JSON format: {...}

# 處理設定
processing:
  batch_size: 32
  supported_formats: [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]
  max_image_size: 1024

# UI 設定
ui:
  similarity_threshold_default: 0.5
  images_per_row: 4
  max_images_display: 100
```

## 🎯 使用技巧

### 1. Prompt 設計建議

#### CLIP Prompt (語義分析)
- 使用簡潔明確的英文描述
- 避免過於複雜的句子
- 可以包含物體、顏色、位置等描述
- 範例：
  - `"red apple on table"`
  - `"cookies on a plate"`
  - `"plastic water bottle"`

#### 🆕 Ollama Prompt (現實性驗證)
- 專注於檢測項目的明確定義
- 要求 JSON 格式回應以便程式解析
- 可自定義檢測重點（物理、浮水印、文字等）
- 建議包含信心度評估

### 2. 二階段驗證策略

#### 門檻設定建議
- **驗證門檻 (0.6)**: 只對高相似度圖片進行昂貴的 Ollama 驗證
- **信心度門檻 (0.7)**: 只接受高信心度的異常判定
- **超時設定 (30s)**: 根據模型大小和硬體調整

#### 效能優化
- 先用快速的 CLIP 過濾，再用慢速的 Ollama 精檢
- 批次處理減少 API 呼叫開銷
- 合理設定門檻避免過度驗證

### 3. 結果分析

#### 傳統模式
- **相似度閾值**: 通常 0.3-0.7 是比較有意義的範圍
- **統計圖表**: 查看分佈圖了解整體相似度情況

#### 🆕 驗證模式
- **接受/拒絕統計**: 了解驗證效果
- **驗證詳情**: 查看具體的物理問題和品質問題
- **信心度分析**: 評估驗證結果的可信度

## 🐛 常見問題

### Q: Ollama 連線失敗

**A**: 
1. 確保 Ollama 服務已啟動: `ollama serve`
2. 檢查模型是否已安裝: `ollama list`
3. 確認 API 地址正確 (預設 `http://localhost:11434`)

### Q: 二階段驗證很慢

**A**: 
1. 提高驗證門檻，減少需要驗證的圖片數量
2. 使用更快的 Ollama 模型
3. 調整超時設定避免等待過久

### Q: Ollama 驗證結果不準確

**A**: 
1. 嘗試調整自定義 Prompt，更明確描述檢測需求
2. 使用更大的模型 (如 llama3.2-vision)
3. 調整信心度門檻，只接受高信心度結果

### Q: 模型載入失敗

**A**: 檢查網路連線，首次運行需要下載模型檔案。也可以嘗試更換預訓練模型。

### Q: 記憶體不足

**A**: 減少 `batch_size` 或 `max_image_size` 設定，或使用較小的圖片。

## 📊 效能基準

### CLIP 分析效能
| 硬體配置 | 100張圖片處理時間 | 記憶體使用 |
|---------|-----------------|-----------|
| CPU (Intel i7) | ~2-3 分鐘 | ~2GB |
| GPU (RTX 3060) | ~30-60 秒 | ~4GB |
| GPU (RTX 4090) | ~15-30 秒 | ~6GB |

### 🆕 二階段驗證效能
| Ollama 模型 | 單張圖片驗證時間 | 記憶體使用 | 準確度 |
|------------|----------------|-----------|--------|
| phi4-mini | ~2-5 秒 | ~2GB | 良好 |
| llama3.2-vision | ~5-10 秒 | ~4GB | 優秀 |
| qwen2-vl | ~3-8 秒 | ~3GB | 優秀 |

## 🔄 工作流程

### 傳統模式
```
圖片輸入 → CLIP 分析 → 相似度過濾 → 結果輸出
```

### 🆕 二階段驗證模式
```
圖片輸入 → CLIP 分析 → 相似度 ≥ 門檻？ → Ollama 驗證 → 現實性判定 → 最終結果
            ↓              ↓                    ↓
        低相似度直接過濾   高相似度進入二階段    normal/abnormal
```

## 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request！

1. Fork 專案
2. 創建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

## 📝 更新日誌

### v2.0.0 (2024-01-15) - 二階段驗證版
- 🎉 **重大更新**: 加入 Ollama 多模態現實性驗證
- 🤖 **物理合理性檢測**: 識別浮空物體、重力違反等問題
- 🏷️ **浮水印檢測**: 過濾含有浮水印的圖片
- 📰 **印刷文字檢測**: 識別不當的文字覆蓋
- ⚙️ **可配置驗證**: 自定義驗證門檻和 Prompt
- 📊 **統計增強**: 詳細的二階段驗證統計報告
- 🔧 **架構重構**: 新增 ValidationEngine 統一管理
- 🎨 **UI 升級**: 新增驗證控制介面和結果過濾器

### v1.0.0 (2024-01-01)
- 🎉 初始版本發布
- ✨ 基本的圖片相似度分析功能
- 📊 相似度過濾和視覺化
- 💾 結果匯出功能

## 📄 授權協議

本專案採用 MIT 授權協議 - 詳見 [LICENSE](LICENSE) 檔案

## 🙏 致謝

- [OpenCLIP](https://github.com/mlfoundations/open_clip) - 提供 CLIP 模型實現
- [Ollama](https://ollama.ai/) - 提供本地多模態模型服務
- [Streamlit](https://streamlit.io/) - 提供優秀的 Web 應用框架
- [phi4-mini](https://huggingface.co/microsoft/phi-4) - Microsoft 的多模態模型

---

**🚀 現在就開始使用二階段驗證，讓你的圖片分析更加智能和可靠！** 