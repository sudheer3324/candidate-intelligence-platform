from app.rag.vector_store import search
from app.gemini_client import generate_chat_answer
from app.schemas import ChatSource


def answer_question(question: str, top_k: int = 10):
    """
    Retrieve context and generate a cited answer.

    Retrieval strategy ("spread across the table" instead of "pile onto one
    or two candidates"): a plain top-k vector search over chunks tends to
    return several chunks belonging to the SAME one or two best-matching
    candidates (each candidate has ~4 chunks - overview/work history/skills/
    projects), which starves the model of visibility into other, possibly
    equally-relevant candidates. Instead we:
      1. Pull a wider pool of raw chunk hits (3x top_k).
      2. Group them by candidate and rank candidates by their single best
         (lowest-distance) chunk.
      3. Take the top N distinct candidates (N = top_k // 2) and, for each,
         include up to their 2 best-matching chunks.
    This keeps the context window small while maximizing how many distinct,
    genuinely-relevant candidates the model can see and compare - which is
    what "who are ALL the candidates who..." / "compare X vs Y vs Z" style
    recruiting questions need.

    Sources are numbered in the exact order they're handed to Gemini as
    context, and the system prompt instructs Gemini to cite using those same
    [n] numbers - so `sources[i]` always corresponds to citation "[i+1]" in
    the returned answer text, and the frontend can render hoverable citation
    chips directly from that mapping.
    """
    raw_hits = search(question, top_k=max(top_k * 3, 20))
    if not raw_hits:
        return generate_chat_answer(question, []), []

    by_candidate: dict[int, list[dict]] = {}
    for h in raw_hits:
        cid = h["metadata"]["candidate_id"]
        by_candidate.setdefault(cid, []).append(h)

    ranked_candidates = sorted(
        by_candidate.items(),
        key=lambda kv: min(h["distance"] for h in kv[1]),
    )

    max_candidates = max(1, top_k // 2)
    selected_hits = []
    for _cid, hits in ranked_candidates[:max_candidates]:
        best_for_candidate = sorted(hits, key=lambda h: h["distance"])[:2]
        selected_hits.extend(best_for_candidate)
    selected_hits.sort(key=lambda h: h["distance"])

    sources = []
    numbered_context = []
    for i, h in enumerate(selected_hits, start=1):
        meta = h["metadata"]
        text = h["text"]
        snippet = (text[:400] + "...") if len(text) > 400 else text
        sources.append(ChatSource(
            candidate_id=meta["candidate_id"],
            candidate_name=meta["candidate_name"],
            chunk_type=meta["chunk_type"],
            snippet=snippet,
            source_files=meta.get("source_files"),
        ))
        numbered_context.append(
            f"[{i}] {meta['candidate_name']} - {meta['chunk_type'].replace('_', ' ')}:\n{text}"
        )

    answer = generate_chat_answer(question, numbered_context)
    return answer, sources
