"""Client MCP : streamable-http, repli sur le service local."""

from __future__ import annotations

import asyncio
import logging

from maintidoc import mcp_service as gmao
from maintidoc.config import get_settings

logger = logging.getLogger("maintidoc.mcp")


async def _via_http(nom: str, arguments: dict) -> str:
    from mcp.client.session import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    url = get_settings().mcp_url
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(nom, arguments)
            parts = []
            for block in result.content:
                text = getattr(block, "text", None)
                if text:
                    parts.append(text)
            return "\n".join(parts) or str(result)


def appeler(nom: str, **arguments: str) -> str:
    """Appelle un tool MCP ; si le serveur est down, même logique en local."""
    try:
        return asyncio.run(_via_http(nom, arguments))
    except Exception as exc:
        logger.info("mcp_http_repli local err=%s", exc)
        return getattr(gmao, nom)(**arguments)


if __name__ == "__main__":
    print(appeler("get_equipment_history", equipment_id="VLT-FC302-01"))
