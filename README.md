# PictureQA Demo - 圖片與文字相似度分析工具

基於 CLIP 模型的圖片與文字相似度分析工具，提供直觀的 Web 介面來批次處理圖片並進行相似度分析。

## 🌟 主要功能

- 🖼️ **批次分析**: 一次處理整個資料夾的圖片
- 🎚️ **即時過濾**: 調整相似度閾值即時查看結果
- 📊 **視覺化統計**: 相似度分佈圖表和統計資訊
- 💾 **結果匯出**: 支援 CSV 格式匯出
- 🚀 **效能優化**: GPU 加速和智慧快取
- 🎯 **智慧建議**: 根據資料夾名稱提供 Prompt 建議

## 🛠️ 技術架構

- **後端**: Python 3.8+
- **AI 模型**: OpenCLIP (ViT-B-32)
- **前端介面**: Streamlit
- **資料處理**: PyTorch, PIL, Pandas
- **視覺化**: Matplotlib, Plotly

## 📦 安裝說明

### 1. 環境需求

- Python 3.8 或更高版本
- CUDA (可選，用於 GPU 加速)

### 2. 安裝依賴套件

```bash
pip install -r requirements.txt
```

### 3. 驗證安裝

```bash
python -c "import torch; import open_clip; print('安裝成功！')"
```

## 🚀 使用方法

### 1. 啟動應用程式

```bash
streamlit run ui/main_app.py
```

應用程式將在瀏覽器中自動開啟，預設地址為 `http://localhost:8501`

### 2. 使用步驟

1. **選擇資料夾**: 輸入或貼上包含圖片的資料夾路徑
2. **輸入 Prompt**: 輸入英文描述，例如 "cookies on a plate"
3. **開始分析**: 點擊「開始分析」按鈕
4. **查看結果**: 在「結果」頁籤中調整相似度閾值查看過濾結果
5. **匯出資料**: 將結果匯出為 CSV 格式

### 3. 範例使用

假設你有一個包含餅乾圖片的資料夾：

```
E:/AI/pictureQA/testPic/3餅乾/
├── ComfyUI_00224_.png
├── ComfyUI_00225_.png
└── ...
```

1. 在資料夾路徑輸入: `E:/AI/pictureQA/testPic/3餅乾`
2. 在 Prompt 輸入: `cookies on a plate`
3. 開始分析並查看結果

## 📁 專案結構

```
pictureQA/
├── src/                      # 核心功能模組
│   ├── config.py            # 配置管理
│   ├── similarity_engine.py # 相似度計算引擎
│   ├── data_manager.py      # 資料管理器
│   └── utils.py             # 工具函數
├── ui/                       # 使用者介面
│   ├── main_app.py          # 主應用程式
│   └── components/          # UI 元件
│       ├── folder_selector.py
│       ├── prompt_input.py
│       ├── similarity_filter.py
│       └── result_viewer.py
├── data/                     # 資料目錄
│   ├── results/             # 分析結果
│   ├── exports/             # 匯出檔案
│   └── cache/               # 快取檔案
├── testPic/                  # 測試圖片
├── config.yaml              # 應用配置
├── requirements.txt         # 依賴套件
└── README.md               # 說明文件
```

## ⚙️ 配置選項

編輯 `config.yaml` 檔案來自訂應用程式設定：

```yaml
# 模型設定
model:
  name: "ViT-B-32"
  pretrained: "laion2b_s34b_b79k"

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

- 使用簡潔明確的英文描述
- 避免過於複雜的句子
- 可以包含物體、顏色、位置等描述
- 範例：
  - `"red apple on table"`
  - `"cookies on a plate"`
  - `"plastic water bottle"`

### 2. 效能優化

- **GPU 加速**: 確保安裝了 CUDA 版本的 PyTorch
- **快取機制**: 相同的圖片-Prompt 組合會使用快取結果
- **批次大小**: 根據顯存大小調整 `batch_size` 設定

### 3. 結果分析

- **相似度閾值**: 通常 0.3-0.7 是比較有意義的範圍
- **統計圖表**: 查看分佈圖了解整體相似度情況
- **排序功能**: 按相似度排序找出最匹配的圖片

## 🐛 常見問題

### Q: 模型載入失敗

**A**: 檢查網路連線，首次運行需要下載模型檔案。也可以嘗試更換預訓練模型。

### Q: 記憶體不足

**A**: 減少 `batch_size` 或 `max_image_size` 設定，或使用較小的圖片。

### Q: 分析速度慢

**A**: 確保使用 GPU 加速，檢查 CUDA 安裝。大量圖片建議分批處理。

### Q: 相似度分數都很低

**A**: 檢查 Prompt 是否準確描述圖片內容，嘗試調整描述方式。

## 📊 效能基準

在不同硬體配置下的效能表現：

| 硬體配置 | 100張圖片處理時間 | 記憶體使用 |
|---------|-----------------|-----------|
| CPU (Intel i7) | ~2-3 分鐘 | ~2GB |
| GPU (RTX 3060) | ~30-60 秒 | ~4GB |
| GPU (RTX 4090) | ~15-30 秒 | ~6GB |

## 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request！

1. Fork 專案
2. 創建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

## 📝 更新日誌

### v1.0.0 (2024-01-01)
- 🎉 初始版本發布
- ✨ 基本的圖片相似度分析功能
- 📊 相似度過濾和視覺化
- 💾 結果匯出功能

## 📄 授權協議

本專案採用 MIT 授權協議 - 詳見 [LICENSE](LICENSE) 檔案

## 🙏 致謝

- [OpenCLIP](https://github.com/mlfoundations/open_clip) - 提供 CLIP 模型實現
- [Streamlit](https://streamlit.io/) - 提供優秀的 Web 應用框架
- [PyTorch](https://pytorch.org/) - 提供深度學習框架

---

如有問題或建議，歡迎聯繫！ 