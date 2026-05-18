# Skill MCP Server (Standalone)

這是一個基於 [FastMCP](https://gofastmcp.com/) 構建的 Model Context Protocol (MCP) 伺服器，旨在將「技能」（包含指令說明與自動化腳本的本地資料夾）無縫整合至 AI 代理（如 Claude, Cursor 等支援 MCP 的工具）的工作流中。

本專案經過重構，將原本的多檔案架構濃縮為單一檔案 `new_skill_server.py`，大幅降低了部署與遷移的門檻，同時引入了 FastMCP 原生的 `SkillsDirectoryProvider`，讓技能的註冊與發現更加自動化且標準化。

---

## 🌟 核心特性

1. **自動技能發現 (SkillsDirectoryProvider)**
   - 伺服器會自動監聽指定的 `skills/` 目錄。
   - 任何包含 `SKILL.md` 的子目錄都會被自動辨識為一個獨立的技能，並將其轉化為 MCP 資源（Resources），例如 `skill://my-skill/SKILL.md`。
   - 支援動態熱重載（依賴 FastMCP 底層機制），無需重啟伺服器即可發現新技能。

2. **安全隔離的腳本執行 (Script Executor)**
   - 內建 `skill_script` 工具，允許 AI 代理主動呼叫技能目錄下的腳本。
   - **智慧執行引擎**：自動判斷副檔名，支援 `.py` (Python), `.sh`/`.bash` (Shell), `.js` (Node.js), `.ts` (ts-node)。
   - **安全防護**：嚴格防止目錄穿越攻擊（Directory Traversal），確保腳本只能在指定的技能或工作區內執行。
   - **執行控制**：支援超時限制 (Timeout)、環境變數注入，並會詳細回傳 stdout 與 stderr 供 AI 分析。

3. **工作區檔案管理 (Workspace Operations)**
   - 為了讓 AI 能有效地產出與修改程式碼，伺服器提供專屬的檔案操作工具：
     - `file_read`: 安全讀取工作區檔案。
     - `file_write`: 建立或覆寫檔案。
     - `file_edit`: 支援安全的搜尋與取代 (Search and Replace) 編輯模式。

---

## 🚀 快速開始

### 1. 系統需求與安裝

請確保您的環境安裝了 Python 3.10+，接著安裝必要的依賴：

```bash
pip install fastmcp pydantic
```
*(若需要透過 SSE 協定提供服務，請額外安裝 `pip install uvicorn starlette`)*

### 2. 準備目錄結構

啟動伺服器前，建議先建立預設的目錄結構：

```text
.
├── new_skill_server.py     # 主程式
├── skills/                # 放置所有技能的目錄
│   └── data-analyzer/     # 一個名為 data-analyzer 的技能
│       ├── SKILL.md       # 技能的指令與系統提示詞
│       └── scripts/       # 該技能專屬的執行腳本
│           └── run.py     
└── workspace/             # AI 進行檔案操作的工作區
```

### 3. 啟動伺服器

**預設啟動（Stdio 模式，適合 Cursor / Claude Desktop 直接掛載）**：
```bash
python new_skill_server.py
```

**自訂路徑啟動**：
```bash
python new_skill_server.py --skills-dir /path/to/my/skills --workspace /path/to/my/workspace
```

---

## 🛠️ MCP 工具 (Tools) 詳解

本伺服器向 AI 暴露了以下工具（透過 Pydantic 嚴格定義 Schema）：

### 1. `skill_script` (執行技能腳本)
在安全隔離的環境下執行特定技能的腳本，並回傳完整的標準輸出與錯誤日誌供 AI 解析。
- **參數 (`RunSkillScriptSchema`)**:
  - `skill_name` (string, 必填): 技能目錄的名稱，例如 `'data-analyzer'`。絕對不可包含路徑符號 (`/`, `\`, `..`)。
  - `file_path` (string, 必填): 要執行的腳本檔案名稱（預設 `'script.py'`），必須位於該技能目錄下，例如 `'scripts/main.py'`。
  - `env_vars` (dict, 可選): 執行腳本前注入的系統環境變數。例如: `{'NODE_ENV': 'production', 'API_KEY': '123'}`。
  - `optional_args` (dict, 可選): 可選參數與旗標。鍵名必須以破折號開頭。範例: `{'-lah': True, '--name': 'test.txt', '--port': 8080}`。
  - `positional_args` (list, 可選): 位置參數。嚴格按照順序傳入。例如: `['input.csv', 'output.json']`。
  - `timeout` (integer, 可選): 執行超時限制 (5~300秒)，預設 30 秒。

### 2. `file_read` (讀取工作區檔案)
讀取 `workspace/` 目錄下的指定檔案。
- **參數**:
  - `path` (string): 相對於工作區的檔案路徑。

### 3. `file_write` (寫入工作區檔案)
在 `workspace/` 中建立新檔案或完全覆寫現有檔案。
- **參數**:
  - `path` (string): 目標檔案路徑。
  - `content` (string): 檔案的完整內容。

### 4. `file_edit` (編輯工作區檔案)
針對較大的檔案，提供精準的字串取代功能，避免重新寫入整份文件。
- **參數**:
  - `path` (string): 要編輯的檔案路徑。
  - `old_string` (string): 原本存在於檔案中的字串。
  - `new_string` (string): 要替換成的新字串。
  - `replace_all` (boolean, 預設 false): 若為 true 則替換所有符合的字串，否則僅替換第一個。

---

## 📖 如何撰寫一個新技能？

一個標準的技能至少需要一個 `SKILL.md`。這個檔案會被 FastMCP 自動轉化為資源。

**路徑範例**: `skills/git-helper/SKILL.md`

**內容範例 (`SKILL.md`)**:
```markdown
---
name: git-helper
description: 協助進行 Git 提交流程標準化的自動化工具
version: 1.0.0
---

# Git Helper

你是一個 Git 助手。當使用者要求提交程式碼時，請遵循以下步驟：
1. 讀取工作區的檔案變更。
2. 呼叫 `skill_script` 執行 `scripts/lint.sh` 確保程式碼風格正確。
3. 若驗證通過，協助生成符合 Conventional Commits 的提交訊息。
```

*(上述 Markdown 頂部的 YAML Frontmatter 雖然在新的 FastMCP 架構中不一定強求，但保留可用作技能中繼資料的擴充使用。)*

**禁用特定工具 (提高安全性)**：
```bash
# 禁用寫入與編輯工具，僅保留讀取與腳本執行
python new_skill_server.py --disable-write --disable-edit
```

---

## ⚙️ 環境變數與進階設定

除了 CLI 參數，您也可以透過環境變數配置伺服器：

- `SKILL_MCP_SKILLS_DIR`: 設定技能的根目錄路徑。
- `SKILL_MCP_WORKSPACE_DIR`: 設定工作區的路徑。
- `SKILL_MCP_ENABLE_FILE_WRITE`: 是否啟用 `file_write` 工具 (true/false, 預設 true)。
- `SKILL_MCP_ENABLE_FILE_EDIT`: 是否啟用 `file_edit` 工具 (true/false, 預設 true)。
- `SKILL_MCP_LOG_LEVEL`: 設定日誌層級 (DEBUG, INFO, WARNING, ERROR, CRITICAL)。若設為 `SILENT`，將完全關閉日誌輸出，這在某些嚴格依賴 Stdio 乾淨傳輸的環境中非常有用。
