#!/usr/bin/env python3
"""
Skill MCP Client (Beginner-Friendly Demo)

这是一个「干净、安静、适合入门」的终端 AI 示例程序。
默认只显示用户输入和 AI 输出，不展示任何内部日志。

用法：
  python demo.py --skills-dir ./skills
  python demo.py --skills-dir ./skills --verbose
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from openai import AsyncOpenAI


# =========================
# 全局 CLI 行为配置
# =========================
QUIET = True  # 默认安静（适合 demo & 新手）


# =========================
# 终端输出工具
# =========================
class Console:
    RESET = "\033[0m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    CYAN = "\033[36m"
    RED = "\033[31m"

    @staticmethod
    def prompt():
        return f"{Console.CYAN}>{Console.RESET} "

    @staticmethod
    def info(msg: str):
        print(f"{Console.DIM}{msg}{Console.RESET}")

    @staticmethod
    def error(msg: str):
        print(f"{Console.RED}✗ {msg}{Console.RESET}", file=sys.stderr)

    @staticmethod
    def debug(msg: str):
        if not QUIET:
            print(f"{Console.DIM}{msg}{Console.RESET}")


# =========================
# MCP + OpenAI 客户端
# =========================
class MCPClient:
    def __init__(
        self,
        openai_client: AsyncOpenAI,
        session: ClientSession,
        model: str,
    ):
        self.openai = openai_client
        self.session = session
        self.model = model

        self.tools: list[dict] = []
        self.messages: list[dict] = []

    async def load_tools(self):
        """从 MCP Server 加载工具定义"""
        resp = await self.session.list_tools()

        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description or "",
                    "parameters": t.inputSchema
                    or {"type": "object", "properties": {}},
                },
            }
            for t in resp.tools
        ]

        Console.debug(f"Loaded {len(self.tools)} tools")

    async def call_tool(self, name: str, args: dict[str, Any]) -> str:
        """执行工具"""
        try:
            result = await self.session.call_tool(name, args)
            return result.content[0].text if result.content else ""
        except Exception as e:
            return f"Tool error: {e}"

    async def chat(self, user_input: str) -> str:
        """发送一条用户消息，返回 AI 最终回复"""
        self.messages.append({"role": "user", "content": user_input})

        while True:
            resp = await self.openai.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=self.tools or None,
            )

            msg = resp.choices[0].message

            # 没有工具调用，说明这是最终回答
            if not msg.tool_calls:
                text = msg.content or ""
                self.messages.append({"role": "assistant", "content": text})
                return text

            # 有工具调用：先记录 assistant 的请求
            self.messages.append(
                {
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in msg.tool_calls
                    ],
                }
            )

            # 逐个执行工具
            for tc in msg.tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments)

                Console.debug(f"→ tool: {name} {args}")

                result = await self.call_tool(name, args)

                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    }
                )

    def clear(self):
        """清空对话上下文"""
        self.messages.clear()


# =========================
# 参数解析
# =========================
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Skill MCP Client (Beginner Demo)"
    )

    parser.add_argument(
        "--url",
        type=str,
        help="遠端 MCP Server 的 SSE 端點 (例如 http://localhost:8000/sse)。若指定此項，則透過 SSE 連線。",
    )

    parser.add_argument(
        "-H", "--header",
        action="append",
        help="自訂 HTTP Header (例如 'Authorization: Bearer YOUR_TOKEN')，可多次使用",
    )

    parser.add_argument(
        "--skills-dir",
        type=Path,
        help="本地 stdio 模式下的技能（tools）所在目錄",
    )

    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd() / "workspace",
        help="工作目录（默认 ./workspace）",
    )

    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="OpenAI 模型名（默认 gpt-4o）",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="显示调试信息（工具调用、内部状态）",
    )

    return parser.parse_args()


# =========================
# 主流程
# =========================
async def run(args: argparse.Namespace):
    global QUIET
    QUIET = not args.verbose

    # 关闭第三方库日志
    logging.getLogger("mcp").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.ERROR)

    # 检查 API Key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        Console.error("缺少环境变量 OPENAI_API_KEY")
        sys.exit(1)

    if not args.url:
        if not args.skills_dir:
            Console.error("本地模式下必須提供 --skills-dir (或使用 --url 連線遠端)")
            sys.exit(1)
        if not args.skills_dir.exists():
            Console.error(f"技能目录不存在: {args.skills_dir}")
            sys.exit(1)
        args.workspace.mkdir(parents=True, exist_ok=True)

    # OpenAI Client
    openai_client = AsyncOpenAI(
        api_key=api_key,
        base_url=os.environ.get("OPENAI_BASE_URL"),
    )

    # 解析自訂 Headers
    headers = {}
    if args.header:
        for h in args.header:
            if ":" in h:
                k, v = h.split(":", 1)
                headers[k.strip()] = v.strip()
            else:
                Console.error(f"無效的 Header 格式: {h} (應為 'Key: Value')")
                sys.exit(1)

    async with AsyncExitStack() as stack:
        if args.url:
            Console.info(f"Connecting to remote MCP server via SSE: {args.url}")
            read, write = await stack.enter_async_context(sse_client(args.url, headers=headers or None))
        else:
            Console.info("Starting local MCP server via stdio...")
            server_params = StdioServerParameters(
                command="python",
                args=[
                    "-m",
                    "skill_mcp_server",
                    "--skills-dir",
                    str(args.skills_dir.resolve()),
                    "--workspace",
                    str(args.workspace.resolve()),
                ],
                env={**os.environ, "SKILL_MCP_LOG_LEVEL": "SILENT"},
            )
            read, write = await stack.enter_async_context(stdio_client(server_params))

        session = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()

        client = MCPClient(openai_client, session, args.model)
        await client.load_tools()

        # 欢迎信息
        print()
        print(f"{Console.BOLD}Skill MCP Client{Console.RESET}")
        print(f"{Console.DIM}输入问题开始对话，/help 查看命令{Console.RESET}")
        print()

        while True:
            try:
                user_input = input(Console.prompt()).strip()
                if not user_input:
                    continue

                if user_input in ("/quit", "/exit", "/q"):
                    break

                if user_input == "/clear":
                    client.clear()
                    Console.info("对话已清空")
                    continue

                if user_input == "/help":
                    print("/clear  清空对话")
                    print("/quit   退出程序")
                    continue

                reply = await client.chat(user_input)
                print()
                print(reply)
                print()

            except (KeyboardInterrupt, EOFError):
                print()
                break
            except Exception as e:
                Console.error(str(e))

    Console.info("Bye 👋")


def main():
    args = parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()