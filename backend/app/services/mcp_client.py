"""MCP Client — connects to local stdio-based MCP servers (govinfo + courtlistener)."""

from __future__ import annotations
import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.config import settings

logger = logging.getLogger(__name__)

# Path to wrapper script that suppresses dotenvx stdout pollution
_WRAPPER_SCRIPT = str(
    Path(__file__).resolve().parent.parent.parent / "scripts" / "mcp_wrapper.mjs"
)

# ──────────────────────────────────────────────────
#  Persistent MCP session pool
# ──────────────────────────────────────────────────
# Each local MCP server is spawned once and kept alive.
# A mapping of server_name → ClientSession is built on first use.

_sessions: dict[str, ClientSession] = {}
_exit_stack: AsyncExitStack | None = None
_initialized = False
_init_lock = asyncio.Lock()


def _build_server_configs() -> list[tuple[str, StdioServerParameters]]:
    """Build StdioServerParameters for each configured local MCP server."""
    servers: list[tuple[str, StdioServerParameters]] = []

    # Prepare environment to suppress dotenv/dotenvx logging which corrupts stdout JSONRPC
    env = os.environ.copy()
    env["DOTENV_QUIET"] = "true"
    env["DOTENVX_QUIET"] = "true"
    env["DOTENV_LOG_LEVEL"] = "error"
    # Pass API keys to child processes (courtlistener server.js reads from env)
    if settings.courtlistener_api_key:
        env["COURTLISTENER_API_KEY"] = settings.courtlistener_api_key

    if settings.mcp_govinfo_server_path:
        servers.append((
            "govinfo",
            StdioServerParameters(
                command="node",
                args=[_WRAPPER_SCRIPT, settings.mcp_govinfo_server_path],
                env=env,
            ),
        ))

    if settings.mcp_courtlistener_server_path:
        servers.append((
            "courtlistener",
            StdioServerParameters(
                command="node",
                args=[_WRAPPER_SCRIPT, settings.mcp_courtlistener_server_path],
                env=env,
            ),
        ))

    return servers


async def _ensure_sessions() -> None:
    """Lazily initialise all MCP stdio sessions on first call."""
    global _sessions, _exit_stack, _initialized

    if _initialized:
        return

    # Use a lock to prevent parallel tool calls from racing to initialize
    async with _init_lock:
        # Double-check after acquiring the lock
        if _initialized:
            return

        _exit_stack = AsyncExitStack()
        configs = _build_server_configs()

        for name, params in configs:
            try:
                logger.info(f"Starting MCP server: {name} ({params.command} {params.args})")

                # stdio_client returns a context manager yielding (read, write) streams
                transport = await _exit_stack.enter_async_context(stdio_client(params))
                read_stream, write_stream = transport

                session = await _exit_stack.enter_async_context(
                    ClientSession(read_stream, write_stream)
                )
                await session.initialize()

                # Log available tools
                tools = await session.list_tools()
                tool_names = [t.name for t in tools.tools]
                logger.info(f"MCP server '{name}' ready — tools: {tool_names}")

                _sessions[name] = session

            except Exception as e:
                logger.error(f"Failed to start MCP server '{name}': {e}")

        _initialized = True


# ──────────────────────────────────────────────────
#  Tool-name → server routing
# ──────────────────────────────────────────────────
#  govinfo tools:        search_documents, get_document_details, get_document_text, extract_bill_sections
#  courtlistener tools:  search_cases, get_case_details

_TOOL_SERVER_MAP: dict[str, str] = {
    # GovInfo
    "search_documents": "govinfo",
    "search_statutes": "govinfo",       # alias used by planner
    "get_document_details": "govinfo",
    "get_document_text": "govinfo",
    "extract_bill_sections": "govinfo",
    # CourtListener
    "search_cases": "courtlistener",
    "get_case_details": "courtlistener",
}


def _resolve_server(tool_name: str) -> str | None:
    """Return the server name that owns `tool_name`."""
    return _TOOL_SERVER_MAP.get(tool_name)


# ──────────────────────────────────────────────────
#  Public API
# ──────────────────────────────────────────────────

async def call_mcp_tool(tool_name: str, arguments: dict[str, Any]) -> list[dict]:
    """
    Call a tool on the appropriate local MCP server.

    The planner uses `search_statutes` as an alias — we map it
    to the govinfo server's `search_documents` tool automatically.
    """
    await _ensure_sessions()

    # Resolve alias: search_statutes → search_documents (with collection=BILLS)
    actual_tool = tool_name
    actual_args = dict(arguments)
    if tool_name == "search_statutes":
        actual_tool = "search_documents"
        # Convert the generic "query" arg to govinfo's "collection" param
        # and use the query as a keyword if the tool supports it
        actual_args.setdefault("collection", "BILLS")

    server_name = _resolve_server(tool_name)
    if not server_name:
        logger.warning(f"No MCP server mapped for tool: {tool_name}")
        return []

    session = _sessions.get(server_name)
    if not session:
        logger.warning(f"MCP server '{server_name}' is not running — skipping {tool_name}")
        return []

    try:
        logger.info(f"Calling MCP tool: {actual_tool} on '{server_name}' with {actual_args}")
        import asyncio
        result = await asyncio.wait_for(
            session.call_tool(actual_tool, actual_args),
            timeout=30.0,
        )

        # Parse the response content
        if result and result.content:
            parsed: list[dict] = []
            for item in result.content:
                if hasattr(item, "text"):
                    try:
                        data = json.loads(item.text)
                        if isinstance(data, list):
                            parsed.extend(data)
                        elif isinstance(data, dict):
                            # Flatten nested results arrays
                            if "results" in data:
                                parsed.extend(data["results"])
                            else:
                                parsed.append(data)
                    except json.JSONDecodeError:
                        parsed.append({"summary": item.text})
            return parsed

    except Exception as e:
        logger.error(f"MCP tool call failed ({actual_tool}@{server_name}): {e}")

    return []


async def list_mcp_tools() -> list[dict]:
    """List available tools from all connected MCP servers."""
    await _ensure_sessions()

    all_tools: list[dict] = []
    for name, session in _sessions.items():
        try:
            tools = await session.list_tools()
            for t in tools.tools:
                all_tools.append({
                    "name": t.name,
                    "description": t.description,
                    "server": name,
                })
        except Exception as e:
            logger.error(f"Failed to list tools from '{name}': {e}")

    return all_tools


async def shutdown_mcp() -> None:
    """Gracefully shut down all MCP server processes."""
    global _exit_stack, _sessions, _initialized

    if _exit_stack:
        logger.info("Shutting down MCP server sessions…")
        await _exit_stack.aclose()
        _exit_stack = None

    _sessions.clear()
    _initialized = False
