"""
LSP-MCP Server: Model Context Protocol server for Language Server Protocol integration.

This server exposes LSAP (Language Server Agent Protocol) capabilities as MCP tools,
allowing AI agents to interact with language servers for code navigation and analysis.
"""

import asyncio
import json
from pathlib import Path
from typing import Any

from lsp_client import (
    Client,
    PyrightClient,
    TypescriptClient,
    RustAnalyzerClient,
    GoplsClient,
)
from lsp_client.server import LocalServer
from lsp_client.utils.workspace import Workspace, WorkspaceFolder
from lsprotocol.types import LanguageKind
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
from lsap.schema.locate import Locate, LocateRequest
from lsap.schema.outline import OutlineRequest
from lsap.schema.reference import ReferenceRequest
from lsap.schema.search import SearchRequest

# Create MCP server
mcp = FastMCP(
    "lsp-mcp",
    instructions="""
    LSP-MCP Server provides high-level Language Server Protocol capabilities for AI agents.
    It transforms low-level LSP operations into agent-friendly cognitive tools.
    
    Before using any tools, you must initialize an LSP client using the init_lsp_client tool
    with the workspace root directory and language server command.
    """,
)

# Global LSP client instance and context manager
_lsp_client: Client | None = None
_lsp_client_cm = None  # Store the context manager for proper cleanup

# Language to client class mapping
LANGUAGE_CLIENT_MAP = {
    "python": PyrightClient,
    "typescript": TypescriptClient,
    "javascript": TypescriptClient,
    "rust": RustAnalyzerClient,
    "go": GoplsClient,
}


def get_client() -> Client:
    """Get the LSP client instance."""
    if _lsp_client is None:
        raise ValueError(
            "LSP client not initialized. Call init_lsp_client first."
        )
    return _lsp_client


