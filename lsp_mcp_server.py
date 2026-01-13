"""
LSP-MCP Server: Model Context Protocol server for Language Server Protocol integration.

This server exposes LSAP (Language Server Agent Protocol) capabilities as MCP tools,
allowing AI agents to interact with language servers for code navigation and analysis.
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import NamedTuple

from lsp_client import Client
from lsp_client.clients.lang import lang_clients
from mcp.server.fastmcp import FastMCP

from lsap.capability import (
    DefinitionCapability,
    HoverCapability,
    OutlineCapability,
    ReferenceCapability,
    SearchCapability,
)
from lsap.schema.definition import DefinitionRequest
from lsap.schema.hover import HoverRequest
from lsap.schema.locate import Locate
from lsap.schema.outline import OutlineRequest
from lsap.schema.reference import ReferenceRequest
from lsap.schema.search import SearchRequest


class TargetClient(NamedTuple):
    """Represents a target client for a specific project."""
    project_path: Path
    client_cls: type[Client]


# Module-level client instance, managed by lifespan
_client: Client | None = None


def find_client(path: Path) -> TargetClient | None:
    """
    Find an appropriate LSP client for the given path.
    
    This function searches for a suitable language client based on the project
    structure, similar to lsp-cli's approach.
    """
    candidates = lang_clients.values()

    for client_cls in candidates:
        lang_config = client_cls.get_language_config()
        if root := lang_config.find_project_root(path):
            return TargetClient(project_path=root, client_cls=client_cls)
    return None


@asynccontextmanager
async def lifespan(app: FastMCP):
    """
    Lifespan context manager for the MCP server.
    
    Initializes the LSP client on startup and cleans up on shutdown.
    """
    global _client
    
    # Get current working directory
    cwd = Path(os.getcwd()).resolve()
    
    # Find appropriate client
    target = find_client(cwd)
    if not target:
        print(f"Warning: No LSP client found for directory: {cwd}")
        yield
        return
    
    print(f"Found {target.client_cls.get_language_config().kind.value} project at {target.project_path}")
    
    # Initialize client with project path directly
    async with target.client_cls(workspace=target.project_path) as client:
        _client = client
        yield
        _client = None
    
    print("LSP client shut down")


# Create MCP server with lifespan management
mcp = FastMCP(
    "lsp-mcp",
    instructions="""
    LSP-MCP Server provides high-level Language Server Protocol capabilities for AI agents.
    It transforms low-level LSP operations into agent-friendly cognitive tools.
    
    The LSP client is automatically initialized based on the current working directory.
    """,
    lifespan=lifespan,
)


@mcp.tool()
async def get_definition(
    file_path: str,
    symbol_name: str | None = None,
    line: int | None = None,
    character: int | None = None,
    mode: str = "definition",
    include_code: bool = True,
) -> str:
    """
    Find the definition, declaration, or type definition of a symbol.
    
    Args:
        file_path: Path to the file containing the symbol
        symbol_name: Name of the symbol to find (optional if line/character provided)
        line: Line number of the symbol (0-indexed, optional)
        character: Character position in the line (0-indexed, optional)
        mode: Type of navigation - "definition", "declaration", or "type_definition"
        include_code: Whether to include code snippets in the result
    
    Returns:
        Markdown-formatted result with definition information
    
    Example:
        get_definition(
            file_path="src/main.py",
            symbol_name="User.validate",
            mode="definition",
            include_code=True
        )
    """
    if _client is None:
        return "Error: LSP client not initialized"
    
    # Build locate request
    locate = Locate(file_path=Path(file_path))
    if line is not None:
        locate.line = line
    if character is not None:
        locate.character = character
    if symbol_name:
        locate.find = symbol_name
    
    request = DefinitionRequest(
        locate=locate,
        mode=mode,  # type: ignore
        include_code=include_code,
    )
    
    capability = DefinitionCapability(client=_client)
    response = await capability(request)
    
    if response is None:
        return "No definition found."
    
    return response.format()


@mcp.tool()
async def find_references(
    file_path: str,
    symbol_name: str | None = None,
    line: int | None = None,
    character: int | None = None,
    mode: str = "references",
    max_items: int = 50,
    context_lines: int = 3,
) -> str:
    """
    Find all references or implementations of a symbol.
    
    Args:
        file_path: Path to the file containing the symbol
        symbol_name: Name of the symbol to find references for
        line: Line number of the symbol (0-indexed, optional)
        character: Character position in the line (0-indexed, optional)
        mode: "references" or "implementations"
        max_items: Maximum number of references to return
        context_lines: Number of context lines to show around each reference
    
    Returns:
        Markdown-formatted result with reference information
    
    Example:
        find_references(
            file_path="src/models.py",
            symbol_name="User.validate",
            mode="references",
            max_items=20
        )
    """
    if _client is None:
        return "Error: LSP client not initialized"
    
    # Build locate request
    locate = Locate(file_path=Path(file_path))
    if line is not None:
        locate.line = line
    if character is not None:
        locate.character = character
    if symbol_name:
        locate.find = symbol_name
    
    request = ReferenceRequest(
        locate=locate,
        mode=mode,  # type: ignore
        max_items=max_items,
        context_lines=context_lines,
    )
    
    capability = ReferenceCapability(client=_client)
    response = await capability(request)
    
    if response is None:
        return "No references found."
    
    return response.format()


@mcp.tool()
async def get_outline(
    file_path: str,
) -> str:
    """
    Get the structural outline of a file showing all symbols.
    
    Args:
        file_path: Path to the file to analyze
    
    Returns:
        Markdown-formatted outline with all symbols in the file
    
    Example:
        get_outline(file_path="src/models.py")
    """
    if _client is None:
        return "Error: LSP client not initialized"
    
    request = OutlineRequest(file_path=Path(file_path))
    capability = OutlineCapability(client=_client)
    response = await capability(request)
    
    if response is None:
        return "No outline available."
    
    return response.format()


@mcp.tool()
async def get_hover_info(
    file_path: str,
    symbol_name: str | None = None,
    line: int | None = None,
    character: int | None = None,
) -> str:
    """
    Get hover information for a symbol at a specific location.
    
    Args:
        file_path: Path to the file
        symbol_name: Name of the symbol (optional if line/character provided)
        line: Line number (0-indexed, optional)
        character: Character position (0-indexed, optional)
    
    Returns:
        Markdown-formatted hover information
    
    Example:
        get_hover_info(
            file_path="src/main.py",
            symbol_name="process_data"
        )
    """
    if _client is None:
        return "Error: LSP client not initialized"
    
    # Build locate request
    locate = Locate(file_path=Path(file_path))
    if line is not None:
        locate.line = line
    if character is not None:
        locate.character = character
    if symbol_name:
        locate.find = symbol_name
    
    request = HoverRequest(locate=locate)
    capability = HoverCapability(client=_client)
    response = await capability(request)
    
    if response is None or not response.hover:
        return "No hover information available."
    
    return response.format()


@mcp.tool()
async def search_workspace(
    query: str,
    file_pattern: str | None = None,
    max_items: int = 50,
) -> str:
    """
    Search for symbols across the entire workspace.
    
    Args:
        query: Search query string
        file_pattern: Optional file pattern to filter results (e.g., "*.py")
        max_items: Maximum number of results to return
    
    Returns:
        Markdown-formatted search results
    
    Example:
        search_workspace(
            query="User",
            file_pattern="*.py",
            max_items=20
        )
    """
    if _client is None:
        return "Error: LSP client not initialized"
    
    request = SearchRequest(
        query=query,
        max_items=max_items,
    )
    
    capability = SearchCapability(client=_client)
    response = await capability(request)
    
    if response is None:
        return "No results found."
    
    return response.format()


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
