# 📈 Stock Assistant — 股票資訊個人助手

台股 + 美股自選清單、新聞爬蟲、Claude AI 摘要、PDF 備份、智慧選股一體化工具。

---

## 🚀 快速啟動

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 啟動伺服器

```bash
python app.py
```

### 3. 開啟瀏覽器

```
http://localhost:5000
```

### 4. 設定 API Key

點選右上角 ⚙️ → 輸入你的 Claude API Key → 儲存

取得 API Key：https://console.anthropic.com

---

## 📂 專案結構

```
stock_assistant/
├── app.py                    # Flask 後端主程式
├── requirements.txt          # Python 依賴套件
├── README.md
├── templates/
│   └── index.html            # 前端介面
└── data/
    ├── watchlist.json        # 自選股清單（自動生成）
    ├── config.json           # API Key 設定（自動生成）
    └── pdf_reports/          # PDF 備份存放位置
        └── stock_report_YYYYMMDD_HHMMSS.pdf
```

---

## 🎯 功能說明

### 分頁 1 — 自選清單
- 搜尋台股（.TW）或美股代號 / 名稱
- 加入 / 移除自選清單
- 即時顯示最新報價與漲跌幅（via Yahoo Finance）

### 分頁 2 — 新聞情報
- 從自選清單勾選要查詢的股票
- 同時爬取 **Google News** 與 **Yahoo Finance** 兩個來源的最新新聞
- 點「Claude 整理摘要」→ 自動呼叫 Claude Haiku 整理重點
- 點「匯出 PDF」→ 將摘要與新聞清單存至 `data/pdf_reports/`

### 分頁 3 — 選股雷達
- 從 5 個維度選擇標籤：產業板塊、投資策略、技術條件、風險偏好、操作週期
- 系統自動組合最佳化 prompt 詢問 Claude
- 獲得台股 + 美股精選推薦與詳細分析

---

## 🔤 中文 PDF 字體說明

PDF 匯出預設會偵測系統中文字體：

| 作業系統 | 使用字體 |
|---------|---------|
| macOS   | Arial Unicode MS |
| Windows | 微軟正黑體 (msyh.ttf) |
| Linux   | Noto Sans CJK |

若中文無法顯示，請手動下載 `NotoSansSC-Regular.ttf` 放入 `data/` 資料夾。
下載連結：https://fonts.google.com/noto/specimen/Noto+Sans+SC

---

## ⚠️ 免責聲明

本工具所有 AI 分析內容僅供資訊參考，不構成投資建議。投資有風險，請謹慎評估。
