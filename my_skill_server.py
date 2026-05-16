#!/usr/bin/env python3
# Copyright (c) 2025
# SPDX-License-Identifier: MIT

"""
Skill MCP Server - Standalone Script
Refactored from multi-file package into a single executable file.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import re
import subprocess
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Optional, TYPE_CHECKING, Dict, List
from pydantic import BaseModel, Field, model_validator, field_validator

# Third-party imports
try:
    from fastmcp import FastMCP
    from fastmcp.server.providers.skills import SkillsDirectoryProvider
except ImportError:
    print("Error: 'fastmcp' not found. Please install it with 'pip install fastmcp'.", file=sys.stderr)
    sys.exit(1)

try:
    import uvicorn
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import JSONResponse
except ImportError:
    # Optional dependencies for SSE
    uvicorn = None
    BaseHTTPMiddleware = object
    Request = Any
    JSONResponse = Any

# --- Constants (from config/defaults.py) ---

DEFAULT_SKILLS_DIR = "skills"
DEFAULT_WORKSPACE_DIR = "workspace"

ALLOWED_FILE_EXTENSIONS: frozenset[str] = frozenset({
    ".md", ".txt", ".json", ".yaml", ".yml", ".py", ".sh", ".bash", 
    ".js", ".ts", ".html", ".css", ".xml", ".csv", ".log", ".toml", 
    ".ini", ".cfg", ".conf",
})

ALLOWED_SCRIPT_EXTENSIONS: frozenset[str] = frozenset({
    ".py", ".sh", ".bash", ".js", ".ts",
})

MAX_FILE_SIZE = 100 * 1024  # 100KB for writing
MAX_READ_SIZE = 1024 * 1024  # 1MB for reading
SCRIPT_TIMEOUT = 120  # seconds

RESOURCE_DIRS: tuple[str, ...] = ("assets", "references", "examples", "templates")
SKILL_FILENAME = "SKILL.md"
SKILL_SCAN_PATTERNS: tuple[str, ...] = ("*/SKILL.md",)

# --- Exceptions ---

class ServerError(Exception):
    """Base exception for server errors."""
    pass

class ToolNotFoundError(ServerError):
    """Raised when a requested tool is not found."""
    def __init__(self, tool_name: str) -> None:
        self.tool_name = tool_name
        super().__init__(f"Tool not found: {tool_name}")

class ConfigurationError(ServerError):
    """Raised when there's a configuration problem."""
    pass

class InitializationError(ServerError):
    """Raised when server initialization fails."""
    pass

class PathValidationError(Exception):
    """Raised when path validation fails."""
    pass

class FileValidationError(Exception):
    """Raised when file validation fails."""
    pass

class ExecutionError(Exception):
    """Raised when script execution fails."""
    pass

class SkillParseError(Exception):
    """Raised when skill parsing fails."""
    pass

class ToolError(Exception):
    """Raised when a tool execution fails."""
    pass

# --- Utilities ---

LOGGER_NAME = "skill_mcp_server"
LOG_LEVEL_ENV = "SKILL_MCP_LOG_LEVEL"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def setup_logging(verbose: bool = False, log_format: Optional[str] = None) -> logging.Logger:
    env_level = os.environ.get(LOG_LEVEL_ENV, "").upper()
    if env_level == "SILENT":
        logging.disable(logging.CRITICAL)
        logger = logging.getLogger(LOGGER_NAME)
        logger.addHandler(logging.NullHandler())
        return logger

    if env_level and hasattr(logging, env_level):
        level = getattr(logging, env_level)
    else:
        level = logging.DEBUG if verbose else logging.INFO

    fmt = log_format or DEFAULT_LOG_FORMAT
    logging.basicConfig(level=level, format=fmt, handlers=[logging.StreamHandler(sys.stderr)])
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    if os.environ.get(LOG_LEVEL_ENV, "").upper() == "SILENT":
        logging.disable(logging.CRITICAL)
    if name is None:
        return logging.getLogger(LOGGER_NAME)
    return logging.getLogger(f"{LOGGER_NAME}.{name}")

# --- Models ---

# --- Configuration ---

