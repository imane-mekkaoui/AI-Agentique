from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Any, Callable, Literal, TypedDict

Modalite = Literal["text", "table", "image"]

TERMES_IMAGES = {
    "image", "images", "photo", "photos", "illustration", "illustrations",
    "schema", "schemas", "dessin", "dessins", "figure", "figures", "visuel",
    "visuels", "montre", "montrer",
}
TERMES_TABLEAUX = {
    "table", "tableau", "tableaux", "valeur", "valeurs", "temperature",
    "pression", "dimension", "dimensions", "specification", "caracteristique",
    "maintenance", "entretien", "jour", "jours", "frequence", "periodicite",
    "controle", "controler", "graisser", "chaine", "chaines",
}
DISTANCE_MAX = 0.9


class EtatRAG(TypedDict, total=False):
    question: str
    modalites: list[Modalite]
    sources: list[dict[str, Any]]
    reponse: str


def normaliser_mots(texte: str) -> set[str]:
    sans_accents = unicodedata.normalize("NFKD", texte.casefold())
    ascii_texte = "".join(
        caractere for caractere in sans_accents
        if not unicodedata.combining(caractere)
    )
    return set(re.findall(r"[a-z0-9]+", ascii_texte))


def choisir_modalites(question: str) -> list[Modalite]:
    mots = normaliser_mots(question)
    modalites: list[Modalite] = ["text"]
    if mots & TERMES_TABLEAUX:
        modalites.append("table")
    if mots & TERMES_IMAGES:
        modalites.append("image")
    return modalites


def repondre_depuis_tableau_frequence(
    question: str,
    sources: list[dict[str, Any]],
) -> str | None:
    jours_match = re.search(r"\b(\d+)\s*jours?\b", question, re.IGNORECASE)
    if not jours_match:
        return None

    jours_demandes = int(jours_match.group(1))
    lignes_trouvees: list[tuple[str, int, str]] = []
    tableau_structure_trouve = False

    for numero, source in enumerate(sources, start=1):
        if source.get("metadata", {}).get("content_type") != "table":
            continue

        for operation, frequence in re.findall(
            r"Opération\s*:\s*(.*?)\s*\|\s*Fréquence\s*:\s*([^\n]+)",
            source.get("contenu", ""),
            flags=re.IGNORECASE,
        ):
            tableau_structure_trouve = True
            frequence_match = re.search(
                r"\b(\d+)\s*jours?\b", frequence, re.IGNORECASE
            )
            if frequence_match and int(frequence_match.group(1)) == jours_demandes:
                lignes_trouvees.append(
                    (
                        operation.strip(),
                        numero,
                        str(source["metadata"].get("page_number", "inconnue")),
                    )
                )

    if not tableau_structure_trouve:
        return None

    if not lignes_trouvees:
        return (
            "## Réponse\n"
            f"Le tableau de maintenance retrouvé ne liste aucune opération "
            f"à la fréquence de {jours_demandes} jours."
        )

    pages = ", ".join(dict.fromkeys(page for _, _, page in lignes_trouvees))
    puces = "\n".join(
        f"- {operation} [{numero}]"
        for operation, numero, _ in lignes_trouvees
    )
    return (
        "## Réponse\n"
        f"Selon le tableau de maintenance (page {pages}), les opérations à "
        f"effectuer tous les {jours_demandes} jours sont :\n\n"
        f"{puces}"
    )


