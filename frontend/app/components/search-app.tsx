"use client";

import { FormEvent, useState } from "react";

type Result = { chunk_id: string; document_id: string; url: string; title: string; snippet: string; score: number };
type Citation = { index: number; chunk_id: string; document_id: string; title: string; url: string; quote: string };
type SearchResponse = { query: string; results: Result[]; took_ms: number };
type AnswerResponse = { query: string; answer: string; citations: Citation[]; grounded: boolean; provider: string };
type Stats = { documents: number; chunks: number; searches: number };

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SAMPLE_DOCUMENTS = [
  { url: "https://docs.seekora.local/hybrid-retrieval", title: "How Seekora ranks evidence", content: "Seekora combines PostgreSQL full-text search with vector similarity. Reciprocal rank fusion merges lexical and semantic candidates. A deterministic reranker rewards passages that cover the query terms before grounded answer generation." },
  { url: "https://docs.seekora.local/crawl-safety", title: "Responsible crawling controls", content: "The crawler honors robots.txt, rejects private network addresses, limits response size, validates redirects, accepts HTML only, and delays requests per origin. Canonical URLs and content hashes prevent duplicate documents." },
  { url: "https://docs.seekora.local/citations", title: "Traceable citations in RAG", content: "Seekora answers from retrieved passages and attaches numbered citations to immutable chunk identifiers. Retrieved documents are treated as untrusted evidence, so instructions embedded in a page are never followed by the answer generator." },
];

function hostname(url: string) { try { return new URL(url).hostname; } catch { return url; } }
async function parseError(response: Response) { try { const payload = await response.json(); return typeof payload.detail === "string" ? payload.detail : "Request failed"; } catch { return "Request failed"; } }

