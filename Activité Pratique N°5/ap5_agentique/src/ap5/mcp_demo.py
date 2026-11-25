"""Serveur MCP démo : deux tools (additionner, multiplier), transport streamable-http."""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ap5-demo", json_response=True)


@mcp.tool()
def additionner(a: float, b: float) -> float:
    """Additionne deux nombres."""
    return a + b


@mcp.tool()
def multiplier(a: float, b: float) -> float:
    """Multiplie deux nombres."""
    return a * b


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8765)
