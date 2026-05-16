# Skill MCP Server (Standalone)

這是一個基於 FastMCP 構建的 Model Context Protocol (MCP) 伺服器，旨在將「技能」（包含指令說明與自動化腳本的資料夾）無縫整合至 AI 代理工作流中。

## 核心特性

- **自動技能發現**：利用 `SkillsDirectoryProvider` 自動將 `skills/` 目錄下的 `SKILL.md` 轉化為 MCP 資源。
- **安全腳本執行**：提供 `skill_script` 工具，支援 Python, Shell, Node.js, TypeScript 腳本，具備超時控制與環境變數注入。
- **工作區檔案管理**：內建讀取、寫入與編輯（搜尋與取代）工具，專門用於處理 `workspace/` 目錄下的檔案。
- **單一檔案部署**：所有邏輯封裝在 `my_skill_server.py` 中，方便攜帶與執行。

## 快速開始

### 1. 安裝依賴

確保已安裝 `fastmcp`：

```bash
pip install fastmcp
```

### 2. 目錄結構

```text
.
├── my_skill_server.py
├── skills/
│   └── demo-skill/
│       ├── SKILL.md
│       └── scripts/
│           └── hello.py
└── workspace/
```

### 3. 執行伺服器

```bash
python my_skill_server.py --skills-dir ./skills --workspace ./workspace
```

## 工具說明

### `skill_script`
執行技能目錄下的腳本。
- **參數**：
  - `skill_name`: 技能資料夾名稱。
  - `script_name`: 腳本名稱（需在技能資料夾內）。
  - `optional_args`: 字典格式的旗標（如 `{"--port": 8080}`）。
  - `positional_args`: 列表格式的位置參數。

### `file_read` / `file_write` / `file_edit`
管理 `workspace/` 目錄下的檔案。支援搜尋與取代編輯。

## 環境變數

- `SKILL_MCP_SKILLS_DIR`: 預設技能路徑。
- `SKILL_MCP_WORKSPACE_DIR`: 預設工作區路徑。
- `SKILL_MCP_LOG_LEVEL`: 設定為 `SILENT` 可關閉日誌。