@dataclass
class Settings:
    skills_dir: Path = field(default_factory=lambda: Path.cwd() / DEFAULT_SKILLS_DIR)
    workspace_dir: Path = field(default_factory=lambda: Path.cwd() / DEFAULT_WORKSPACE_DIR)
    allowed_file_extensions: frozenset[str] = ALLOWED_FILE_EXTENSIONS
    allowed_script_extensions: frozenset[str] = ALLOWED_SCRIPT_EXTENSIONS
    max_file_size: int = MAX_FILE_SIZE
    max_read_size: int = MAX_READ_SIZE
    script_timeout: int = SCRIPT_TIMEOUT
    resource_dirs: tuple[str, ...] = RESOURCE_DIRS
    skill_filename: str = SKILL_FILENAME
    skill_scan_patterns: tuple[str, ...] = SKILL_SCAN_PATTERNS
    verbose: bool = False

    def __post_init__(self) -> None:
        if isinstance(self.skills_dir, str): self.skills_dir = Path(self.skills_dir)
        if isinstance(self.workspace_dir, str): self.workspace_dir = Path(self.workspace_dir)
        self.skills_dir = self.skills_dir.resolve()
        self.workspace_dir = self.workspace_dir.resolve()

    def ensure_directories(self) -> None:
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_args(cls, skills_dir: Optional[Path] = None, workspace_dir: Optional[Path] = None, verbose: bool = False) -> Settings:
        kwargs: dict = {"verbose": verbose}
        if skills_dir is not None: kwargs["skills_dir"] = skills_dir
        if workspace_dir is not None: kwargs["workspace_dir"] = workspace_dir
        return cls(**kwargs)

def load_config(skills_dir: Optional[Path] = None, workspace_dir: Optional[Path] = None, verbose: bool = False) -> Settings:
    env_skills_dir = os.environ.get("SKILL_MCP_SKILLS_DIR")
    env_workspace_dir = os.environ.get("SKILL_MCP_WORKSPACE_DIR")
    env_verbose = os.environ.get("SKILL_MCP_VERBOSE", "").lower() in ("1", "true", "yes")
    
    final_skills_dir = skills_dir or (Path(env_skills_dir) if env_skills_dir else None)
    final_workspace_dir = workspace_dir or (Path(env_workspace_dir) if env_workspace_dir else None)
    final_verbose = verbose or env_verbose
    
    return Settings.from_args(skills_dir=final_skills_dir, workspace_dir=final_workspace_dir, verbose=final_verbose)

# --- Security ---

class PathValidator:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir.resolve()

    def validate(self, relative_path: str) -> Path:
        target_path = (self.base_dir / relative_path).resolve()
        if not self.is_within_base(target_path):
            raise PathValidationError(f"Security error: Path '{relative_path}' resolves outside '{self.base_dir}'")
        return target_path

    def is_within_base(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self.base_dir)
            return True
        except ValueError:
            return False

    def validate_file(self, relative_path: str) -> Path:
        target_path = self.validate(relative_path)
        if not target_path.exists(): raise PathValidationError(f"Path not found: {relative_path}")
        if not target_path.is_file(): raise PathValidationError(f"Not a file: {relative_path}")
        return target_path

class FileValidator:
    def __init__(self, allowed_extensions=ALLOWED_FILE_EXTENSIONS, allowed_script_extensions=ALLOWED_SCRIPT_EXTENSIONS, max_file_size=MAX_FILE_SIZE, max_read_size=MAX_READ_SIZE):
        self.allowed_extensions = allowed_extensions
        self.allowed_script_extensions = allowed_script_extensions
        self.max_file_size = max_file_size
        self.max_read_size = max_read_size

    def validate_extension(self, path: Path) -> None:
        suffix = path.suffix.lower()
        if suffix not in self.allowed_extensions:
            raise FileValidationError(f"File type '{suffix}' not allowed.")

    def validate_script_extension(self, path: Path) -> None:
        suffix = path.suffix.lower()
        if suffix not in self.allowed_script_extensions:
            raise FileValidationError(f"Script type '{suffix}' not allowed.")

    def validate_read_size(self, path: Path) -> int:
        file_size = path.stat().st_size
        if file_size > self.max_read_size:
            raise FileValidationError(f"File too large: {file_size} bytes")
        return file_size

    def validate_write_size(self, content: str | bytes) -> int:
        size = len(content.encode("utf-8")) if isinstance(content, str) else len(content)
        if size > self.max_file_size:
            raise FileValidationError(f"Content too large: {size} bytes")
        return size

    def validate_for_script(self, path: Path) -> None:
        self.validate_script_extension(path)

