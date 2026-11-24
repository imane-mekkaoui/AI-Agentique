import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000")
  .trim()
  .replace(/\/+$/, "");

type Source = {
  numero: number;
  document: string;
  page: string | number;
  type: string;
  contenu: string;
  distance: number;
  image_path?: string | null;
};

type ChatResponse = {
  answer: string;
  sources: Source[];
};

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  error?: boolean;
};

type ApiStatus = "checking" | "online" | "offline";

const suggestions = [
  "Quelle est la plage de température ambiante ?",
  "Quelles opérations faut-il effectuer tous les 30 jours ?",
  "Montre-moi les images du manuel.",
];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isChatResponse(value: unknown): value is ChatResponse {
  return (
    isRecord(value) &&
    typeof value.answer === "string" &&
    Array.isArray(value.sources) &&
    value.sources.every(
      (source) =>
        isRecord(source) &&
        typeof source.numero === "number" &&
        typeof source.document === "string" &&
        (typeof source.page === "string" || typeof source.page === "number") &&
        typeof source.type === "string" &&
        typeof source.contenu === "string" &&
        typeof source.distance === "number" &&
        (source.image_path === undefined ||
          source.image_path === null ||
          typeof source.image_path === "string"),
    )
  );
}

function errorMessage(error: unknown): string {
  if (error instanceof TypeError) {
    return "Impossible de joindre l’API. Vérifiez que le backend est démarré et que son URL et ses origines CORS sont configurées.";
  }
  return error instanceof Error ? error.message : "Une erreur inattendue est survenue.";
}

async function readApiError(response: Response): Promise<string> {
  const body: unknown = await response.json().catch(() => undefined);
  if (isRecord(body) && typeof body.detail === "string") {
    return body.detail;
  }
  if (isRecord(body) && Array.isArray(body.detail)) {
    const messages = body.detail
      .filter(
        (issue): issue is Record<string, unknown> & { msg: string } =>
          isRecord(issue) && typeof issue.msg === "string",
      )
      .map((issue) => issue.msg);
    if (messages.length) return messages.join(" ");
  }
  return `L’API a répondu avec le statut ${response.status}.`;
}

function imageUrl(imagePath: string | null | undefined): string | undefined {
  if (!imagePath?.trim()) return undefined;
  const path = imagePath.trim();
  if (/^https?:\/\//i.test(path)) {
    try {
      const url = new URL(path);
      return url.protocol === "http:" || url.protocol === "https:"
        ? url.href
        : undefined;
    } catch {
      return undefined;
    }
  }

  const filename = path.split(/[\\/]/).filter(Boolean).at(-1);
  if (!filename) return undefined;
  return `${API_URL}/api/images/${encodeURIComponent(filename)}`;
}

function typeLabel(type: string): string {
  const labels: Record<string, string> = {
    text: "Texte",
    table: "Tableau",
    image: "Image",
    image_caption: "Légende d’image",
  };
  return labels[type] ?? type.replaceAll("_", " ");
}

function structuredRows(content: string): string[][] | undefined {
  const rows = content
    .split(/\r?\n/)
    .map((line) =>
      line
        .split("|")
        .map((field) => field.trim())
        .filter(Boolean)
        .flatMap((field) => {
          const separator = field.indexOf(":");
          return separator > 0
            ? [field.slice(0, separator).trim(), field.slice(separator + 1).trim()]
            : ["Extrait", field];
        }),
    )
    .filter((row) => row.length > 1);
  return rows.length ? rows : undefined;
}

