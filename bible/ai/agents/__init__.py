"""
AI Agents package.

Contains shared infrastructure for Bible API AI features.

Structure:
- base/: Shared infrastructure (ResponsesAPIClient, ToolExecutor)
- tools/: Legacy tools (NLP query, query expansion)
"""

# Base infrastructure
from .base import ResponsesAPIClient, RESPONSES_API_AVAILABLE, ToolExecutor

__all__ = [
    "ResponsesAPIClient",
    "RESPONSES_API_AVAILABLE",
    "ToolExecutor",
]