# --- Executors ---

@dataclass
class ExecutionResult:
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out

class BaseExecutor(ABC):
    extensions: tuple[str, ...] = ()
    def __init__(self, timeout: int = SCRIPT_TIMEOUT) -> None:
        self.timeout = timeout

    @abstractmethod
    def build_command(self, script_path: Path, args: list[str]) -> list[str]: pass

    def execute(self, script_path: Path, working_dir: Path, args: Optional[list[str]] = None) -> ExecutionResult:
        cmd = self.build_command(script_path, args or [])
        try:
            result = subprocess.run(cmd, cwd=str(working_dir), capture_output=True, text=True, timeout=self.timeout)
            return ExecutionResult(exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr)
        except subprocess.TimeoutExpired:
            return ExecutionResult(exit_code=-1, stdout="", stderr=f"Timed out after {self.timeout}s", timed_out=True)
        except Exception as e:
            raise ExecutionError(f"Failed to execute: {e}") from e

    def can_execute(self, path: Path) -> bool:
        return path.suffix.lower() in self.extensions

class PythonExecutor(BaseExecutor):
    extensions = (".py",)
    def build_command(self, script_path: Path, args: list[str]) -> list[str]:
        return [sys.executable, str(script_path)] + args

class ShellExecutor(BaseExecutor):
    extensions = (".sh", ".bash")
    def __init__(self, shell: str = "bash", **kwargs) -> None:
        super().__init__(**kwargs)
        self.shell = shell
    def build_command(self, script_path: Path, args: list[str]) -> list[str]:
        return [self.shell, str(script_path)] + args

class NodeExecutor(BaseExecutor):
    extensions = (".js",)
    def build_command(self, script_path: Path, args: list[str]) -> list[str]:
        return ["node", str(script_path)] + args

class TypeScriptExecutor(BaseExecutor):
    extensions = (".ts",)
    def build_command(self, script_path: Path, args: list[str]) -> list[str]:
        return ["npx", "ts-node", str(script_path)] + args

class ExecutorFactory:
    def __init__(self, timeout: int = SCRIPT_TIMEOUT) -> None:
        self.timeout = timeout
        self._executors = [
            PythonExecutor(timeout=timeout),
            ShellExecutor(timeout=timeout),
            NodeExecutor(timeout=timeout),
            TypeScriptExecutor(timeout=timeout)
        ]

    def get_executor(self, path: Path) -> Optional[BaseExecutor]:
        for e in self._executors:
            if e.can_execute(path): return e
        return None

_executor_factory: Optional[ExecutorFactory] = None
def get_executor(path: Path, timeout: int = SCRIPT_TIMEOUT) -> BaseExecutor:
    global _executor_factory
    if _executor_factory is None: _executor_factory = ExecutorFactory(timeout=timeout)
    executor = _executor_factory.get_executor(path)
    if not executor: raise ExecutionError(f"No executor for {path.suffix}")
    return executor

# --- Tools ---

class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str: pass
    @property
    @abstractmethod
    def description(self) -> str: pass
    @abstractmethod
    def execute(self, **kwargs: Any) -> str: pass

class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool
    def register_many(self, tools: list[BaseTool]) -> None:
        for t in tools: self.register(t)
    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)
    def count(self) -> int: return len(self._tools)

class FileReaderTool(BaseTool):
    def __init__(self, workspace_dir: Path, file_validator: FileValidator) -> None:
        self.workspace_dir = workspace_dir
        self.path_validator = PathValidator(workspace_dir)
        self.file_validator = file_validator
    @property
    def name(self) -> str: return "file_read"
    @property
    def description(self) -> str: return "Read a file from the workspace."
    def execute(self, path: str = "", **kwargs: Any) -> str:
        file_path = path or kwargs.get("file_path", "")
        if not file_path: raise ToolError("file_path required")
        try:
            p = self.path_validator.validate_file(file_path)
            self.file_validator.validate_extension(p)
            self.file_validator.validate_read_size(p)
            return p.read_text(encoding="utf-8")
        except Exception as e: return f"Error: {e}"

