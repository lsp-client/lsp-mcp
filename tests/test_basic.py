"""Basic tests for LSP-MCP server."""

import pytest

import lsp_mcp_server


def test_server_imports():
    """Test that the server module can be imported."""
    assert hasattr(lsp_mcp_server, 'mcp')
    assert hasattr(lsp_mcp_server, 'get_definition')
    assert hasattr(lsp_mcp_server, 'find_references')
    assert hasattr(lsp_mcp_server, 'get_outline')
    assert hasattr(lsp_mcp_server, 'get_hover_info')
    assert hasattr(lsp_mcp_server, 'search_workspace')


def test_mcp_server_creation():
    """Test that the MCP server is created correctly."""
    assert lsp_mcp_server.mcp is not None
    assert lsp_mcp_server.mcp.name == "lsp-mcp"


def test_client_not_initialized():
    """Test that client starts as None."""
    # Client should be None before initialization
    assert lsp_mcp_server._client is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
