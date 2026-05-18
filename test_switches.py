import asyncio
from pathlib import Path
from new_skill_server import create_server

async def test_disabling_tools():
    # Test with both enabled (default)
    server_all = create_server(enable_file_write=True, enable_file_edit=True)
    print(f"All enabled - count: {server_all.registry.count()}")
    assert server_all.registry.get("file_write") is not None
    assert server_all.registry.get("file_edit") is not None

    # Test with write disabled
    server_no_write = create_server(enable_file_write=False, enable_file_edit=True)
    print(f"No write - count: {server_no_write.registry.count()}")
    assert server_no_write.registry.get("file_write") is None
    assert server_no_write.registry.get("file_edit") is not None

    # Test with both disabled
    server_none = create_server(enable_file_write=False, enable_file_edit=False)
    print(f"None - count: {server_none.registry.count()}")
    assert server_none.registry.get("file_write") is None
    assert server_none.registry.get("file_edit") is None
    
    print("Test passed!")

if __name__ == "__main__":
    asyncio.run(test_disabling_tools())