class FileWriterTool(BaseTool):
    def __init__(self, workspace_dir: Path, file_validator: FileValidator) -> None:
        self.workspace_dir = workspace_dir
        self.path_validator = PathValidator(workspace_dir)
        self.file_validator = file_validator
    @property
    def name(self) -> str: return "file_write"
    @property
    def description(self) -> str: return "Create or overwrite a file in the workspace."
    def execute(self, path: str = "", content: str = "", **kwargs: Any) -> str:
        file_path = path or kwargs.get("file_path", "")
        if not file_path: raise ToolError("file_path required")
        try:
            p = self.path_validator.validate(file_path)
            self.file_validator.validate_write_size(content)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return f"File written to {file_path}"
        except Exception as e: return f"Error: {e}"

class FileEditorTool(BaseTool):
    def __init__(self, workspace_dir: Path, file_validator: FileValidator) -> None:
        self.workspace_dir = workspace_dir
        self.path_validator = PathValidator(workspace_dir)
        self.file_validator = file_validator
    @property
    def name(self) -> str: return "file_edit"
    @property
    def description(self) -> str: return "Edit a file using search and replace."
    def execute(self, path: str = "", old_string: str = "", new_string: str = "", replace_all: bool = False, **kwargs: Any) -> str:
        file_path = path or kwargs.get("file_path", "")
        edits = kwargs.get("edits")
        if edits and isinstance(edits, list):
            return self._execute_bulk(file_path, edits)
            
        if not file_path or not old_string: raise ToolError("file_path and old_string required")
        try:
            p = self.path_validator.validate_file(file_path)
            content = p.read_text(encoding="utf-8")
            if old_string not in content: return f"Error: '{old_string}' not found"
            if not replace_all and content.count(old_string) > 1: return "Error: old_string not unique"
            new_content = content.replace(old_string, new_string) if replace_all else content.replace(old_string, new_string, 1)
            self.file_validator.validate_write_size(new_content)
            p.write_text(new_content, encoding="utf-8")
            return f"File {file_path} edited successfully"
        except Exception as e: return f"Error: {e}"

    def _execute_bulk(self, file_path: str, edits: list[dict[str, Any]]) -> str:
        try:
            p = self.path_validator.validate_file(file_path)
            content = p.read_text(encoding="utf-8")
            for edit in edits:
                old = edit.get("old_string")
                new = edit.get("new_string")
                if not old: continue
                content = content.replace(old, new)
            self.file_validator.validate_write_size(content)
            p.write_text(content, encoding="utf-8")
            return f"File {file_path} bulk-edited successfully"
        except Exception as e: return f"Error: {e}"

class ScriptRunRequest(BaseModel):
    skill_name: str = Field(..., description="技能目錄的名稱，例如 'data-analyzer'")
    script_name: str = Field(default="script.py", description="要執行的腳本檔案名稱 (必須位於該技能目錄下)，例如 'main.py'、'build.sh'。預設為 'script.py'。")
    env_vars: Dict[str, str] = Field(default_factory=dict, description="執行腳本前注入的系統環境變數。例如: {'NODE_ENV': 'production', 'API_KEY': '123'}")
    optional_args: Dict[str, Any] = Field(default_factory=dict, description="可選參數與旗標。鍵名(Key)必須以破折號開頭。請完全依照標準指令的寫法傳遞，絕對不要自行拆解字元。正確範例: {'-lah': True, '-name': 'test.txt', '--port': 8080}")
    positional_args: List[str] = Field(default_factory=list, description="位置參數。請嚴格按照腳本要求的順序傳入。例如: ['input.csv', 'output.json']")
    timeout_seconds: int = Field(default=30, ge=5, le=300, description="腳本執行的超時限制 (5~300秒)，預設為 30 秒")

    @field_validator('skill_name', 'script_name')
    @classmethod
    def validate_paths(cls, v: str, info) -> str:
        if "/" in v or "\\" in v or ".." in v:
            raise ValueError(f"{info.field_name} 只能是單一名稱，絕對不可包含路徑符號 (/, \\, ..)")
        return v

    @model_validator(mode='after')
    def validate_options(self):
        for key in self.optional_args.keys():
            if not str(key).startswith("-"):
                raise ValueError(f"參數錯誤: '{key}' 不是合法的 Option。鍵名必須以 '-' 或 '--' 開頭。")
        return self