function SourceCard({ source }: { source: Source }) {
  const image = imageUrl(source.image_path);
  const [imageFailed, setImageFailed] = useState(false);
  const rows = source.type === "table" ? structuredRows(source.contenu) : undefined;

  return (
    <article className="source-card">
      <div className="source-heading">
        <span className="source-number">[{source.numero}]</span>
        <div className="source-title">
          <strong>{source.document}</strong>
          <span>
            Page {source.page} <span aria-hidden="true">·</span>{" "}
            {typeLabel(source.type)}
          </span>
        </div>
      </div>
      {rows ? (
        <div className="table-scroll">
          <table className="structured-table">
            <tbody>
              {rows.map((row, rowIndex) => (
                <tr key={`${source.numero}-${rowIndex}`}>
                  {row.map((cell, cellIndex) =>
                    cellIndex % 2 === 0 ? (
                      <th key={`${rowIndex}-${cellIndex}`} scope="row">
                        {cell}
                      </th>
                    ) : (
                      <td key={`${rowIndex}-${cellIndex}`}>{cell}</td>
                    ),
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="source-excerpt">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {source.contenu}
          </ReactMarkdown>
        </div>
      )}
      {image && !imageFailed && (
        <a
          className="source-image-link"
          href={image}
          target="_blank"
          rel="noreferrer"
        >
          <img
            className="source-image"
            src={image}
            alt={`Illustration du document ${source.document}, page ${source.page}`}
            loading="lazy"
            onError={() => setImageFailed(true)}
          />
          <span>Ouvrir l’image</span>
        </a>
      )}
    </article>
  );
}

function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [apiStatus, setApiStatus] = useState<ApiStatus>("checking");

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_URL}/health`, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`L’API a répondu avec le statut ${response.status}.`);
        }
        const health: unknown = await response.json();
        if (!isRecord(health) || health.ready !== true) {
          throw new Error("Le service RAG n’est pas encore prêt.");
        }
        setApiStatus("online");
      })
      .catch((error: unknown) => {
        if (!(error instanceof DOMException && error.name === "AbortError")) {
          setApiStatus("offline");
        }
      });
    return () => controller.abort();
  }, []);

  async function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const prompt = question.trim();
    if (!prompt || isSending) return;

    setQuestion("");
    setIsSending(true);
    setMessages((current) => [
      ...current,
      { id: crypto.randomUUID(), role: "user", content: prompt },
    ]);

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: prompt }),
      });
      if (!response.ok) {
        throw new Error(await readApiError(response));
      }

      const body: unknown = await response.json();
      if (!isChatResponse(body)) {
        throw new Error("La réponse reçue de l’API n’a pas le format attendu.");
      }
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: body.answer,
          sources: body.sources,
        },
      ]);
      setApiStatus("online");
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: errorMessage(error),
          error: true,
        },
      ]);
      setApiStatus("offline");
    } finally {
      setIsSending(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand" aria-label="Atelier, assistant manuel">
          <span className="brand-mark" aria-hidden="true">
            A
          </span>
          <span>ATELIER <small>ASSISTANT MANUEL</small></span>
        </div>
        <div className={`connection-status ${apiStatus}`} role="status">
          <span className="status-dot" aria-hidden="true" />
          {apiStatus === "checking"
            ? "Connexion…"
            : apiStatus === "online"
              ? "API connectée"
              : "API indisponible"}
        </div>
      </header>

      <section className="workspace">
        <aside className="intro-panel">
          <div className="eyebrow"><span /> BASE DE CONNAISSANCES</div>
          <h1>Le manuel,<br />à portée de question.</h1>
          <p>
            Interrogez votre documentation technique. Chaque réponse s’appuie
            sur les passages retrouvés dans le manuel.
          </p>
          <div className="intro-note">
            <span className="note-icon" aria-hidden="true">✳</span>
            <span><strong>Réponses sourcées</strong><br />Pages, extraits et visuels à l’appui.</span>
          </div>
          <div className="intro-footer">RAG MULTIMODAL <span>·</span> OLLAMA</div>
        </aside>

        <section className="chat-panel" aria-label="Assistant du manuel">
          <div className="chat-header">
            <div>
              <span className="chat-kicker">ESPACE DE CONSULTATION</span>
              <h2>Assistant technique</h2>
            </div>
            {messages.length > 0 && !isSending && (
              <button
                className="clear-button"
                type="button"
                onClick={() => setMessages([])}
              >
                Nouvelle discussion <span aria-hidden="true">↗</span>
              </button>
            )}
          </div>

          <div className="conversation" aria-live="polite">
            {messages.length === 0 ? (
              <div className="welcome">
                <div className="welcome-icon" aria-hidden="true">✳</div>
                <h3>Que souhaitez-vous savoir ?</h3>
                <p>Choisissez une question ou écrivez la vôtre.</p>
                <div className="suggestions">
                  {suggestions.map((suggestion, index) => (
                    <button
                      type="button"
                      key={suggestion}
                      className="suggestion"
                      onClick={() => setQuestion(suggestion)}
                    >
                      <span>0{index + 1}</span>{suggestion}<b aria-hidden="true">↗</b>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="message-list">
                {messages.map((message) => (
                  <article
                    className={`message ${message.role}${message.error ? " error" : ""}`}
                    key={message.id}
                  >
                    <div className="message-label">
                      {message.role === "user" ? "VOUS" : message.error ? "ERREUR" : "ASSISTANT"}
                    </div>
                    <div className="message-content">
                      {message.role === "assistant" && !message.error ? (
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {message.content}
                        </ReactMarkdown>
                      ) : (
                        <p>{message.content}</p>
                      )}
                    </div>
                    {message.sources && message.sources.length > 0 && (
                      <div className="sources">
                        <div className="sources-heading">
                          <span>SOURCES DU MANUEL</span>
                          <span>{message.sources.length} retrouvée{message.sources.length > 1 ? "s" : ""}</span>
                        </div>
                        {message.sources.map((source) => (
                          <SourceCard key={`${message.id}-${source.numero}`} source={source} />
                        ))}
                      </div>
                    )}
                    {message.role === "assistant" &&
                      !message.error &&
                      message.sources?.length === 0 && (
                        <div className="no-sources">
                          Aucune source pertinente retrouvée dans le manuel.
                        </div>
                      )}
                  </article>
                ))}
                {isSending && (
                  <div className="loading-message" role="status">
                    <span className="loader" aria-hidden="true" />
                    <span>
                      <strong>Recherche dans le manuel</strong>
                      <small>Analyse des sources et préparation de la réponse…</small>
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>

          <form className="composer" onSubmit={submitQuestion}>
            <label className="sr-only" htmlFor="question">
              Votre question sur le manuel
            </label>
            <textarea
              id="question"
              rows={2}
              maxLength={2000}
              placeholder="Ex. : Quelles sont les opérations de maintenance mensuelle ?"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  event.currentTarget.form?.requestSubmit();
                }
              }}
            />
            <div className="composer-footer">
              <span>Entrée pour envoyer <span aria-hidden="true">·</span> Maj + Entrée pour un retour à la ligne</span>
              <button
                className="send-button"
                type="submit"
                disabled={!question.trim() || isSending}
                aria-label="Envoyer la question"
              >
                {isSending ? "Recherche…" : "Envoyer"}
                <span aria-hidden="true">↗</span>
              </button>
            </div>
          </form>
          <p className="privacy-note">Les réponses sont générées à partir des documents indexés.</p>
        </section>
      </section>
    </main>
  );
}

export default App;
