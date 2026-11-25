"""Serveur MCP GMAO de démo (streamable-http, port 8767)."""

from mcp.server.mcpserver import MCPServer

from maintidoc import mcp_service as gmao

mcp = MCPServer("maintidoc-gmao")


@mcp.tool()
def get_equipment_history(equipment_id: str) -> str:
    """Historique d'un équipement (GMAO lecture)."""
    return gmao.get_equipment_history(equipment_id)


@mcp.tool()
def get_open_tickets(equipment_id: str) -> str:
    """Tickets ouverts pour un équipement."""
    return gmao.get_open_tickets(equipment_id)


@mcp.tool()
def create_ticket(
    equipment_id: str,
    title: str,
    description: str,
    approval_token: str,
) -> str:
    """Crée un ticket. Exige un jeton d'approbation humaine lié au contenu."""
    return gmao.create_ticket(equipment_id, title, description, approval_token)


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8767,
        json_response=True,
    )