class ScriptExecutorTool(BaseTool):
    def __init__(self, skills_dir: Path, file_validator: FileValidator, workspace_dir: Path, timeout=120) -> None:
        self.skills_dir, self.file_validator = skills_dir, file_validator
        self.workspace_dir, self.timeout = workspace_dir, timeout
    @property
    def name(self) -> str: return "skill_script"
    @property
    def description(self) -> str: return "在安全隔離的環境下執行技能腳本，並回傳完整的標準輸出與錯誤日誌供 AI 解析。"
    def execute(self, request: ScriptRunRequest, **kwargs: Any) -> str:
        skill_dir = self.skills_dir / request.skill_name
        if not skill_dir.is_dir(): return f"❌ 執行失敗：找不到技能 '{request.skill_name}'"
        
        script_path = skill_dir / request.script_name
        if not script_path.is_file():
            return f"❌ 執行失敗：在技能 '{request.skill_name}' 中找不到腳本 '{request.script_name}'"

        try:
            self.file_validator.validate_script_extension(script_path)
        except Exception as e:
            return f"❌ 執行失敗：副檔名不支援 - {e}"

        cmd_args = []
        for key, value in request.optional_args.items():
            cmd_args.append(str(key))
            if isinstance(value, bool):
                if value is False: cmd_args.pop()
                continue
            elif value is not None:
                cmd_args.append(str(value))
        cmd_args.extend([str(arg) for arg in request.positional_args])
        
        ext = script_path.suffix.lower()
        if ext == ".py":
            base_command = [sys.executable, str(script_path)]
        elif ext == ".sh" or ext == ".bash":
            base_command = ["bash", str(script_path)]
        elif ext == ".js":
            base_command = ["node", str(script_path)]
        elif ext == ".ts":
            base_command = ["npx", "ts-node", str(script_path)]
        else:
            base_command = [str(script_path)]

        command = base_command + cmd_args

        execution_env = os.environ.copy()
        for k, v in request.env_vars.items():
            execution_env[k] = str(v)

        try:
            result = subprocess.run(
                command,
                cwd=skill_dir,
                stdin=subprocess.DEVNULL,
                env=execution_env,
                capture_output=True,
                text=True,
                timeout=request.timeout_seconds
            )

            if result.returncode == 0:
                return (
                    f"✅ 腳本執行成功\n"
                    f"--- 執行指令 ---\n{' '.join(command)}\n"
                    f"--- 標準輸出 (Stdout) ---\n"
                    f"{result.stdout.strip() or '(無輸出內容)'}"
                )
            else:
                return (
                    f"⚠️ 腳本執行失敗 (Return Code: {result.returncode})\n"
                    f"--- 執行指令 ---\n{' '.join(command)}\n"
                    f"--- 標準輸出 (Stdout) ---\n"
                    f"{result.stdout.strip() or '(無輸出內容)'}\n"
                    f"--- 錯誤訊息 (Stderr) ---\n"
                    f"{result.stderr.strip() or '(無錯誤訊息)'}\n"
                    f"💡 請分析上述錯誤訊息，修改你的參數後重新呼叫此工具。"
                )
        except subprocess.TimeoutExpired:
            return f"⏳ 執行超時：腳本運行超過了 {request.timeout_seconds} 秒已被強制終止。"
        except PermissionError:
            return f"🚫 權限不足：無法執行 {request.script_name}。請確認該檔案是否有執行權限 (chmod +x) 或副檔名是否正確支援。"
        except Exception as e:
            return f"💥 系統層級錯誤：無法啟動子進程。詳細資訊：{str(e)}"

# --- Server ---

