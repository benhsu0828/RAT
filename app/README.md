# 🧠 RAT: Retrieval-Augmented Thoughts System
[中文](./README.md) | [English](./README.en.md)

**智能檢索增強思維系統** - 結合 OpenAI ChatGPT 和網路搜尋的課程大綱生成與智能問答系統

## 📋 專案簡介

RAT 是一個基於 AI 的課程設計與問答系統，利用檢索增強生成技術 (Retrieval-Augmented Generation) 來提供更準確、更豐富的內容生成服務。

### 🎯 主要功能

- **📚 課程大綱生成**: 上傳文件或輸入需求，自動生成專業課程大綱
- **🔍 智能問答**: 結合網路搜尋的 AI 問答系統
- **📄 多格式支援**: 支援 PDF、DOCX、TXT 文件處理
- **🌐 網路增強**: 整合 Google 搜尋提升內容品質
- **📊 系統監控**: 即時系統狀態和配置監控

## 🚀 快速開始

### 1. 建立 Conda 虛擬環境

```bash
# 建立新的 conda 環境
conda create -n RAT python=3.10 -y

# 啟動環境
conda activate RAT
```

### 2. 安裝相依套件

```bash
# 進入專案目錄
cd /path/to/RAT

# 安裝所需套件
pip install -r requirements.txt
```

## 3. 環境變數設定

### 方法 1：建立設定腳本（建議）
1. 建立腳本檔案
```bash
cd /path/to/RAT/app
touch setup_env.sh
```

2. 編輯 setup_env.sh（請自行填入你的金鑰，切勿提交到版本控制）
```bash
#!/bin/bash
# Environment variables for RAT (do NOT commit real keys)

# OpenAI API（必填）
export OPENAI_API_KEY="your-openai-api-key"

# Google 搜尋 API（選填，但建議）
export GOOGLE_API_KEY="your-google-api-key"
export GOOGLE_CSE_ID="your-custom-search-engine-id"

# 系統設定
export MODEL_TYPE="openai"
echo "[RAT] Environment variables loaded."
```

3. 賦予執行權限並載入
```bash
chmod +x setup_env.sh
source ./setup_env.sh
```

4.（可選）開機自動載入：將下行加入 ~/.zshrc 或 ~/.bashrc
```bash
source /path/to/RAT/app/setup_env.sh
```

### 方法 2：每次手動設定環境變數
```bash
# OpenAI（必填）
export OPENAI_API_KEY="your-openai-api-key"

# Google 搜尋（選填）
export GOOGLE_API_KEY="your-google-api-key"
export GOOGLE_CSE_ID="your-custom-search-engine-id"

# 系統設定
export MODEL_TYPE="openai"
```

---

#### 取得 API Keys

1. **OpenAI API Key**:
   - 前往 [OpenAI Platform](https://platform.openai.com/)
   - 建立帳號並取得 API Key

2. **Google Search API**:
   - 前往 [Google Cloud Console](https://console.cloud.google.com/)
   - 啟用 Custom Search API
   - 建立 Custom Search Engine 並取得 CSE ID

### 4. 啟動應用

#### Web 界面 (Flask)

```bash
# 啟動 Flask Web 應用
python app.py
```

應用將在 `http://localhost:7860` 上運行

#### Gradio 界面

```bash
# 啟動 Gradio 界面
python gradio_app.py
```

#### 使用啟動腳本

```bash
# 給予執行權限
chmod +x start_rat.sh

# 一鍵啟動
./start_rat.sh
```

## 📁 專案結構

```
RAT/app/
├── 📄 app.py                    # Flask Web 應用主程式
├── 📄 gradio_app.py            # Gradio 界面應用
├── 📄 README.md                # 專案說明文件
├── 📄 setup.sh                 # 環境變數設定腳本
├── 📄 start_rat.sh             # 應用啟動腳本
├── 📄 requirements.txt         # Python 相依套件列表
├── 📁 __pycache__/             # Python 編譯快取
├── 📁 core/                    # 核心功能模組
│   ├── 📄 chunk.py             # 文本分塊處理
│   ├── 📄 config.py            # 系統配置和模型設定
│   ├── 📄 file_processing.py   # 檔案處理 (PDF/DOCX/TXT)
│   ├── 📄 search.py            # Google 搜尋功能
│   └── 📁 __pycache__/         # 核心模組編譯快取
├── 📁 static/                  # 靜態資源
│   ├── 📁 css/
│   │   └── 📄 style.css        # 自訂樣式
│   └── 📁 js/
│       ├── 📄 app.js           # 通用 JavaScript
│       └── 📄 course.js        # 課程生成功能 JS
├── 📁 templates/               # HTML 模板
│   ├── 📄 404.html             # 404 錯誤頁面
│   ├── 📄 500.html             # 500 錯誤頁面
│   ├── 📄 base.html            # 基礎模板
│   ├── 📄 course.html          # 課程生成頁面
│   ├── 📄 index.html           # 首頁
│   ├── 📄 system.html          # 系統資訊頁面
│   └── 📄 test.html            # 測試頁面
└── 📁 uploads/                 # 檔案上傳目錄
```

## 🔧 核心模組說明

### `core/config.py`
- **OpenAI API 整合**: ChatGPT 模型調用
- **系統配置管理**: 模型選擇和參數設定
- **統一回應生成**: 標準化 AI 回應介面

### `core/file_processing.py`
- **多格式檔案支援**: PDF、DOCX、TXT 解析
- **課程資訊提取**: 從文件中萃取關鍵課程資訊
- **智能內容分析**: 自動理解文件結構和內容

### `core/search.py`
- **Google 搜尋整合**: 網路資訊檢索
- **內容品質篩選**: 相關性和可信度評估
- **搜尋結果優化**: 智能查詢生成和結果處理

### `core/chunk.py`
- **文本分塊處理**: 大文件智能分段
- **Token 計算**: 精確的文本長度計算
- **記憶體優化**: 高效的文本處理策略

## 🌐 Web 界面功能

### 主要頁面

1. **首頁** (`/`): 系統介紹和功能概覽
2. **課程生成器** (`/course`): 上傳文件或輸入需求生成課程大綱
3. **系統資訊** (`/system`): 查看系統狀態、API 配置和專案資訊

### API 端點

- `POST /api/generate_course`: 課程大綱生成 API
- `GET /api/system_status`: 系統狀態查詢 API

## ⚙️ 系統需求

### API 需求
- **OpenAI API Key**: 必須 (用於 ChatGPT)
- **Google Search API**: 選用 (增強搜尋功能)
- **Google CSE ID**: 選用 (自訂搜尋引擎)

## 🔍 使用方式

### 課程大綱生成

1. **方式一**: 上傳課程相關文件 (PDF/DOCX/TXT)
2. **方式二**: 直接輸入課程需求描述
3. **方式三**: 同時提供文件和需求描述

### 系統會自動:
- 分析文件內容或需求
- 生成初始課程大綱
- 搜尋相關教學資源 (如啟用)
- 優化和增強課程內容
- 產出專業格式化的課程大綱

## 🛠️ 故障排除

### 常見問題

1. **OpenAI API 錯誤**:
   ```bash
   # 檢查 API Key 是否正確設定
   echo $OPENAI_API_KEY
   ```