class RAGRuntime:
    def __init__(
        self,
        collection_images: Any,
        collection_texte: Any,
        modele_embeddings: Any,
        processor_clip: Any,
        modele_clip: Any,
        torch_module: Any,
        functional_module: Any,
    ) -> None:
        self.collection_images = collection_images
        self.collection_texte = collection_texte
        self.modele_embeddings = modele_embeddings
        self.processor_clip = processor_clip
        self.modele_clip = modele_clip
        self.torch = torch_module
        self.functional = functional_module

    @classmethod
    def from_project(cls, project_root: Path | None = None) -> RAGRuntime:
        import chromadb
        import torch
        import torch.nn.functional as functional
        from langchain_huggingface import HuggingFaceEmbeddings
        from transformers import CLIPModel, CLIPProcessor

        racine = project_root or Path(__file__).resolve().parents[1]
        chemin_chroma = racine / "chroma_db"
        if not chemin_chroma.is_dir():
            raise FileNotFoundError(
                f"Index Chroma introuvable : {chemin_chroma}. "
                "Exécutez d'abord l'indexation de la partie 1."
            )

        client_chroma = chromadb.PersistentClient(path=str(chemin_chroma))
        collection_images = client_chroma.get_collection("manual_images_clip")
        collection_texte = client_chroma.get_collection("manual_text_tables")
        modele_embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={"local_files_only": True},
        )
        nom_modele_clip = "openai/clip-vit-base-patch32"
        processor_clip = CLIPProcessor.from_pretrained(
            nom_modele_clip, local_files_only=True
        )
        modele_clip = CLIPModel.from_pretrained(
            nom_modele_clip, local_files_only=True
        )
        modele_clip.eval()
        return cls(
            collection_images,
            collection_texte,
            modele_embeddings,
            processor_clip,
            modele_clip,
            torch,
            functional,
        )

    def rechercher(self, question: str, modalite: Modalite) -> list[dict[str, Any]]:
        if modalite == "image":
            entrees_texte = self.processor_clip(
                text=[question],
                return_tensors="pt",
                padding=True,
                truncation=True,
            )
            with self.torch.inference_mode():
                sortie = self.modele_clip.text_model(
                    input_ids=entrees_texte["input_ids"],
                    attention_mask=entrees_texte["attention_mask"],
                )
                vecteur = self.modele_clip.text_projection(sortie.pooler_output)
                vecteur = self.functional.normalize(
                    vecteur, p=2, dim=-1
                )[0].cpu().tolist()
            resultats = self.collection_images.query(
                query_embeddings=[vecteur],
                n_results=4,
                include=["documents", "metadatas", "distances"],
            )
        else:
            entrees_texte = self.processor_clip(
                text=[question],
                return_tensors="pt",
                padding=True,
                truncation=True,
            )
            with self.torch.inference_mode():
                sortie_texte = self.modele_clip.get_text_features(
                    input_ids=entrees_texte["input_ids"],
                    attention_mask=entrees_texte["attention_mask"],
                )
                vecteur_brut = (
                    sortie_texte.pooler_output
                    if hasattr(sortie_texte, "pooler_output")
                    else sortie_texte
                )
                vecteur_texte = self.functional.normalize(
                    vecteur_brut,
                    p=2,
                    dim=-1,
                )[0].cpu().tolist()
            filtres = (
                {"content_type": "table"}
                if modalite == "table"
                else {"content_type": {"$in": ["text", "image_caption"]}}
            )
            kwargs = {
                "query_embeddings": [vecteur_texte],
                "n_results": 4,
                "include": ["documents", "metadatas", "distances"],
            }
            try:
                resultats = self.collection_texte.query(where=filtres, **kwargs)
            except Exception:
                resultats = self.collection_texte.query(**kwargs)

        documents = (resultats.get("documents") or [[]])[0]
        metadonnees = (resultats.get("metadatas") or [[]])[0]
        distances = (resultats.get("distances") or [[]])[0]
        ids = (resultats.get("ids") or [[]])[0]
        sources = []
        for identifiant, document, metadata, distance in zip(
            ids, documents, metadonnees, distances
        ):
            contenu = document or ""
            if modalite == "image":
                contenu = (
                    metadata.get("description_qwen2vl")
                    or metadata.get("description_qwen25vl")
                    or metadata.get("description")
                    or contenu
                )
            sources.append(
                {
                    "id": identifiant,
                    "contenu": contenu,
                    "metadata": metadata,
                    "distance": float(distance),
                    "modalite_recherche": modalite,
                }
            )
        return sources

    def rechercher_sources(
        self,
        question: str,
        modalites: list[Modalite],
        fonction_recherche: Callable[
            [str, Modalite], list[dict[str, Any]]
        ] | None = None,
    ) -> list[dict[str, Any]]:
        recherche = fonction_recherche or self.rechercher
        deja_vus: set[tuple[Modalite, str]] = set()
        sources = []
        for modalite in modalites:
            for source in recherche(question, modalite):
                cle = (modalite, source["id"])
                if cle not in deja_vus:
                    sources.append(source)
                    deja_vus.add(cle)

        pertinentes = [
            source for source in sources
            if source["distance"] <= DISTANCE_MAX
        ]
        if pertinentes:
            return pertinentes

        for modalite in ("text", "table", "image"):
            if modalite in modalites:
                continue
            complement = recherche(question, modalite)
            pertinentes = [
                source for source in complement
                if source["distance"] <= DISTANCE_MAX
            ]
            if pertinentes:
                return pertinentes
        return []

    @staticmethod
    def formater_sources(
        sources: list[dict[str, Any]],
    ) -> tuple[str, list[dict[str, Any]]]:
        contexte = []
        citations = []
        for numero, source in enumerate(sources, start=1):
            metadata = source["metadata"]
            citation = {
                "numero": numero,
                "document": metadata.get("source", "Document inconnu"),
                "page": metadata.get("page_number", "inconnue"),
                "type": metadata.get("content_type", "inconnu"),
                "image_path": metadata.get("image_path"),
                "contenu": source["contenu"],
                "distance": source["distance"],
            }
            citations.append(citation)
            contexte.append(
                f"[{numero}] page {citation['page']} ({citation['type']}): "
                f"{source['contenu']}"
            )
        return "\n\n".join(contexte), citations

    def creer_retriever_tool(self) -> Any:
        from langchain_core.tools import StructuredTool

        def _run(query: str) -> str:
            sources = self.rechercher_sources(query, ["text", "image"])
            if not sources:
                return "Aucun passage pertinent dans l'index."
            lignes = []
            for n, source in enumerate(sources, start=1):
                meta = source["metadata"]
                lignes.append(
                    f"[{n}] p.{meta.get('page_number')} "
                    f"({meta.get('content_type')}) "
                    f"dist={source['distance']:.3f}\n{source['contenu']}"
                )
            return "\n\n".join(lignes)

        return StructuredTool.from_function(
            name="retriever_tool",
            description=(
                "Outil de recherche vectorielle multimodale (cosine / CLIP) "
                "dans le PDF indexé. Entrée : une question en texte. "
                "Sortie : extraits texte et légendes d'images avec page et distance. "
                "À appeler avant de répondre (ReAct : Reasoning → Action → Observation)."
            ),
            func=_run,
        )

    def creer_agent_react(self, llm: Any) -> Any:
        from langgraph.prebuilt import create_react_agent

        return create_react_agent(
            llm,
            tools=[self.creer_retriever_tool()],
            prompt=(
                "Tu es un agent RAG (MIND = LLM, BODY = retriever_tool). "
                "Pour toute question sur le document, appelle retriever_tool, "
                "observe les extraits, puis réponds uniquement à partir de cette "
                "observation. Cite les pages."
            ),
            name="rag_react",
        )

    def creer_agent_rag(
        self,
        llm: Any,
        fonction_recherche: Callable[
            [str, list[Modalite]], list[dict[str, Any]]
        ] | None = None,
        notifier_etape: Callable[[str], None] | None = None,
    ) -> Any:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langgraph.graph import END, START, StateGraph

        def planifier(etat: EtatRAG) -> dict[str, Any]:
            return {"modalites": choisir_modalites(etat["question"])}

        def recuperer(etat: EtatRAG) -> dict[str, Any]:
            if notifier_etape:
                notifier_etape("Recherche en cours dans le manuel…")
            sources = (
                fonction_recherche or self.rechercher_sources
            )(etat["question"], etat.get("modalites", ["text"]))
            if notifier_etape:
                if sources:
                    notifier_etape(
                        f"{len(sources)} source(s) trouvée(s). "
                        "Génération de la réponse avec Ollama…"
                    )
                else:
                    notifier_etape(
                        "Aucune source pertinente trouvée dans le manuel."
                    )
            return {"sources": sources}

        def repondre(etat: EtatRAG) -> dict[str, str]:
            sources = etat.get("sources", [])
            reponse_tableau = repondre_depuis_tableau_frequence(
                etat["question"], sources
            )
            if reponse_tableau is not None:
                return {"reponse": reponse_tableau}

            contexte, _ = self.formater_sources(sources)
            if not contexte:
                return {
                    "reponse": (
                        "Je n’ai pas trouvé de source suffisamment pertinente "
                        "dans le manuel."
                    )
                }
            resultat = llm.invoke(
                [
                    SystemMessage(
                        content=(
                            "Réponds en français et uniquement à partir des "
                            "sources fournies. Présente la réponse en Markdown "
                            "avec cette structure :\n"
                            "## Réponse\nDonne d'abord la réponse directe en "
                            "une ou deux phrases.\n\n"
                            "## Éléments du manuel\nPrésente les faits utiles "
                            "sous forme de puces. Ajoute une citation [n] à "
                            "chaque fait.\n\n"
                            "## Limites\nSignale ce que les sources ne "
                            "permettent pas de conclure. Si aucune limite "
                            "n'est à signaler, omets cette section.\n"
                            "N'invente aucun fait. Si les sources ne permettent "
                            "pas de répondre, dis-le clairement et ne déduis "
                            "pas une réponse incertaine. Pour les tableaux, "
                            "respecte strictement l'association entre chaque "
                            "opération et sa fréquence. N'attribue jamais une "
                            "fréquence à une opération si la source ne "
                            "l'associe pas explicitement. Si l'extraction "
                            "affiche des colonnes ou des marqueurs sans "
                            "association lisible, indique que la fréquence "
                            "ne peut pas être vérifiée au lieu de la deviner. "
                            "Chaque fait affirmé doit être directement "
                            "appuyé par la citation correspondante."
                        )
                    ),
                    HumanMessage(
                        content=(
                            f"Question : {etat['question']}\n\n"
                            f"Sources :\n{contexte}"
                        )
                    ),
                ]
            )
            if not isinstance(resultat.content, str) or not resultat.content.strip():
                raise RuntimeError("Ollama a renvoyé une réponse vide.")
            return {"reponse": resultat.content.strip()}

        graphe = StateGraph(EtatRAG)
        graphe.add_node("planifier", planifier)
        graphe.add_node("recuperer", recuperer)
        graphe.add_node("repondre", repondre)
        graphe.add_edge(START, "planifier")
        graphe.add_edge("planifier", "recuperer")
        graphe.add_edge("recuperer", "repondre")
        graphe.add_edge("repondre", END)
        return graphe.compile()


def creer_agent_rag_reel() -> Any:
    from langchain_ollama import ChatOllama

    runtime = RAGRuntime.from_project()
    llm = ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "qwen2.5:3b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        temperature=0,
    )
    return runtime.creer_agent_rag(llm)