class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, api_key: str):
        super().__init__(app)
        self.api_key = api_key
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS": return await call_next(request)
        auth = request.headers.get("authorization")
        if not auth or auth != f"Bearer {self.api_key}":
            return JSONResponse(status_code=401, content={"error": "Unauthorized"})
        return await call_next(request)

class SkillMCPServer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.settings.ensure_directories()
        self.file_validator = FileValidator(
            allowed_extensions=settings.allowed_file_extensions,
            allowed_script_extensions=settings.allowed_script_extensions,
            max_file_size=settings.max_file_size,
            max_read_size=settings.max_read_size
        )
        self.registry = ToolRegistry()
        self._init_tools()
        self.mcp = FastMCP("skill-mcp-server")
        self.mcp.add_provider(SkillsDirectoryProvider(roots=[self.settings.skills_dir]))
        self._init_mcp_server()

    def _init_tools(self) -> None:
        self.tools = [
            ScriptExecutorTool(self.settings.skills_dir, self.file_validator, self.settings.workspace_dir, self.settings.script_timeout),
            FileReaderTool(self.settings.workspace_dir, self.file_validator),
            FileWriterTool(self.settings.workspace_dir, self.file_validator),
            FileEditorTool(self.settings.workspace_dir, self.file_validator)
        ]
        self.registry.register_many(self.tools)

    def _init_mcp_server(self) -> None:
        executor = self.registry.get("skill_script")
        f_reader = self.registry.get("file_read")
        f_writer = self.registry.get("file_write")
        f_editor = self.registry.get("file_edit")

        @self.mcp.tool(name=executor.name, description=executor.description)
        def skill_script(request: ScriptRunRequest) -> str:
            return executor.execute(request=request)

        @self.mcp.tool(name=f_reader.name, description=f_reader.description)
        def file_read(path: str) -> str: return f_reader.execute(path=path)

        @self.mcp.tool(name=f_writer.name, description=f_writer.description)
        def file_write(path: str, content: str) -> str: return f_writer.execute(path=path, content=content)

        @self.mcp.tool(name=f_editor.name, description=f_editor.description)
        def file_edit(path: str, edits: list[dict[str, Any]]) -> str:
            return f_editor.execute(path=path, edits=edits)

    async def run(self) -> None:
        get_logger().info("Starting Skill MCP Server (stdio)...")
        await asyncio.to_thread(self.mcp.run, transport="stdio")

    async def run_sse(self, host="0.0.0.0", port=8000) -> None:
        if uvicorn is None: raise ServerError("uvicorn and starlette required for SSE")
        get_logger().info(f"Starting Skill MCP Server (SSE) on http://{host}:{port}")
        app = self.mcp.http_app()
        api_key = os.environ.get("SKILL_MCP_API_KEY")
        if api_key: app.add_middleware(APIKeyAuthMiddleware, api_key=api_key)
        config = uvicorn.Config(app, host=host, port=port, log_level="info")
        await uvicorn.Server(config).serve()

def create_server(skills_dir=None, workspace_dir=None, verbose=False) -> SkillMCPServer:
    setup_logging(verbose=verbose)
    settings = load_config(skills_dir=skills_dir, workspace_dir=workspace_dir, verbose=verbose)
    return SkillMCPServer(settings)

# --- CLI ---

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="skill-mcp-server", description="Skill MCP Server")
    parser.add_argument("--skills-dir", type=str, default=None, help="Directory containing skill folders")
    parser.add_argument("--workspace", type=str, default=None, help="Working directory for file operations")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--version", action="version", version="0.1.0")
    return parser.parse_args()

def main() -> int:
    args = parse_args()
    try:
        server = create_server(
            skills_dir=Path(args.skills_dir) if args.skills_dir else None,
            workspace_dir=Path(args.workspace) if args.workspace else None,
            verbose=args.verbose
        )
        asyncio.run(server.run())
        return 0
    except KeyboardInterrupt: return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    if os.environ.get("SKILL_MCP_LOG_LEVEL", "").upper() == "SILENT":
        logging.disable(logging.CRITICAL)
        sys.stderr = open(os.devnull, "w")
    sys.exit(main())
