import asyncio
import os
import shutil
from pathlib import Path
from my_skill_server import create_server, ScriptRunRequest

# 測試用的路徑
TEST_ROOT = Path("test_env").resolve()
SKILLS_DIR = TEST_ROOT / "skills"
WORKSPACE_DIR = TEST_ROOT / "workspace"

async def setup_test_env():
    """建立測試所需的目錄與檔案"""
    if TEST_ROOT.exists():
        shutil.rmtree(TEST_ROOT)
    
    SKILLS_DIR.mkdir(parents=True)
    WORKSPACE_DIR.mkdir(parents=True)
    
    # 建立一個測試技能
    skill_path = SKILLS_DIR / "test-skill"
    skill_path.mkdir()
    (skill_path / "SKILL.md").write_text("# Test Skill\nThis is a test skill content.")
    
    # 建立一個測試腳本
    scripts_path = skill_path / "scripts"
    scripts_path.mkdir()
    (scripts_path / "hello.py").write_text("import sys; print(f'Hello {sys.argv[1]}')")

async def test_file_operations(server):
    """測試檔案讀寫工具"""
    print("\n--- Testing File Operations ---")
    
    # 測試寫入
    writer = server.registry.get("file_write")
    res_write = writer.execute(path="test.txt", content="Hello MCP World")
    print(f"Write result: {res_write}")
    
    # 測試讀取
    reader = server.registry.get("file_read")
    res_read = reader.execute(path="test.txt")
    print(f"Read result: {res_read}")
    
    # 測試編輯
    editor = server.registry.get("file_edit")
    res_edit = editor.execute(path="test.txt", old_string="World", new_string="Universe")
    print(f"Edit result: {res_edit}")
    
    # 驗證編輯結果
    res_final = reader.execute(path="test.txt")
    print(f"Final read: {res_final}")

async def test_script_execution(server):
    """測試腳本執行工具"""
    print("\n--- Testing Script Execution ---")
    
    executor = server.registry.get("skill_script")
    
    # 建立 Request
    request = ScriptRunRequest(
        skill_name="test-skill",
        script_name="scripts/hello.py",
        positional_args=["Jason"]
    )
    
    # 執行
    res_script = executor.execute(request=request)
    print(f"Script execution result:\n{res_script}")

async def main():
    await setup_test_env()
    
    # 建立 Server 實例 (不啟動 stdio，僅測試內部 Registry)
    server = create_server(
        skills_dir=SKILLS_DIR,
        workspace_dir=WORKSPACE_DIR,
        verbose=False
    )
    
    try:
        await test_file_operations(server)
        await test_script_execution(server)
    finally:
        # 清理
        if TEST_ROOT.exists():
            shutil.rmtree(TEST_ROOT)
        print("\nTest completed and cleaned up.")

if __name__ == "__main__":
    asyncio.run(main())
