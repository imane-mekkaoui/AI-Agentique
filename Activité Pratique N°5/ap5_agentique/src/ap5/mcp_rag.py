"""Serveur MCP SAV : outil distant rag_multimodal."""

from ap5.rag import rag_multimodal as rechercher
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ap5-rag", json_response=True)


@mcp.tool()
def rag_multimodal(question: str, image_ref: str = "") -> str:
    """Recherche des passages et figures dans les manuels du distributeur."""
    ref = image_ref.strip() or None
    return rechercher(question, image_ref=ref)


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8766)
