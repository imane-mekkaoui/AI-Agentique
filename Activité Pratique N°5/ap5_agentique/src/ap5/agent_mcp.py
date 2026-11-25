"""Agent LangChain qui consomme le serveur MCP démo (streamable-http)."""

from __future__ import annotations

import asyncio
import os

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from ap5.llm import modele_ollama


async def creer_agent_mcp():
    url = os.getenv("MCP_DEMO_URL", "http://127.0.0.1:8765/mcp")
    client = MultiServerMCPClient(
        {
            "demo": {
                "transport": "http",
                "url": url,
            }
        }
    )
    tools = await client.get_tools()
    return create_agent(
        modele_ollama(),
        tools,
        system_prompt=(
            "Tu es un agent qui utilise uniquement les tools MCP "
            "additionner et multiplier pour les calculs."
        ),
    )


async def poser_question(question: str) -> str:
    agent = await creer_agent_mcp()
    sortie = await agent.ainvoke({"messages": [("human", question)]})
    return sortie["messages"][-1].content


if __name__ == "__main__":
    print(asyncio.run(poser_question("Combien font 3 + 5, puis multiplie par 12 ?")))
