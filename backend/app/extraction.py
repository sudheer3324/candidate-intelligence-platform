"""
Turns an uploaded file (PDF / DOCX / TXT) into an ExtractedCandidate by
routing it to Gemini in whatever form Gemini understands best, then converts
that structured result into the flat text fields our database/Excel use.
"""
import io
from pathlib import Path

import docx  # python-docx

from app.gemini_client import extract_candidate_from_document
from app.schemas import ExtractedCandidate

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def _docx_to_text(file_bytes: bytes) -> str:
    document = docx.Document(io.BytesIO(file_bytes))
    parts = [p.text for p in document.paragraphs if p.text.strip()]
    for table in document.tables:
        for row in table.rows:
            parts.append(" | ".join(cell.text for cell in row.cells))
    return "\n".join(parts)


def extract_from_file(filename: str, file_bytes: bytes) -> ExtractedCandidate:
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")

    if ext == ".pdf":
        return extract_candidate_from_document(file_bytes, "application/pdf", filename)

    if ext == ".docx":
        text = _docx_to_text(file_bytes)
        return extract_candidate_from_document(text.encode("utf-8"), "text/plain", filename)

    # .txt
    return extract_candidate_from_document(file_bytes, "text/plain", filename)


def join_list(items, sep="; "):
    return sep.join(i for i in (items or []) if i)


def work_history_to_text(work_history) -> str:
    lines = []
    for item in work_history or []:
        loc = f" ({item.location})" if getattr(item, "location", None) else ""
        lines.append(f"{item.company} - {item.title}{loc} | {item.duration}")
    return "\n".join(lines)


def extracted_to_candidate_dict(extracted: ExtractedCandidate) -> dict:
    """Flatten an ExtractedCandidate (lists everywhere) into the DB's text-column shape."""
    return {
        "name": extracted.name,
        "email": (extracted.email or "").strip().lower() or None,
        "phone": extracted.phone,
        "current_location": extracted.current_location,
        "preferred_locations": extracted.preferred_locations,
        "total_experience_years": extracted.total_experience_years,
        "current_company": extracted.current_company,
        "current_designation": extracted.current_designation,
        "current_role_since": extracted.current_role_since,
        "current_ctc_lpa": extracted.current_ctc_lpa,
        "expected_ctc_lpa": extracted.expected_ctc_lpa,
        "notice_period": extracted.notice_period,
        "domain": extracted.domain,
        "primary_skills": join_list(extracted.primary_skills),
        "all_skills": join_list(sorted(set(extracted.all_skills), key=lambda x: extracted.all_skills.index(x))),
        "certifications": join_list(extracted.certifications),
        "highest_education": extracted.highest_education,
        "education_details": join_list(extracted.education_details, sep="\n"),
        "work_history": work_history_to_text(extracted.work_history),
        "total_companies": len(set(w.company for w in (extracted.work_history or []))) or None,
        "previous_companies": join_list(extracted.previous_companies),
        "key_projects_clients": join_list(extracted.key_projects_clients),
        "achievements": join_list(extracted.achievements),
        "languages_known": join_list(extracted.languages_known),
        "telugu": "Yes" if any("telugu" in (lang or "").lower() for lang in extracted.languages_known) else "No",
        "date_of_birth": extracted.date_of_birth,
        "gender": extracted.gender,
        "marital_status": extracted.marital_status,
        "work_authorization": extracted.work_authorization,
        "profile_summary": extracted.profile_summary,
    }
