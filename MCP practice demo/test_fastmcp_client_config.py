import os
import asyncio
from fastmcp.client import Client, StreamableHttpTransport

# 定義一個 MCP_CONFIG 字典 (此寫法常見於 Claude Desktop、LangChain 或其他 Agent 框架)
MCP_CONFIG = {
    "mcpServers": {
        "my-skill-mcp": {
            "transport": "streamable-http",
            "url": "http://localhost:8000/mcp",
            "headers": {
                "Authorization": "Bearer " + os.environ.get("MCP_AUTH_TOKEN", "test")
            }
        }
        # 如果未來有其他的 MCP Server，也可以加在這裡
        # "another-mcp": {
        #     "transport": "stdio",
        #     "command": "python",
        #     "args": ["other_server.py"]
        # }
    }
}


async def main():
    server_name = "my-skill-mcp"
    print(f"讀取 MCP_CONFIG，準備連線到 {server_name} ...")
    
    async with Client(MCP_CONFIG) as client:
        print("✅ 連線成功！\n")
        
        print("--- 1. 列出可用的工具 (tools/list) ---")
        tools = await client.list_tools()
        for t in tools:
            print(f" - [{t.name}] {t.description}")
        
        print("\n--- 2. 執行 get_user_data 工具 (tools/call) ---")
        try:
            result = await client.call_tool("get_user_data", arguments={"user_id": 888})
            print("✅ 執行成功，取得結果：")
            print(result)
        except Exception as e:
            print(f"❌ 工具執行發生錯誤: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"執行失敗: {e}")