export function SearchApp() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<"answer" | "search">("answer");
  const [searchData, setSearchData] = useState<SearchResponse | null>(null);
  const [answerData, setAnswerData] = useState<AnswerResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [adminOpen, setAdminOpen] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [adminMessage, setAdminMessage] = useState("");
  const [stats, setStats] = useState<Stats | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault(); const trimmed = query.trim(); if (trimmed.length < 2) return;
    setLoading(true); setError(""); setSearchData(null); setAnswerData(null);
    try {
      if (mode === "answer") {
        const response = await fetch(`${API_URL}/v1/answer`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query: trimmed }) });
        if (!response.ok) throw new Error(await parseError(response));
        setAnswerData((await response.json()) as AnswerResponse);
      } else {
        const response = await fetch(`${API_URL}/v1/search?q=${encodeURIComponent(trimmed)}`);
        if (!response.ok) throw new Error(await parseError(response));
        setSearchData((await response.json()) as SearchResponse);
      }
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Search failed."); }
    finally { setLoading(false); }
  }

  async function refreshStats(key = apiKey) {
    const response = await fetch(`${API_URL}/v1/admin/stats`, { headers: { Authorization: `Bearer ${key}` } });
    if (!response.ok) throw new Error(await parseError(response));
    setStats((await response.json()) as Stats);
  }

  async function ingestSamples() {
    if (!apiKey) { setAdminMessage("Enter the administrator API key first."); return; }
    setAdminMessage("Indexing demo corpus…");
    try {
      for (const document of SAMPLE_DOCUMENTS) {
        const response = await fetch(`${API_URL}/v1/documents/text`, { method: "POST", headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" }, body: JSON.stringify(document) });
        if (!response.ok && response.status !== 422) throw new Error(await parseError(response));
      }
      await refreshStats(); setAdminMessage("Demo corpus is indexed and ready to query.");
    } catch (cause) { setAdminMessage(cause instanceof Error ? cause.message : "Ingestion failed."); }
  }

  const hasResults = Boolean(searchData || answerData || error);
  return (
    <>
      <section className={`hero ${hasResults ? "heroCompact" : ""}`} id="top">
        <img className="bannerGlyph" src="/seekora-banner.svg" alt="" />
        <div className="heroCopy"><div className="eyebrow"><span>01</span> SOURCE-GROUNDED DISCOVERY</div><h1>Search beyond<br /><em>the obvious.</em></h1><p>Hybrid retrieval and grounded answers across the sources you control.</p></div>
        <div className="queryPanel">
          <div className="modeSwitch" role="group" aria-label="Search mode"><button className={mode === "answer" ? "active" : ""} onClick={() => setMode("answer")}>ASK SEEKORA</button><button className={mode === "search" ? "active" : ""} onClick={() => setMode("search")}>SEARCH SOURCES</button></div>
          <form onSubmit={submit} role="search"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m21 21-4.3-4.3m2.3-5.7a8 8 0 1 1-16 0 8 8 0 0 1 16 0Z" /></svg><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ask a question about your indexed sources" aria-label="Search query" /><button disabled={loading || query.trim().length < 2}>{loading ? "THINKING" : mode === "answer" ? "ASK" : "SEARCH"}<span>↗</span></button></form>
          <div className="queryFooter"><span><i /> citations enforced</span><button onClick={() => setAdminOpen(true)}>ADMIN CONSOLE</button></div>
        </div>
      </section>
      <section className="output" aria-live="polite">
        {error ? <div className="errorPanel"><b>REQUEST INTERRUPTED</b><span>{error}</span></div> : null}
        {answerData ? <div className="answerLayout"><article className="answerCard"><div className="answerLabel"><span>SEEKORA SYNTHESIS</span><i className={answerData.grounded ? "verified" : ""}>{answerData.grounded ? "GROUNDED" : "INSUFFICIENT EVIDENCE"}</i></div><h2>{answerData.query}</h2><p className="answerText">{answerData.answer}</p><footer><span>{answerData.provider}</span><span>{answerData.citations.length} traceable sources</span></footer></article><aside className="citationRail" aria-label="Citations"><div className="railTitle">SOURCE TRAIL <span>{String(answerData.citations.length).padStart(2, "0")}</span></div>{answerData.citations.map((citation) => <a href={citation.url} target="_blank" rel="noreferrer" key={citation.chunk_id}><span className="citationNumber">[{citation.index}]</span><div><b>{citation.title}</b><small>{hostname(citation.url)}</small><p>{citation.quote}</p></div></a>)}</aside></div> : null}
        {searchData ? <div className="searchResults"><div className="resultHeader"><span>{searchData.results.length} EVIDENCE MATCHES</span><span>{searchData.took_ms.toFixed(0)} MS · HYBRID RANKED</span></div><ol>{searchData.results.map((result, index) => <li key={result.chunk_id}><span>{String(index + 1).padStart(2, "0")}</span><article><small>{hostname(result.url)}</small><a href={result.url} target="_blank" rel="noreferrer"><h2>{result.title}</h2></a><p>{result.snippet}</p><footer>RRF {result.score.toFixed(4)} · SOURCE ↗</footer></article></li>)}</ol></div> : null}
      </section>
      <div className={`adminBackdrop ${adminOpen ? "open" : ""}`} onClick={() => setAdminOpen(false)} />
      <aside className={`adminDrawer ${adminOpen ? "open" : ""}`} aria-hidden={!adminOpen}><header><div><small>CONTROL PLANE</small><h2>Corpus console</h2></div><button onClick={() => setAdminOpen(false)} aria-label="Close admin console">×</button></header><p>Authenticate locally to ingest the deterministic demo corpus and inspect index activity.</p><label>ADMINISTRATOR API KEY<input type="password" value={apiKey} onChange={(event) => setApiKey(event.target.value)} placeholder="SEEKORA_ADMIN_API_KEY" /></label><button className="primaryAction" onClick={ingestSamples}>INGEST DEMO CORPUS <span>↗</span></button><button className="secondaryAction" onClick={() => refreshStats().catch((cause) => setAdminMessage(cause.message))}>REFRESH INDEX STATS</button>{adminMessage ? <div className="adminMessage">{adminMessage}</div> : null}{stats ? <div className="stats"><div><b>{stats.documents}</b><span>DOCUMENTS</span></div><div><b>{stats.chunks}</b><span>CHUNKS</span></div><div><b>{stats.searches}</b><span>QUERIES</span></div></div> : null}<footer>Keys remain in this browser tab only and are sent exclusively in authorization headers.</footer></aside>
    </>
  );
}
