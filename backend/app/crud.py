import re
import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Candidate


def normalize_email(email: Optional[str]) -> Optional[str]:
    if not email:
        return None
    return email.strip().lower() or None


def normalize_phone(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    return digits[-10:] if len(digits) >= 10 else (digits or None)


def next_candidate_code(db: Session) -> str:
    count = db.query(func.count(Candidate.id)).scalar() or 0
    return f"CAND-{count + 1:04d}"


def find_existing_candidate(db: Session, email: Optional[str], phone: Optional[str]) -> Optional[Candidate]:
    """De-duplication lookup: match by email first, then phone."""
    email_n = normalize_email(email)
    phone_n = normalize_phone(phone)
    if email_n:
        existing = db.query(Candidate).filter(Candidate.email_norm == email_n).first()
        if existing:
            return existing
    if phone_n:
        existing = db.query(Candidate).filter(Candidate.phone_norm == phone_n).first()
        if existing:
            return existing
    return None


NEWLINE_SEP_FIELDS = {"work_history", "education_details"}


def _merge_field(old_value, new_value, mode: str, field: str = ""):
    """mode='overwrite' -> new wins if present; mode='union' -> combine unique items."""
    if mode == "overwrite":
        return new_value if new_value not in (None, "", []) else old_value
    sep = "\n" if field in NEWLINE_SEP_FIELDS else "; "
    old_items = [i.strip() for i in re.split(r"; |\n", old_value or "") if i.strip()]
    new_items = [i.strip() for i in re.split(r"; |\n", new_value or "") if i.strip()]
    merged, seen = [], set()
    for i in old_items + new_items:
        key = i.lower()
        if key not in seen:
            seen.add(key)
            merged.append(i)
    return sep.join(merged)


OVERWRITE_FIELDS = {
    "name", "email", "phone", "current_location", "preferred_locations",
    "total_experience_years", "current_company", "current_designation",
    "current_role_since", "current_ctc_lpa", "expected_ctc_lpa", "notice_period",
    "domain", "highest_education", "date_of_birth", "gender", "marital_status",
    "work_authorization", "profile_summary", "total_companies", "telugu",
}
UNION_FIELDS = {
    "primary_skills", "all_skills", "certifications", "education_details",
    "work_history", "previous_companies", "key_projects_clients",
    "achievements", "languages_known",
}


def upsert_candidate_from_extraction(db: Session, data: dict, source_filename: str) -> tuple[Candidate, str]:
    """
    Insert a new candidate row, or merge into an existing one if the email/phone
    matches a record we already have (de-duplication). Returns (candidate, "created"|"merged").
    """
    existing = find_existing_candidate(db, data.get("email"), data.get("phone"))

    if existing is None:
        candidate = Candidate(**{k: v for k, v in data.items() if k in Candidate.__table__.columns.keys()})
        candidate.candidate_code = next_candidate_code(db)
        candidate.email_norm = normalize_email(data.get("email"))
        candidate.phone_norm = normalize_phone(data.get("phone"))
        candidate.source_files = source_filename
        candidate.status = "New"
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        return candidate, "created"

    for field in OVERWRITE_FIELDS:
        setattr(existing, field, _merge_field(getattr(existing, field), data.get(field), "overwrite", field))
    for field in UNION_FIELDS:
        setattr(existing, field, _merge_field(getattr(existing, field), data.get(field), "union", field))

    existing.email_norm = normalize_email(existing.email)
    existing.phone_norm = normalize_phone(existing.phone)
    existing_sources = set((existing.source_files or "").splitlines())
    existing_sources.add(source_filename)
    existing.source_files = "\n".join(sorted(existing_sources))
    existing.last_updated = datetime.datetime.utcnow()

    db.commit()
    db.refresh(existing)
    return existing, "merged"


def merge_extracted_dicts(dicts: list[dict]) -> dict:
    """Combine several per-file extraction dicts (e.g. a resume + a Naukri
    export for the SAME candidate, uploaded together) into one record, using
    the same overwrite/union rules as merging into an existing DB row."""
    if not dicts:
        return {}
    merged = dict(dicts[0])
    for d in dicts[1:]:
        for field in OVERWRITE_FIELDS:
            merged[field] = _merge_field(merged.get(field), d.get(field), "overwrite", field)
        for field in UNION_FIELDS:
            merged[field] = _merge_field(merged.get(field), d.get(field), "union", field)
    return merged


def group_extracted_dicts(items: list[tuple[str, dict]]) -> list[dict]:
    """
    Take a batch of (filename, extracted_dict) pairs from a single multi-file
    upload - which may contain documents for SEVERAL DIFFERENT candidates at
    once (e.g. a recruiter drops in 5 resumes together) - and cluster them
    into one group per real candidate.

    Two files are grouped together only when they share a normalized email
    OR a normalized phone number (the same signal used for de-dup against the
    existing database in find_existing_candidate/upsert_candidate_from_extraction).
    Files with no email/phone at all are never auto-merged with anything else,
    since name-only matching risks silently combining two different people.

    Returns a list of {"data": merged_dict, "files": [filenames]} - one entry
    per detected candidate, in first-seen order.
    """
    groups: list[dict] = []  # each: {"data": dict, "files": [str], "emails": set, "phones": set}

    for filename, data in items:
        email_n = normalize_email(data.get("email"))
        phone_n = normalize_phone(data.get("phone"))
        match = None
        if email_n or phone_n:
            for g in groups:
                if (email_n and email_n in g["emails"]) or (phone_n and phone_n in g["phones"]):
                    match = g
                    break
        if match is None:
            groups.append({
                "data": dict(data),
                "files": [filename],
                "emails": {email_n} if email_n else set(),
                "phones": {phone_n} if phone_n else set(),
            })
        else:
            match["data"] = merge_extracted_dicts([match["data"], data])
            match["files"].append(filename)
            if email_n:
                match["emails"].add(email_n)
            if phone_n:
                match["phones"].add(phone_n)

    return [{"data": g["data"], "files": g["files"]} for g in groups]


def update_candidate(db: Session, candidate: Candidate, data: dict) -> Candidate:
    for k, v in data.items():
        if v is not None and hasattr(candidate, k):
            setattr(candidate, k, v)
    candidate.email_norm = normalize_email(candidate.email)
    candidate.phone_norm = normalize_phone(candidate.phone)
    candidate.last_updated = datetime.datetime.utcnow()
    db.commit()
    db.refresh(candidate)
    return candidate


def delete_candidate(db: Session, candidate: Candidate):
    db.delete(candidate)
    db.commit()


def get_candidate(db: Session, candidate_id: int) -> Optional[Candidate]:
    return db.query(Candidate).filter(Candidate.id == candidate_id).first()


def list_candidates(db: Session):
    return db.query(Candidate).order_by(Candidate.id.asc()).all()


def candidate_to_rag_documents(candidate: Candidate) -> list[dict]:
    """Split a candidate record into a few semantically-grouped chunks for the vector store."""
    docs = []

    overview = (
        f"Candidate: {candidate.name}\n"
        f"Current role: {candidate.current_designation or '-'} at {candidate.current_company or '-'} "
        f"(since {candidate.current_role_since or 'unknown'})\n"
        f"Total experience: {candidate.total_experience_years or '-'} years\n"
        f"Domain/specialization: {candidate.domain or '-'}\n"
        f"Location: {candidate.current_location or '-'} | Preferred: {candidate.preferred_locations or '-'}\n"
        f"Primary skills: {candidate.primary_skills or '-'}\n"
        f"Current CTC: {candidate.current_ctc_lpa or '-'} LPA | Expected CTC: {candidate.expected_ctc_lpa or '-'} LPA\n"
        f"Summary: {candidate.profile_summary or '-'}"
    )
    docs.append({"chunk_type": "overview", "text": overview})

    if candidate.work_history:
        docs.append({
            "chunk_type": "work_history",
            "text": f"Candidate: {candidate.name}\nWork history:\n{candidate.work_history}",
        })

    if candidate.all_skills or candidate.certifications:
        docs.append({
            "chunk_type": "skills",
            "text": (
                f"Candidate: {candidate.name}\n"
                f"All skills: {candidate.all_skills or '-'}\n"
                f"Certifications: {candidate.certifications or '-'}\n"
                f"Education: {candidate.highest_education or '-'}"
            ),
        })

    if candidate.key_projects_clients or candidate.achievements:
        docs.append({
            "chunk_type": "projects_achievements",
            "text": (
                f"Candidate: {candidate.name}\n"
                f"Key projects / clients: {candidate.key_projects_clients or '-'}\n"
                f"Achievements: {candidate.achievements or '-'}"
            ),
        })

    return docs
