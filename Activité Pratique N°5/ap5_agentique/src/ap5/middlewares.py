from __future__ import annotations

from collections.abc import Callable

from langchain.agents.middleware import (
    HumanInTheLoopMiddleware,
    ModelRequest,
    ModelResponse,
    PIIMiddleware,
    ToolErrorMiddleware,
    dynamic_prompt,
    wrap_model_call,
)

from ap5.llm import modele_ollama


@dynamic_prompt
def prompt_dynamique(request: ModelRequest) -> str:
    n = len(request.state.get("messages") or [])
    if n > 6:
        return (
            "Tu es un assistant concis. La conversation est déjà longue : "
            "réponds en 4 phrases maximum."
        )
    return (
        "Tu es un assistant LangChain. Utilise tes tools quand c'est utile. "
        "Réponds en français."
    )


@wrap_model_call
def modele_dynamique(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """Petit modèle par défaut ; on peut forcer un second tag Ollama si besoin."""
    messages = request.state.get("messages") or []
    dernier = ""
    if messages:
        contenu = getattr(messages[-1], "content", "")
        dernier = contenu if isinstance(contenu, str) else str(contenu)
    if len(dernier) > 800:
        request = request.override(model=modele_ollama(temperature=0.2))
    return handler(request)


def erreur_outil(exc: Exception, request) -> str:
    nom = request.tool_call.get("name", "outil")
    return f"L'outil `{nom}` a échoué ({type(exc).__name__}). Reformule l'appel."


def liste_middlewares(*, hitl: bool = True) -> list:
    items = [
        prompt_dynamique,
        modele_dynamique,
        PIIMiddleware("email", strategy="redact", apply_to_input=True),
        ToolErrorMiddleware(erreur_outil),
    ]
    if hitl:
        items.append(
            HumanInTheLoopMiddleware(
                interrupt_on={
                    "Python_REPL": True,
                    "python_repl": True,
                }
            )
        )
    return items
