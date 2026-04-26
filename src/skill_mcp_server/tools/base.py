# Copyright (c) 2025
# SPDX-License-Identifier: MIT

"""Base tool interface for MCP tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ToolError(Exception):
    """Raised when a tool execution fails."""

    pass


class BaseTool(ABC):
    """Abstract base class for MCP tools.

    Each tool implementation should:
    1. Define its name and description
    2. Implement the execute method
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the tool name.

        Returns:
            Unique tool identifier.
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Get the tool description.

        Returns:
            Human-readable description of what the tool does.
        """
        pass

    @abstractmethod
    def execute(self, **kwargs: Any) -> str:
        """Execute the tool with the given arguments.

        Args:
            **kwargs: Tool-specific arguments.

        Returns:
            Result string to return to the client.

        Raises:
            ToolError: If execution fails.
        """
        pass
