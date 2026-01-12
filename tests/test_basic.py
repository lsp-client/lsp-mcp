"""Basic tests for LSP-MCP server."""

import pytest

import lsp_mcp_server


def test_server_imports():
    """Test that the server module can be imported."""
    assert hasattr(lsp_mcp_server, 'mcp')
    assert hasattr(lsp_mcp_server, 'init_lsp_client')
    assert hasattr(lsp_mcp_server, 'get_definition')
    assert hasattr(lsp_mcp_server, 'find_references')
    assert hasattr(lsp_mcp_server, 'get_outline')
    assert hasattr(lsp_mcp_server, 'get_hover_info')
    assert hasattr(lsp_mcp_server, 'search_workspace')
    assert hasattr(lsp_mcp_server, 'shutdown_lsp_client')


def test_mcp_server_creation():
    """Test that the MCP server is created correctly."""
    assert lsp_mcp_server.mcp is not None
    assert lsp_mcp_server.mcp.name == "lsp-mcp"


def test_client_not_initialized_error():
    """Test that accessing client before initialization raises error."""
    # Reset client to None
    lsp_mcp_server._lsp_client = None
    
    with pytest.raises(ValueError, match="LSP client not initialized"):
        lsp_mcp_server.get_client()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
