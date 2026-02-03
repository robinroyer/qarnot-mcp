"""Entry point for Qarnot MCP Server."""

from src.qarnot_mcp.server import mcp

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
