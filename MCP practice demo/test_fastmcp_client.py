import os
import asyncio
from fastmcp.client import Client, StreamableHttpTransport


MCP_AUTH_TOKEN = os.environ.get("MCP_AUTH_TOKEN", "test")


async def main():
    # app.py 中使用了 stateless_http=True，並掛載在 /mcp
    # 所以要用 StreamableHttpTransport 連接 http://localhost:8000/mcp
    transport = StreamableHttpTransport(
        url="http://localhost:8000/mcp",
        headers={
            "Authorization": f"Bearer {MCP_AUTH_TOKEN}",
            "Content-Type": "application/json"
        }
    )

    print("準備連線到 MCP Server...")
    
    # 建立 FastMCP 官方的 Client
    async with Client(transport) as client:
        print("✅ 連線成功！\n")
        
        print("--- 1. 列出可用的工具 (tools/list) ---")
        tools = await client.list_tools()
        for t in tools:
            print(f" - [{t.name}] {t.description}")
        
        print("\n--- 2. 執行 get_user_data 工具 (tools/call) ---")
        try:
            # 使用官方 client 的 call_tool 方法
            result = await client.call_tool("get_user_data", arguments={"user_id": 12345})
            print("✅ 執行成功，取得結果：")
            print(result)
        except Exception as e:
            print(f"❌ 工具執行發生錯誤: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"連線失敗或發生錯誤: {e}")
