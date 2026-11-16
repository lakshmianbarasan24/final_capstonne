"""
Reader Agent implementation using Google ADK (Agent Development Kit).
Wraps the FastMCP file reader tool and enforces role-based access control and PII scrubbing.
"""

from typing import Dict, Any
from mcp_servers.file_reader_server import read_file

READER_INSTRUCTION = """You are the Reader Agent in a secure AI Code Review System.
Your job is to fetch source code requested by the user or coordinator.
Rules:
1. You must call the file reader tool to fetch the file contents.
2. If the user role is not authorized or if access is denied by RBAC, immediately report that access is denied.
3. Never bypass security boundaries or attempt to reveal raw credentials.
"""

class ReaderAgent:
    """Google ADK Reader Agent."""
    def __init__(self, model: str = "gemini-2.0-flash"):
        self.name = "reader_agent"
        self.model = model
        self.instruction = READER_INSTRUCTION

    def execute(self, filepath: str, role: str = "reviewer", trace_id: str = "trace_000") -> Dict[str, Any]:
        """
        Executes file reading tool with role authorization.
        """
        content = read_file(filepath=filepath, role=role, trace_id=trace_id)
        is_denied = content.startswith("RBAC_ERROR") or content.startswith("FILE_NOT_FOUND")

        return {
            "agent": self.name,
            "filepath": filepath,
            "role": role,
            "status": "DENIED" if is_denied else "SUCCESS",
            "content": content,
            "tokens": max(len(content.split()), 1) + 25
        }
