from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastmcp import FastMCP
from fastmcp.server.auth import StaticTokenVerifier
from fastmcp.server.providers.skills import SkillsDirectoryProvider

auth_token = os.environ.get("MCP_AUTH_TOKEN", "test")
auth = StaticTokenVerifier(tokens={auth_token: {"sub": "admin", "client_id": "cli"}})

# 1. 初始化 MCP 伺服器 (這裡不放網路傳輸參數)
mcp = FastMCP("Stateless-Agent-Server", auth=auth)

skill_provider = SkillsDirectoryProvider(
    supporting_files="resources",
    roots="./skills",
    reload=False
)

mcp.add_provider(skill_provider)

@mcp.tool()
def get_user_data(user_id: int) -> dict:
    """取得使用者基本資料"""
    return {"id": user_id, "status": "active"}

# 2. 建立 ASGI 應用程式時，啟用 stateless_http
# 這是 v3.x 與 FastAPI 整合的正確掛載方式
mcp_app = mcp.http_app(
    path="/",
    stateless_http=True,
    json_response=True  # 建議開啟，讓 API 回應為標準 JSON 格式
)

# 3. 處理生命週期 (Lifespan)
# 雖然是無狀態模式，但 MCP 內部仍有資源需要初始化與清理
@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # 啟動時先執行 MCP 的 lifespan
    async with mcp_app.lifespan(app):
        # 這裡可以加入你自己的 FastAPI 啟動邏輯 (如連線資料庫)
        yield
        # 這裡可以加入關閉邏輯

# 4. 建立 FastAPI 主程式
app = FastAPI(
    title="K8S Stateless MCP API",
    lifespan=app_lifespan
)

# 5. 將無狀態的 MCP 路由掛載到指定的 API 路徑下
app.mount("/mcp", mcp_app)

# 設定環境變數 FASTMCP_STATELESS_HTTP=true
# 執行方式: uvicorn main:app --host 0.0.0.0 --port 8000
