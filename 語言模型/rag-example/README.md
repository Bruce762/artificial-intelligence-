# RAG 應用示例

此專案是一個簡單的 RAG (Retrieval Augmented Generation) 應用，使用 LangChain 和 Ollama 實現，可以讀取文字檔案並回答相關問題。

## 功能特點

- 讀取文件夾中的所有文字檔案
- 使用 Ollama 的 nomic-embed-text 模型進行文本嵌入
- 使用 Ollama 的 llama3-taide-lx-8b-chat-alpha 模型進行文本生成
- 提供命令行介面、API 介面和網頁前端三種使用方式

## 前置需求

- Python 3.8 或更高版本
- [Ollama](https://ollama.ai/) 已安裝並運行
- 確保 Ollama 中已安裝以下模型：
  - `nomic-embed-text:latest`
  - `cwchang/llama3-taide-lx-8b-chat-alpha1:latest`

## 安裝

1. 安裝依賴包：

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 準備數據

將您的文本文件（.txt 格式）放在 `data` 目錄下。如果目錄為空，系統會自動創建一個簡單的示例文件。

### 2. 命令行介面

運行以下命令啟動命令行介面：

```bash
python main.py
```

然後按照提示輸入問題。

### 3. 網頁介面和 API

運行以下命令啟動 Web 服務器：

```bash
python api.py
```

- 網頁前端: 通過瀏覽器訪問 `http://localhost:8000`
- API 服務器: API 端點在 `http://localhost:8000/query`

#### API 端點

- `POST /query`：發送問題並獲取回答
  ```json
  { "question": "您的問題" }
  ```

- `GET /health`：檢查 API 服務器狀態

## 專案結構

```
rag-example/
├── rag.py        # RAG 核心功能
├── main.py       # 命令行介面
├── api.py        # API 介面和網頁服務
├── templates/    # HTML 模板
│   └── index.html    # 前端頁面
├── static/       # 靜態文件目錄
│   ├── css/      # CSS 樣式
│   └── js/       # JavaScript 文件
├── data/         # 數據文件目錄
├── chroma_db/    # 向量數據庫存儲目錄（運行後自動創建）
└── requirements.txt
```

## 注意事項

- 確保 Ollama 服務在使用應用前已啟動
- 文本檔案應使用 UTF-8 編碼
- 如果沒有足夠相關的資訊，系統會回應無法找到相關資訊 