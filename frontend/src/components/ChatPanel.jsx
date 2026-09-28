import React, { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { chunkLabel } from "../utils";

const SUGGESTIONS = [
  "Who has the most experience with Oracle databases?",
  "Find candidates who know Salesforce and are based in Bengaluru.",
  "Compare the DBA candidates - who's the strongest fit for a MongoDB-heavy role?",
];

// Splits "Jane has 8 years [1]. Bob also matches [1][3]." into plain text and
// hoverable citation chips, each linked back to its numbered source so the
// underlying candidate/snippet shows up in a tooltip without leaving the chat.
function AnswerText({ text, sources }) {
  const parts = text.split(/(\[\d+\])/g);
  return (
    <>
      {parts.map((part, i) => {
        const m = part.match(/^\[(\d+)\]$/);
        if (!m) return <React.Fragment key={i}>{part}</React.Fragment>;
        const n = parseInt(m[1], 10);
        const source = sources?.[n - 1];
        if (!source) return <React.Fragment key={i}>{part}</React.Fragment>;
        return (
          <span className="citation" tabIndex={0} key={i}>
            [{n}]
            <span className="citation-tooltip" role="tooltip">
              <div className="citation-tooltip-title">{source.candidate_name}</div>
              <div className="citation-tooltip-type">{chunkLabel(source.chunk_type)}</div>
              <div className="citation-tooltip-snippet">{source.snippet}</div>
            </span>
          </span>
        );
      })}
    </>
  );
}

export default function ChatPanel() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  async function send(question) {
    const q = (question ?? input).trim();
    if (!q || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text: q }]);
    setLoading(true);
    try {
      const res = await api.chat(q);
      setMessages((m) => [...m, { role: "assistant", text: res.answer, sources: res.sources }]);
    } catch (err) {
      setMessages((m) => [...m, { role: "assistant", text: `Error: ${err.message}`, sources: [] }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card chat-shell">
      <div className="chat-messages" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="empty-state">
            <p>Ask about your candidate database in plain language.</p>
            <div style={{ display: "flex", flexDirection: "column", gap: 8, alignItems: "center" }}>
              {SUGGESTIONS.map((s) => (
                <button key={s} className="btn btn-secondary" onClick={() => send(s)}>{s}</button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <React.Fragment key={i}>
            <div className={`msg ${m.role}`}>
              {m.role === "assistant" ? <AnswerText text={m.text} sources={m.sources} /> : m.text}
            </div>
            {m.role === "assistant" && m.sources?.length > 0 && (
              <div className="sources">
                <div className="sources-label">Referenced candidates</div>
                {m.sources.map((s, j) => (
                  <div className="source-card" key={j}>
                    <div className="source-title">
                      <span>[{j + 1}] {s.candidate_name}</span>
                      <span className="muted">{chunkLabel(s.chunk_type)}</span>
                    </div>
                    <div className="snippet">{s.snippet}</div>
                  </div>
                ))}
              </div>
            )}
          </React.Fragment>
        ))}
        {loading && <div className="msg assistant loading">Thinking...</div>}
      </div>
      <div className="chat-input-row">
        <input
          placeholder="e.g. Which candidates have Kubernetes experience and are open to Bengaluru?"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
        />
        <button className="btn btn-primary" onClick={() => send()} disabled={loading}>Ask</button>
      </div>
    </div>
  );
}
