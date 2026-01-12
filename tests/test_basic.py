"""Basic tests for LSP-MCP server."""

import pytest


def test_server_imports():
    """Test that the server module can be imported."""
    import lsp_mcp_server
    
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
    from lsp_mcp_server import mcp
    
    assert mcp is not None
    assert mcp.name == "lsp-mcp"


def test_client_not_initialized_error():
    """Test that accessing client before initialization raises error."""
    from lsp_mcp_server import get_client
    
    # Reset client to None
    import lsp_mcp_server
    lsp_mcp_server._lsp_client = None
    
    with pytest.raises(ValueError, match="LSP client not initialized"):
        get_client()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
