# Copyright (c) 2025
# SPDX-License-Identifier: MIT

"""Main MCP Server implementation."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

import uvicorn
from fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from ..config.loader import load_config
from ..config.settings import Settings
from ..security.file_validator import FileValidator
from ..skill.manager import SkillManager
from ..tools.file_editor import FileEditorTool
from ..tools.file_reader import FileReaderTool
from ..tools.file_writer import FileWriterTool
from ..tools.resource_reader import ResourceReaderTool
from ..tools.script_executor import ScriptExecutorTool
from ..tools.skill_lister import SkillListerTool
from ..tools.skill_loader import SkillLoaderTool
from ..utils.logging import get_logger, setup_logging
from .registry import ToolRegistry

logger = get_logger("core.server")


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Simple API Key Authentication Middleware."""

    def __init__(self, app, api_key: str):
        super().__init__(app)
        self.api_key = api_key

    async def dispatch(self, request: Request, call_next):
        # 允許 CORS preflight 請求直接通過 (若未來有瀏覽器前端整合需求)
        if request.method == "OPTIONS":
            return await call_next(request)

        auth_header = request.headers.get("authorization")
        expected = f"Bearer {self.api_key}"

        if not auth_header or auth_header != expected:
            logger.warning(f"Unauthorized access attempt from {request.client.host}")
            return JSONResponse(status_code=401, content={"error": "Unauthorized"})

        return await call_next(request)


