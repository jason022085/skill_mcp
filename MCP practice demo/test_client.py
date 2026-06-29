import os
import requests
import json

API_URL = "http://localhost:8000"
# 若要順利通過雙重驗證，請確保這裡的 token 能同時滿足 FastAPI 與 MCP 的條件
# 這裡我們為了示範，先假設兩者已設定為相同（或者您已將 FastAPI 的 token 改為與 MCP 一致）
# 若您未修改，預設使用 FASTAPI_TOKEN 會讓 FastAPI 放行，但 MCP 會因為不是 "test" 而報錯。
USE_TOKEN = "test"  

headers = {
    "Authorization": f"Bearer {USE_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def test_fastapi_health():
    """測試 FastAPI 層級的驗證（例如存取 openapi.json）"""
    print("--- 1. 測試 FastAPI 層級端點 (/openapi.json) ---")
    response = requests.get(f"{API_URL}/openapi.json", headers=headers)
    if response.status_code == 200:
        print("✅ FastAPI 驗證成功！取得 OpenAPI schema")
    else:
        print(f"❌ FastAPI 驗證失敗 ({response.status_code}): {response.text}")

def test_mcp_tools_list():
    """測試呼叫 MCP 的 tools/list"""
    print("\n--- 2. 測試 MCP tools/list ---")
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    
    # FastMCP stateless_http 掛載在 /mcp 的根目錄，通常直接 POST 到該路徑
    response = requests.post(f"{API_URL}/mcp", headers=headers, json=payload)
    
    if response.status_code == 200:
        print("✅ MCP tools/list 請求成功！")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    else:
        print(f"❌ MCP 請求失敗 ({response.status_code}): {response.text}")

def test_mcp_call_tool():
    """測試呼叫 MCP 中定義的 get_user_data 工具"""
    print("\n--- 3. 測試 MCP tools/call (呼叫 get_user_data) ---")
    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "get_user_data",
            "arguments": {
                "user_id": 999
            }
        }
    }
    
    response = requests.post(f"{API_URL}/mcp", headers=headers, json=payload)
    
    if response.status_code == 200:
        print("✅ MCP tools/call 請求成功！")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    else:
        print(f"❌ MCP 工具呼叫失敗 ({response.status_code}): {response.text}")

if __name__ == "__main__":
    print("準備測試 app.py API... (請確保您的 app.py 已啟動)")
    test_fastapi_health()
    test_mcp_tools_list()
    test_mcp_call_tool()
