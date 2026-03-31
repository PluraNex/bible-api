"""
Base module for AI Agents.

Contains shared infrastructure for all agents:
- OpenAI Responses API client
- Tool executor base class
- Common schemas and utilities
"""

from .client import ResponsesAPIClient, RESPONSES_API_AVAILABLE
from .executor import ToolExecutor

__all__ = [
    "ResponsesAPIClient",
    "RESPONSES_API_AVAILABLE",
    "ToolExecutor",
]
