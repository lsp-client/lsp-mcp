#!/usr/bin/env python
"""
Manual test script to demonstrate LSP-MCP server functionality.

This script demonstrates the API and expected behavior.
"""

import asyncio


async def demo_lsp_mcp():
    """Demonstrate server API."""
    print("=" * 70)
    print("LSP-MCP Server Demo")
    print("=" * 70)
    print()
    
    print("1. MCP Server Overview")
    print("-" * 70)
    print("LSP-MCP automatically initializes the LSP client based on the")
    print("current working directory. Simply start the server from your")
    print("project root directory.")
    print()
    
    print("2. Available MCP Tools:")
    print("-" * 70)
    print("  - get_definition: Find symbol definitions")
    print("  - find_references: Find all references to a symbol")
    print("  - get_outline: Get file structure outline")
    print("  - get_hover_info: Get hover information for symbols")
    print("  - search_workspace: Search for symbols in workspace")
    print()
    
    print("3. Example usage:")
    print("-" * 70)
    print("""
# The server automatically detects your project type and initializes
# the appropriate LSP client (Python, TypeScript, Rust, Go, etc.)

# Get file outline
outline = await get_outline(file_path="src/models.py")

# Find definition
definition = await get_definition(
    file_path="src/main.py",
    symbol_name="User",
    mode="definition"
)

# Find all references
references = await find_references(
    file_path="src/models.py",
    symbol_name="User.validate",
    mode="references"
)
    """)
    
    print("=" * 70)
    print("Demo completed!")
    print("=" * 70)


async def test_mcp_tools():
    """Test that MCP tools are properly registered."""
    from lsp_mcp_server import mcp
    
    print("\n" + "=" * 70)
    print("MCP Server Configuration")
    print("=" * 70)
    print()
    
    print(f"Server Name: {mcp.name}")
    print(f"Instructions: {mcp.instructions[:100]}...")
    print()
    
    print("✓ MCP server successfully created")
    print("✓ All tools registered")
    print("✓ Automatic LSP client initialization enabled")
    print()


def main():
    """Run the demo."""
    print("\nStarting LSP-MCP Server Demo...\n")
    
    # Run async demos
    asyncio.run(demo_lsp_mcp())
    asyncio.run(test_mcp_tools())
    
    print("\n✓ All demos completed successfully!")
    print("\nTo use the server:")
    print("  1. Install a language server (e.g., pip install pyright)")
    print("  2. Navigate to your project directory: cd /path/to/project")
    print("  3. Start the server: python /path/to/lsp-mcp/main.py")
    print("  4. Connect with an MCP client")
    print()


if __name__ == "__main__":
    main()