class SkillMCPServer:
    """Skill MCP Server - exposes skills as MCP tools.

    This is the main entry point for the MCP server. It coordinates
    all components and handles the MCP protocol.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize the server.

        Args:
            settings: Server configuration.
        """
        self.settings = settings

        # Ensure directories exist
        self.settings.ensure_directories()

        # Initialize components
        self._init_validators()
        self._init_skill_manager()
        self._init_tools()
        self._init_mcp_server()

    def _init_validators(self) -> None:
        """Initialize security validators."""
        self.file_validator = FileValidator(
            allowed_extensions=self.settings.allowed_file_extensions,
            allowed_script_extensions=self.settings.allowed_script_extensions,
            max_file_size=self.settings.max_file_size,
            max_read_size=self.settings.max_read_size,
        )

    def _init_skill_manager(self) -> None:
        """Initialize the skill manager."""
        self.skill_manager = SkillManager(
            skill_dirs=[self.settings.skills_dir],
            scan_patterns=self.settings.skill_scan_patterns,
            resource_dirs=self.settings.resource_dirs,
        )

    def _init_tools(self) -> None:
        """Initialize and register all tools."""
        self.registry = ToolRegistry()

        # Create tool instances
        self.skill_loader = SkillLoaderTool(skill_manager=self.skill_manager)
        self.skill_lister = SkillListerTool(
            skill_manager=self.skill_manager,
            skills_dir=self.settings.skills_dir,
        )
        self.resource_reader = ResourceReaderTool(
            skill_manager=self.skill_manager,
            file_validator=self.file_validator,
        )
        self.script_executor = ScriptExecutorTool(
            skill_manager=self.skill_manager,
            file_validator=self.file_validator,
            workspace_dir=self.settings.workspace_dir,
            script_timeout=self.settings.script_timeout,
        )
        self.file_reader = FileReaderTool(
            workspace_dir=self.settings.workspace_dir,
            file_validator=self.file_validator,
        )
        self.file_writer = FileWriterTool(
            workspace_dir=self.settings.workspace_dir,
            file_validator=self.file_validator,
        )
        self.file_editor = FileEditorTool(
            workspace_dir=self.settings.workspace_dir,
            file_validator=self.file_validator,
        )

        tools = [
            self.skill_loader,
            self.skill_lister,
            self.resource_reader,
            self.script_executor,
            self.file_reader,
            self.file_writer,
            self.file_editor,
        ]

        self.registry.register_many(tools)
        logger.info(f"Registered {self.registry.count()} tools")

    def _init_mcp_server(self) -> None:
        """Initialize FastMCP server and register tools."""
        self.mcp = FastMCP("skill-mcp-server")

        # 利用 FastMCP 以 Type Hints 來推導 Schema 的特性，宣告 Wrapper：

        @self.mcp.tool(name=self.skill_loader.name, description=self.skill_loader.description)
        def skill(name: str) -> str:
            return self.skill_loader.execute(name=name)

        @self.mcp.tool(name=self.skill_lister.name, description=self.skill_lister.description)
        def list_skills() -> str:
            return self.skill_lister.execute()

        @self.mcp.tool(name=self.resource_reader.name, description=self.resource_reader.description)
        def skill_resource(skill_name: str, resource_path: str) -> str:
            return self.resource_reader.execute(skill_name=skill_name, resource_path=resource_path)

        @self.mcp.tool(name=self.script_executor.name, description=self.script_executor.description)
        def skill_script(skill_name: str, script_name: str, args: dict[str, Any] | None = None) -> str:
            execute_args = {"skill_name": skill_name, "script_name": script_name}
            if args is not None:
                execute_args["args"] = args
            return self.script_executor.execute(**execute_args)

        @self.mcp.tool(name=self.file_reader.name, description=self.file_reader.description)
        def file_read(path: str) -> str:
            return self.file_reader.execute(path=path)

        @self.mcp.tool(name=self.file_writer.name, description=self.file_writer.description)
        def file_write(path: str, content: str) -> str:
            return self.file_writer.execute(path=path, content=content)

        @self.mcp.tool(name=self.file_editor.name, description=self.file_editor.description)
        def file_edit(path: str, edits: list[dict[str, Any]]) -> str:
            return self.file_editor.execute(path=path, edits=edits)

    async def run(self) -> None:
        """Run the MCP server over stdio."""
        logger.info("Starting Skill MCP Server...")

        # Pre-load skills
        skills = self.skill_manager.all()
        logger.info(f"Loaded {len(skills)} skills: {[s.name for s in skills]}")

        # fastmcp.run() 為同步阻塞並有自己的 Event Loop，
        # 由於外部 __main__ 已使用 asyncio.run()，我們用 to_thread 避免 Event Loop 衝突
        await asyncio.to_thread(self.mcp.run, transport="stdio")

    async def run_sse(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """Run the MCP server over HTTP/SSE."""
        logger.info(f"Starting Skill MCP Server (FastMCP SSE) on http://{host}:{port}...")

        # Pre-load skills
        skills = self.skill_manager.all()
        logger.info(f"Loaded {len(skills)} skills: {[s.name for s in skills]}")

        # 1. 取得 FastMCP 底層的 ASGI 應用程式 (Starlette App)
        app = self.mcp.http_app()

        # 2. 檢查是否設定了 API Key，若有則掛載驗證 Middleware
        api_key = os.environ.get("SKILL_MCP_API_KEY")
        if api_key:
            logger.info("Authentication enabled. API Key is required.")
            app.add_middleware(APIKeyAuthMiddleware, api_key=api_key)
        else:
            logger.warning("No SKILL_MCP_API_KEY found. Server is running WITHOUT authentication!")

        # 3. 透過 Uvicorn 的異步 API 啟動伺服器
        config = uvicorn.Config(app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()


def create_server(
    skills_dir: Path | None = None,
    workspace_dir: Path | None = None,
    verbose: bool = False,
) -> SkillMCPServer:
    """Create a configured SkillMCPServer instance.

    This is the recommended way to create a server instance.

    Args:
        skills_dir: Path to skills directory.
        workspace_dir: Path to workspace directory.
        verbose: Enable verbose logging.

    Returns:
        Configured SkillMCPServer instance.

    Example:
        >>> server = create_server(
        ...     skills_dir=Path("./skills"),
        ...     workspace_dir=Path("./workspace"),
        ... )
        >>> import asyncio
        >>> asyncio.run(server.run())
    """
    # Setup logging
    setup_logging(verbose=verbose)

    # Load configuration
    settings = load_config(
        skills_dir=skills_dir,
        workspace_dir=workspace_dir,
        verbose=verbose,
    )

    return SkillMCPServer(settings)
