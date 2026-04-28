"""
SynthesAI MCP Package - MCP Protocol Adapter.

This package provides MCP server implementation for SynthesAI,
allowing Claude Desktop and other MCP clients to use SynthesAI tools.

Quick Start:
    # Install MCP support
    pip install "synthesai[mcp]"

    # Run MCP server (for testing)
    python -m learning_assistant.mcp.server

    # Configure in Claude Desktop
    # Add to ~/Library/Application Support/Claude/claude_desktop_config.json:
    {
        "mcpServers": {
            "synthesai": {
                "command": "python",
                "args": ["-m", "learning_assistant.mcp.server"],
                "env": {
                    "OPENAI_API_KEY": "sk-...",
                    "ANTHROPIC_API_KEY": "sk-..."
                }
            }
        }
    }
"""

from learning_assistant.mcp.server import server, main, run_server

__all__ = ["server", "main", "run_server"]