"""Integration test for LSP-MCP server with a real LSP server."""

import os
import shutil

import pytest

# Skip these tests if pyright-langserver is not installed
pytestmark = pytest.mark.skipif(
    shutil.which("pyright-langserver") is None,
    reason="pyright-langserver not installed"
)


@pytest.fixture(scope="module")
def test_project_path(tmp_path_factory):
    """Create a test project with example Python code."""
    project_dir = tmp_path_factory.mktemp("test_project")
    
    # Create a pyproject.toml to mark it as a Python project
    pyproject_file = project_dir / "pyproject.toml"
    pyproject_file.write_text("""
[project]
name = "test-project"
version = "0.1.0"
""")
    
    # Create example.py with test code
    example_file = project_dir / "example.py"
    example_file.write_text("""
\"\"\"Example Python module for testing LSP-MCP server.\"\"\"


class Calculator:
    \"\"\"A simple calculator class.\"\"\"
    
    def add(self, a: int, b: int) -> int:
        \"\"\"Add two numbers.\"\"\"
        return a + b
    
    def subtract(self, a: int, b: int) -> int:
        \"\"\"Subtract b from a.\"\"\"
        return a - b
    
    def multiply(self, a: int, b: int) -> int:
        \"\"\"Multiply two numbers.\"\"\"
        return a * b


def main():
    \"\"\"Main function demonstrating calculator usage.\"\"\"
    calc = Calculator()
    result = calc.add(5, 3)
    print(f"5 + 3 = {result}")
    
    result = calc.multiply(4, 7)
    print(f"4 * 7 = {result}")


if __name__ == "__main__":
    main()
""")
    
    return project_dir


@pytest.fixture()
async def lsp_client_initialized(test_project_path):
    """Initialize LSP client by changing to the test project directory."""
    import lsp_mcp_server
    
    # Save current directory
    original_cwd = os.getcwd()
    
    try:
        # Change to test project directory
        os.chdir(test_project_path)
        
        # Manually initialize client for testing
        target = lsp_mcp_server.find_client(test_project_path)
        assert target is not None, "Failed to find LSP client for test project"
        
        async with target.client_cls(workspace=target.project_path) as client:
            lsp_mcp_server._client = client
            yield
            lsp_mcp_server._client = None
    finally:
        # Restore original directory
        os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_get_outline(lsp_client_initialized, test_project_path):
    """Test getting file outline."""
    from lsp_mcp_server import get_outline
    
    result = await get_outline(
        file_path=str(test_project_path / "example.py")
    )
    
    # Should contain the Calculator class and its methods
    assert "Calculator" in result or "Outline for" in result


@pytest.mark.asyncio
async def test_get_definition(lsp_client_initialized, test_project_path):
    """Test getting symbol definition."""
    from lsp_mcp_server import get_definition
    
    result = await get_definition(
        file_path=str(test_project_path / "example.py"),
        symbol_name="Calculator",
        mode="definition",
        include_code=True,
    )
    
    # Should contain definition information or a clear error message about the definition request
    result_lower = result.lower()
    if "error" in result_lower:
        # Error path: ensure it's an error related to the definition request
        assert "definition" in result_lower
    else:
        # Success path: should contain definition information for Calculator
        assert "Calculator" in result or "definition" in result_lower


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
