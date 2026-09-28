"""
Thin wrapper around the google-genai SDK. Every Gemini call in the app goes
through here, so if Google changes the SDK surface again in the future, this
is the one file that needs updating.
"""
from typing import List
from google import genai
from google.genai import types

from app.config import (
    GEMINI_API_KEY, GEMINI_EXTRACTION_MODEL, GEMINI_CHAT_MODEL,
    GEMINI_EMBEDDING_MODEL, EMBEDDING_DIMENSIONS,
)
from app.schemas import ExtractedCandidate

_client = None


def get_client() -> genai.Client:
    global _client
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to backend/.env (see backend/.env.example) "
            "then restart the app."
        )
    if _client is None:
        # Keep retries short: if Gemini/the network is unreachable we want the app
        # to fail fast (a few seconds) with a clear error rather than hang for a
        # long time behind the SDK's default retry/backoff schedule.
        _client = genai.Client(
            api_key=GEMINI_API_KEY,
            http_options=types.HttpOptions(
                timeout=20_000,  # ms per attempt
                retry_options=types.HttpRetryOptions(attempts=2, initial_delay=1.0, max_delay=4.0),
            ),
        )
    return _client


EXTRACTION_PROMPT = """You are an expert technical recruiter's assistant. Read the attached candidate
document (it may be a resume, a Naukri.com profile export, or both combined) and extract every
field in the schema as accurately as possible.

Rules:
- Only use information present in the document. Never invent facts.
- If a field is not mentioned, leave it empty / null / an empty list - do not guess.
- "total_experience_years" should be your best numeric estimate of TOTAL professional experience
  (e.g. a Naukri header like "12y 8m" -> 12.7). If several numbers conflict, prefer the most
  recent / most prominent one (e.g. the Naukri profile header over an older attached resume).
- "all_skills" should be exhaustive - include every technology, tool, platform, methodology and
  soft skill mentioned anywhere in the document, not just the "Key Skills" section.
- "work_history" should list every employer, most recent first, in the order given in the source.
- Money amounts: convert to Lakhs Per Annum (LPA) as a plain number (e.g. "Rs. 28,00,000" -> 28,
  "42 Lacs" -> 42). Leave null if not in LPA/India-style pay.
"""


def extract_candidate_from_document(file_bytes: bytes, mime_type: str, filename: str) -> ExtractedCandidate:
    """Send a resume/profile document to Gemini and get back structured fields."""
    client = get_client()
    part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
    response = client.models.generate_content(
        model=GEMINI_EXTRACTION_MODEL,
        contents=[part, types.Part.from_text(text=EXTRACTION_PROMPT + f"\n\nFilename: {filename}")],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ExtractedCandidate,
            temperature=0.1,
        ),
    )
    parsed = response.parsed
    if parsed is None:
        # Fall back to manual JSON parsing if the SDK couldn't auto-parse for some reason.
        import json
        parsed = ExtractedCandidate.model_validate(json.loads(response.text))
    return parsed


def embed_texts(texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT") -> List[List[float]]:
    """Embed a batch of texts. task_type should be RETRIEVAL_DOCUMENT when embedding
    candidate data to store, or RETRIEVAL_QUERY when embedding a user's chat question."""
    if not texts:
        return []
    client = get_client()
    result = client.models.embed_content(
        model=GEMINI_EMBEDDING_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=EMBEDDING_DIMENSIONS,
        ),
    )
    return [e.values for e in result.embeddings]


CHAT_SYSTEM_PROMPT = """You are TalentMatch AI, a recruiting assistant helping a technical resource
mapping engineer find and compare candidates for client requirements.

CONTEXT FORMAT
You will be given a numbered list of candidate context snippets retrieved from the candidate
database, like:
[1] Jane Doe - overview:
...
[2] Jane Doe - skills:
...
[3] John Smith - overview:
...
Each snippet is independent evidence. The same candidate may appear in more than one snippet
(e.g. their overview AND their skills) - treat those as one person, not two.

GROUND RULES
- Answer using ONLY the information in the snippets above. Never invent a skill, employer, number,
  or fact that isn't stated in them.
- Scan EVERY snippet before answering, not just the first one or two - the snippets are pre-selected
  to span as many distinct, relevant candidates as the database has, specifically so you can compare
  or list across the whole matching set rather than fixating on a single result.
- If the question asks for "who/which candidates match X", check each candidate against X
  individually and only include ones that actually satisfy it based on the snippets - do not include
  a candidate just because they appear in the context if they don't actually meet the criteria.
- If the snippets don't contain enough information to answer confidently (e.g. no candidate matches,
  or the data needed isn't present), say so plainly and suggest what additional information or
  upload would help - never guess or pad the answer.
- Answer strictly what was asked - if asked for candidates matching X, give only those who match X. Do not mention who doesn't match, why others were excluded, or any candidate not relevant to the question.
- If no snippet satisfies the request, say so in one line and stop - no partial matches, no filler, no "closest" candidates unless asked for close matches.

CITATIONS (required)
- Every factual claim must be followed immediately by the bracket number(s) of the snippet(s) it
  came from, e.g. "Jane Doe has 8 years of Oracle DBA experience [2]." or "...matches both criteria
  [1][4]."
- Use ONLY the exact numbers given in the context - never renumber, combine, or invent numbers.
- Do not add a "References" or "Sources" list at the end of your answer - citations are inline only,
  the app renders them separately.

STYLE
- Name candidates explicitly when recommending or comparing them, and briefly explain why they fit
  (skills, experience, domain, current role) - grounded in the cited snippet.
- Keep the answer concise and scannable (short paragraphs or a short list) - this is read by a busy
  recruiter, not a report audience.
"""


def generate_chat_answer(question: str, context_chunks: List[str]) -> str:
    client = get_client()
    context = "\n\n---\n\n".join(context_chunks) if context_chunks else "(no matching candidates found)"
    prompt = f"CANDIDATE CONTEXT:\n{context}\n\nRECRUITER QUESTION: {question}"
    response = client.models.generate_content(
        model=GEMINI_CHAT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=CHAT_SYSTEM_PROMPT,
            temperature=0.3,
        ),
    )
    return response.text or "I couldn't generate an answer - please try rephrasing your question."
