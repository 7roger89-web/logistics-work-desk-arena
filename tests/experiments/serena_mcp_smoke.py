"""MCP client acceptance for Serena semantic navigation over copied LOGI code.

No repository writes, no credentials, no app database, no production.
"""
import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def text_of(result):
    return "\n".join(str(x.text) for x in result.content if hasattr(x, "text"))


async def probe(binary: str, project: str):
    params = StdioServerParameters(
        command=binary,
        args=[
            "start-mcp-server",
            "--project", project,
            "--context", "codex",
            "--mode", "no-memories",
            "--agent-interface", "tools",
            "--transport", "stdio",
            "--enable-web-dashboard", "false",
            "--open-web-dashboard", "false",
            "--log-level", "ERROR",
        ],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            names = {x.name for x in (await session.list_tools()).tools}
            needed = {"find_symbol", "get_symbols_overview", "find_referencing_symbols"}
            if not needed.issubset(names):
                raise AssertionError(f"missing Serena MCP tools {sorted(needed - names)}")
            overview = await session.call_tool(
                "get_symbols_overview", {"relative_path": "core/journey_notes.py"}
            )
            overview_text = text_of(overview)
            if overview.isError or "read_note_attachment" not in overview_text:
                raise AssertionError("Serena cannot outline real note/backend code: " + overview_text[:600])
            found = await session.call_tool(
                "find_symbol", {
                    "name_path_pattern": "read_note_attachment",
                    "relative_path": "core/journey_notes.py",
                    "include_body": False,
                }
            )
            found_text = text_of(found)
            if found.isError or "read_note_attachment" not in found_text:
                raise AssertionError("Serena cannot resolve exact backend function: " + found_text[:600])
            references = await session.call_tool(
                "find_referencing_symbols",
                {"name_path": "read_note_attachment", "relative_path": "core/journey_notes.py"},
            )
            references_text = text_of(references)
            if references.isError:
                raise AssertionError("Serena reference lookup failed: " + references_text[:600])
            if "journey_inline" not in references_text and "_handle_download" not in references_text:
                raise AssertionError("Serena did not link file download caller: " + references_text[:1200])
            print("SERENA_MCP=PASS")
            print("SERENA_TOOLS=" + ",".join(sorted(needed)))
            print("SERENA_FUNCTION=core/journey_notes.py::read_note_attachment")
            print("SERENA_REFERENCES=" + references_text[:1600].replace("\n", " "))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python serena_mcp_smoke.py /abs/serena /abs/safe-code-copy")
    asyncio.run(asyncio.wait_for(probe(sys.argv[1], sys.argv[2]), timeout=150))
