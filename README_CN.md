# Skill MCP Server 🚀

<p align="center">
  <strong>將任何 AI Agent 變成專家 — 只需放入一個 skill 資料夾即可。</strong>
</p>

<p align="center">
  <a href="#什麼是-skill-mcp-server">📖 什麼是 Skill MCP Server？</a> •
  <a href="#為什麼選擇-skill-mcp-server">🌟 為什麼選擇它？</a> •
  <a href="#核心功能">✨ 核心功能</a> •
  <a href="#快速開始">🚀 快速開始</a> •
  <a href="#建立-skills">📝 建立 Skills</a> •
  <a href="#文件">📚 文件</a>
</p>

## 📖 什麼是 Skill MCP Server？

Skill MCP Server 是一個標準的 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 伺服器，它將 Claude Skills 橋接到任何支援 MCP 的 AI Agent。

<p align="center">
  <img src="docs/skll_mcp.png" alt="Skill MCP Server" style="max-width: 100%; height: auto;"/>
</p>

以前，Claude Skills 主要用於 Anthropic 的官方工具。如果你的 AI 應用程式不支援 Skills，你必須自己實作解析和執行邏輯，這非常繁瑣。有了這個專案，你只需進行配置，就可以讓任何相容 MCP 的 Agent 直接使用標準的 Skill 檔案。

---

## 🎬 示範

<p align="center">
  <img src="https://github.com/ephemeraldew/skill_mcp/raw/main/docs/example.gif" alt="Demo Video" width="800">
</p>

## 💡 核心概念

- 🔌 **MCP (Model Context Protocol)**: 可以把它想像成 AI 的「USB 介面」。只要你的 AI 助理支援這個介面，它就能連接到各種工具和服務。
- 📦 **Claude Skills**: 可以把它看作是 AI 的「技能包」。它們不僅僅是文件——還包含了說明指令 (`SKILL.md`)、配套腳本 (Python/JS) 以及參考資料。

Skill MCP Server 是一個「轉換器」，它可以幫助各種 Agent 接入 Skill 生態，實現隨插即用的功能。

## 🌟 為什麼選擇 Skill MCP Server？

如果你的 Agent 還不支援 Skills，這個專案可以幫你快速整合：

| 面向 | 原生支援的 Agent (例如 Claude Code) | 其他 Agent (使用本專案) |
|-----------|------------------------------------------------|----------------------------------|
| 接入門檻 | 深度整合，通常不可移植 | 門檻低，使用標準 MCP 協定 |
| 開發負擔 | 官方實作完整 | 零程式碼，無需自行建置 Skill 解析器 |
| 彈性 | 與特定用戶端綁定 | 跨平台，適用於任何相容 MCP 的 Agent |
| 功能對齊 | 完整的腳本、資源和檔案流支援 | 完美對齊，具有相同的動態執行和資源存取能力 |

## ✨ 核心功能

- 🛠️ **高度標準化**: 嚴格遵循 MCP 協定
- 🌍 **通用相容性**: 不綁定任何廠商，適用於所有相容 MCP 的 AI 用戶端
- ⚡ **零程式碼整合**: 幫助沒有原生 Skill 支援的 Agent 快速接入 Skill 生態
- 📦 **完全相容**: 支援 `SKILL.md` 格式以及 `scripts/`, `references/` 資源目錄
- 📂 **工作區隔離**: 支援 `--workspace` 參數來指定 Skill 輸出檔案的儲存位置
- 🌐 **遠端連線支援**: 內建 HTTP/SSE 伺服器與 API Key 認證，輕鬆打造團隊共用技能庫
- 🔄 **熱重載**: 無需重啟伺服器即可加入新的 skills
- 🔒 **安全設計**: 路徑驗證，沙盒化檔案操作

## 🚀 快速開始

推薦：使用 `uvx` 執行而無需手動安裝。

### 📥 安裝

```bash
# 使用 pip
pip install skill-mcp-server

# 使用 uv (推薦)
uv pip install skill-mcp-server
```

### ⚙️ 配置 MCP

將 Skill MCP Server 加入到你的 MCP 用戶端配置中。所有相容 MCP 的用戶端都使用相同的配置格式：

**使用 uvx (推薦，無需安裝)：**

```json
{
  "mcpServers": {
    "skill-server": {
      "command": "uvx",
      "args": [
        "skill-mcp-server",
        "--skills-dir", "/path/to/your/skills",
        "--workspace", "/path/to/workspace"
      ]
    }
  }
}
```

**使用本地安裝：**

```json
{
  "mcpServers": {
    "skill-server": {
      "command": "python",
      "args": [
        "-m", "skill_mcp_server",
        "--skills-dir", "/path/to/your/skills",
        "--workspace", "/path/to/workspace"
      ]
    }
  }
}
```

**設定檔位置：**
- Claude Desktop: `claude_desktop_config.json` (位置因作業系統而異)
- Claude Code: `~/.claude.json`
- 其他 MCP 用戶端：請參考你的用戶端文件