@mcp.tool()
async def init_lsp_client(
    workspace_root: str,
    language: str,
    server_command: str | None = None,
    server_args: list[str] | None = None,
) -> str:
    """
    Initialize the LSP client for a workspace.
    
    Args:
        workspace_root: Path to the workspace root directory
        language: Language kind (e.g., "python", "typescript", "rust", "go")
        server_command: Optional language server executable command. If not provided, uses default for language.
        server_args: Optional arguments for the language server
    
    Returns:
        Status message indicating whether initialization was successful
    
    Example:
        # Using default language server
        init_lsp_client(
            workspace_root="/path/to/project",
            language="python"
        )
        
        # Using custom server command
        init_lsp_client(
            workspace_root="/path/to/project",
            language="python",
            server_command="pylsp",
            server_args=[]
        )
    """
    global _lsp_client, _lsp_client_cm
    
    try:
        workspace_path = Path(workspace_root).resolve()
        if not workspace_path.exists():
            return f"Error: Workspace path does not exist: {workspace_root}"
        
        # Create workspace
        workspace = Workspace({
            "main": WorkspaceFolder(
                uri=workspace_path.as_uri(),
                name="main",
            )
        })
        
        # Select client based on language
        lang_lower = language.lower()
        
        if server_command:
            # Use custom server command
            server = LocalServer(
                program=server_command,
                args=server_args or [],
            )
            
            # Map to appropriate client class based on language
            client_class = LANGUAGE_CLIENT_MAP.get(lang_lower)
            if client_class is None:
                return f"Error: Unsupported language: {language}. Supported: {list(LANGUAGE_CLIENT_MAP.keys())}"
            
            client = client_class(
                server=server,
                workspace=workspace,
            )
        else:
            # Use default client for language
            client_class = LANGUAGE_CLIENT_MAP.get(lang_lower)
            if client_class is None:
                return f"Error: Unsupported language: {language}. Supported: {list(LANGUAGE_CLIENT_MAP.keys())}"
            
            client = client_class(workspace=workspace)
        
        # Start the client using async context manager
        _lsp_client_cm = client
        _lsp_client = await _lsp_client_cm.__aenter__()
        
        return f"LSP client initialized successfully for {language} at {workspace_root}"
    
    except Exception as e:
        return f"Error initializing LSP client: {str(e)}"


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
    try:
        client = get_client()
        
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
        
        capability = DefinitionCapability(client=client)
        response = await capability(request)
        
        if response is None:
            return "No definition found."
        
        # Format response as markdown
        result = f"# {mode.replace('_', ' ').title()} Result\n\n"
        
        if not response.items:
            result += f"No {mode.replace('_', ' ')} found."
        else:
            for item in response.items:
                result += f"## `{item.file_path}`: {'.'.join(item.path)} (`{item.kind}`)\n\n"
                if item.code and include_code:
                    suffix = item.file_path.suffix.lstrip(".")
                    result += f"### Content\n```{suffix}\n{item.code}\n```\n\n"
        
        return result
    
    except Exception as e:
        return f"Error getting definition: {str(e)}"


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
    try:
        client = get_client()
        
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
        
        capability = ReferenceCapability(client=client)
        response = await capability(request)
        
        if response is None:
            return "No references found."
        
        # Format response as markdown
        result = f"# {mode.title()} Found\n\n"
        result += f"Total {mode}: {response.total} | Showing: {len(response.items)}\n\n"
        
        for item in response.items:
            loc = item.location
            result += f"### {loc.file_path}:{loc.range.start.line}\n\n"
            
            if item.scope_info:
                scope = item.scope_info
                result += f"In `{'.'.join(scope.path)}` (`{scope.kind}`)\n\n"
            
            if item.code:
                suffix = loc.file_path.suffix.lstrip(".")
                result += f"```{suffix}\n{item.code}\n```\n\n"
        
        return result
    
    except Exception as e:
        return f"Error finding references: {str(e)}"


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
    try:
        client = get_client()
        
        request = OutlineRequest(file_path=Path(file_path))
        capability = OutlineCapability(client=client)
        response = await capability(request)
        
        if response is None:
            return "No outline available."
        
        # Format response as markdown
        result = f"# Outline for `{response.file_path}`\n\n"
        
        # Group items by hierarchy
        for item in response.items:
            indent = "  " * (len(item.path) - 1)
            symbol_path = ".".join(item.path)
            result += f"{indent}## {symbol_path} (`{item.kind}`)\n\n"
            
            if item.signature:
                suffix = response.file_path.suffix.lstrip(".")
                result += f"{indent}```{suffix}\n{item.signature}\n```\n\n"
            
            if item.hover:
                result += f"{indent}---\n\n{indent}{item.hover}\n\n"
        
        return result
    
    except Exception as e:
        return f"Error getting outline: {str(e)}"


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
    try:
        client = get_client()
        
        # Build locate request
        locate = Locate(file_path=Path(file_path))
        if line is not None:
            locate.line = line
        if character is not None:
            locate.character = character
        if symbol_name:
            locate.find = symbol_name
        
        request = HoverRequest(locate=locate)
        capability = HoverCapability(client=client)
        response = await capability(request)
        
        if response is None or not response.hover:
            return "No hover information available."
        
        result = f"# Hover Information\n\n"
        result += f"**File**: `{response.file_path}`\n"
        result += f"**Position**: Line {response.position.line}, Character {response.position.character}\n\n"
        result += "---\n\n"
        result += response.hover
        
        return result
    
    except Exception as e:
        return f"Error getting hover info: {str(e)}"


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
    try:
        client = get_client()
        
        request = SearchRequest(
            query=query,
            max_items=max_items,
        )
        
        capability = SearchCapability(client=client)
        response = await capability(request)
        
        if response is None:
            return "No results found."
        
        # Format response as markdown
        result = f"# Search Results for '{query}'\n\n"
        result += f"Total results: {response.total} | Showing: {len(response.items)}\n\n"
        
        for item in response.items:
            result += f"### `{item.file_path}`: {'.'.join(item.path)} (`{item.kind}`)\n\n"
            
            if item.signature:
                suffix = item.file_path.suffix.lstrip(".")
                result += f"```{suffix}\n{item.signature}\n```\n\n"
            
            if item.hover:
                result += f"{item.hover}\n\n"
            
            result += "---\n\n"
        
        return result
    
    except Exception as e:
        return f"Error searching workspace: {str(e)}"


@mcp.tool()
async def shutdown_lsp_client() -> str:
    """
    Shutdown the LSP client and clean up resources.
    
    Returns:
        Status message
    """
    global _lsp_client, _lsp_client_cm
    
    try:
        if _lsp_client is not None and _lsp_client_cm is not None:
            # Use async context manager exit for proper cleanup
            await _lsp_client_cm.__aexit__(None, None, None)
            _lsp_client = None
            _lsp_client_cm = None
            return "LSP client shut down successfully."
        return "No LSP client was running."
    except Exception as e:
        return f"Error shutting down LSP client: {str(e)}"


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
