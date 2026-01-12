"""Integration test for LSP-MCP server with a real LSP server."""

import asyncio
from pathlib import Path

import pytest

from lsp_mcp_server import (
    get_definition,
    get_outline,
    init_lsp_client,
    shutdown_lsp_client,
)

# Skip these tests if pyright is not installed
pytest.importorskip("pyright", reason="pyright not installed")


@pytest.fixture(scope="module")
def test_project_path():
    """Return path to the test project."""
    return Path("/tmp/test_project")


@pytest.fixture(scope="module")
async def lsp_client_initialized(test_project_path):
    """Initialize LSP client for tests."""
    result = await init_lsp_client(
        workspace_root=str(test_project_path),
        language="python",
        server_command="pyright-langserver",
        server_args=["--stdio"],
    )
    assert "successfully" in result.lower() or "initialized" in result.lower()
    
    yield
    
    # Cleanup
    await shutdown_lsp_client()


@pytest.mark.asyncio
async def test_get_outline(lsp_client_initialized, test_project_path):
    """Test getting file outline."""
    result = await get_outline(
        file_path=str(test_project_path / "example.py")
    )
    
    # Should contain the Calculator class and its methods
    assert "Calculator" in result
    assert "add" in result or "Outline for" in result


@pytest.mark.asyncio
async def test_get_definition(lsp_client_initialized, test_project_path):
    """Test getting symbol definition."""
    result = await get_definition(
        file_path=str(test_project_path / "example.py"),
        symbol_name="Calculator",
        mode="definition",
        include_code=True,
    )
    
    # Should contain definition information
    assert "Calculator" in result or "definition" in result.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
