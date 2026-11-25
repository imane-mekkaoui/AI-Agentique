# Activité pratique N°5 — Agentique AI

LangChain, LangGraph, MCP (`streamable-http`), synthèse SAV d’un distributeur (schéma au tableau).

Le dossier `.venv` n’est pas versionné. Kernel Jupyter : **ap5_agentique**.

```powershell
cd tps/ap5_agentique
uv sync
copy .env.example .env
.\.venv\Scripts\python.exe -m ipykernel install --user --name ap5_agentique --display-name "ap5_agentique"
```

Ollama : `qwen2.5:3b` (comme les TPs RAG).

## A — LangChain

Notebook `notebooks/01_langchain.ipynb` :

1. Agent simple  
2. Mémoire (`InMemorySaver`, `thread_id`)  
3. Tools maison  
4. DuckDuckGo, Tavily, `PythonREPLTool`  
5. Middlewares : `dynamic_model`, `dynamic_prompt`, `tool_error_handling`, GuardRails (`PIIMiddleware`), Human in the loop  
6. Chatbot RAG agentique (`retriever_tool`)

Tavily : remplir `TAVILY_API_KEY` dans `.env` (sinon la cellule Tavily l’indique).

## B — LangGraph

- Bases : `notebooks/02_langgraph_bases.ipynb` et graphe `bases`  
- RAG agentique : `src/ap5/agentic_rag.py`  
- Studio : `uv run langgraph dev` (fichier `langgraph.json`)  
- Interface : `uv run streamlit run streamlit_app.py`

## C — MCP

Deux tools démo : `additionner`, `multiplier`.

```powershell
uv run python -m ap5.mcp_demo
npx @modelcontextprotocol/inspector http://127.0.0.1:8765/mcp
uv run python -m ap5.agent_mcp
```

Agent N8N : importer `n8n/mcp_streamable_http.json`. Transport **HTTP Streamable**, URL `http://host.docker.internal:8765/mcp`.

## D — Synthèse SAV

Orchestrateur LangGraph → un seul agent spécialisé → retour orchestrateur → END.

| Exemple | Catégorie | Agent |
|---|---|---|
| Voyant + photo `img_px200_01` | documentation | agent_documentaire |
| Série `PX200-0042` | garantie | agent_garantie |

- Outil distant `rag_multimodal` : `uv run python -m ap5.mcp_rag` (port 8766)  
- Outil local `consulter_garantie` : `data/registre_garantie.json` (lecture seule)

```powershell
uv run python tests/test_synthese.py
```
