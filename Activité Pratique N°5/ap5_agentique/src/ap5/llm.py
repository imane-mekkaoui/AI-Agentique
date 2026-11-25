from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def modele_ollama(temperature: float = 0):
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "qwen2.5:3b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        temperature=temperature,
    )