**參數說明：**

- `--skills-dir`: 核心參數。設定為包含你想讓 Agent 使用的所有 Skill 資料夾的根目錄。
- `--workspace`: 重要參數。指定儲存 Skill 執行輸出檔案（程式碼、報告等）的位置。

## 🎮 互動式測試 (Interactive Demo)

專案內建了一個簡單的終端機 MCP 客戶端 (`examples/demo.py`)，讓你可以直接透過 OpenAI 模型來互動測試你的 Skills。

### 準備工作
```bash
# 設定你的 OpenAI API Key
export OPENAI_API_KEY="your-api-key-here"
```

### 模式一：本地端執行 (Stdio 模式)
這是最簡單的測試方式，直接掛載本地的 skills 目錄，程式會在底層自動啟動 Server：
```bash
# 進入 examples 目錄
cd examples

# 執行 demo.py (指定 skills 目錄與可選的 workspace)
python demo.py --skills-dir ./skills --workspace ../workspace
```

### 模式二：連接遠端伺服器 (SSE 模式)
如果你想測試透過網路連接獨立運作的 Skill Server：
```bash
# 1. 在第一個終端機啟動帶有 API Key 驗證的遠端 Server
SKILL_MCP_API_KEY="my-secret-token" python -m skill_mcp_server

# 2. 在第二個終端機使用 demo.py 透過 URL 與自訂 Header 連線
cd examples
python demo.py --url http://localhost:8000/sse -H "Authorization: Bearer my-secret-token"
```

## 🛠️ 可用工具 (MCP Tools)

連線後，你的 AI Agent 可以使用以下工具：

1. 🔍 `list_skills`: 列出所有可用的 skills
2. 📚 `skill`: 載入特定的 skill 以從其 `SKILL.md` 取得詳細指令
3. 📄 `skill_resource`: 從 skill 包中讀取參考文件或範本
4. ▶️ `skill_script`: 在安全環境中執行 skill 附帶的腳本
5. 📖 `file_read`: 從指定的工作區讀取檔案
6. ✍️ `file_write`: 將檔案寫入指定的工作區
7. ✏️ `file_edit`: 編輯工作區中的現有檔案

## 📝 建立 Skills

標準的 Skill 結構如下所示：

```
my-skills/
└── deploy-helper/           # Skill 資料夾
    ├── SKILL.md             # 核心文件 (必填)
    ├── scripts/             # 可執行腳本
    └── references/          # 參考資料
```

**SKILL.md 範例：**

```markdown
---
name: deploy-helper
description: 幫助使用者一鍵將應用程式部署到生產環境
---

# Deploy Helper Usage Guide

When users request deployment, follow these steps:
1. Use `skill_resource` to read the deployment template.
2. Modify local configuration files.
3. Call `skill_script` to execute the deployment script.
```

### SKILL.md 格式

```markdown
---
name: my-skill
description: 簡要描述該 skill 的作用以及何時使用它
---

# My Skill

## 概覽

解釋該 skill 使 AI 能夠做什麼。

## 用法

針對 AI Agent 的逐步說明...

## 可用資源

- `scripts/process_data.py` - 處理輸入資料
- `assets/report_template.md` - 輸出範本
```

## 💼 使用情境

- 📊 **資料分析**: 讓 Agent 能夠執行資料分析
- 📝 **文件產生**: 讓 Agent 能夠建立專業文件
- 🔗 **API 整合**: 讓 Agent 能夠與特定的 API 整合
- 🔍 **程式碼審查**: 讓 Agent 能夠遵循團隊標準
- 🚀 **DevOps 任務**: 讓 Agent 能夠自動化部署工作流程

## 📚 文件

- 📖 [入門指南](docs/getting-started.md)
- ✨ [建立 Skills](docs/creating-skills.md)
- 📋 [Skill 格式參考](docs/skill-format.md)
- 📤 [發布指南](docs/publishing.md)

## 🛠️ 開發

```bash
# 複製儲存庫
git clone https://github.com/ephemeraldew/skill_mcp.git
cd skill_mcp

# 安裝開發依賴
uv pip install -e ".[dev]"

# 執行測試
pytest

# 執行程式碼檢查
ruff check src/
```

## 🤝 貢獻

歡迎貢獻！請參閱 [CONTRIBUTING.md](CONTRIBUTING.md) 了解指南。

如果這個專案對你有幫助，請給它一個 ⭐️ Star。

## 📄 授權

MIT 授權 - 詳情請參閱 [LICENSE](LICENSE)。

## 🔗 相關資源

- [MCP 官方文件](https://modelcontextprotocol.io/)
- [Claude Skills 官方指南](https://code.claude.com/docs/en/skills)
- [Agent Skills 開放標準](https://agentskills.io/)

---

<p align="center">
  <sub>基於 <a href="https://modelcontextprotocol.io/">Model Context Protocol</a> 建置</sub>
</p>