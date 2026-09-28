from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud, schemas
from app.excel_export import export_candidates_to_excel
from app.rag.vector_store import index_candidate, remove_candidate
from app.extraction import extract_from_file, extracted_to_candidate_dict, SUPPORTED_EXTENSIONS
from app.config import EXCEL_PATH, MAX_UPLOAD_MB

router = APIRouter(prefix="/api/candidates", tags=["candidates"])


def _sync_after_write(db: Session):
    candidates = crud.list_candidates(db)
    export_candidates_to_excel(candidates)


def _reindex(candidate):
    """Refresh this candidate's chatbot search index. Never lets a Gemini/embedding
    hiccup (bad key, offline, rate limit) break a plain CRUD save - the candidate
    record itself is already committed to the database by the time this runs."""
    try:
        from app.crud import candidate_to_rag_documents
        docs = candidate_to_rag_documents(candidate)
        index_candidate(candidate.id, candidate.name, candidate.source_files or "", docs)
    except Exception as e:
        print(f"[warn] Could not update chatbot index for candidate {candidate.id}: {e}")


@router.get("", response_model=List[schemas.CandidateRead])
def list_candidates(db: Session = Depends(get_db)):
    rows = crud.list_candidates(db)
    return [_serialize(c) for c in rows]


def _serialize(c) -> dict:
    d = {col.name: getattr(c, col.name) for col in c.__table__.columns}
    if d.get("date_added"):
        d["date_added"] = d["date_added"].isoformat()
    if d.get("last_updated"):
        d["last_updated"] = d["last_updated"].isoformat()
    return d


@router.get("/{candidate_id}", response_model=schemas.CandidateRead)
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    c = crud.get_candidate(db, candidate_id)
    if not c:
        raise HTTPException(404, "Candidate not found")
    return _serialize(c)


@router.post("", response_model=schemas.CandidateRead)
def create_candidate(payload: schemas.CandidateCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    source_label = data.pop("source_files", None) or "Added manually"
    # Dedup-aware: if this email/phone already exists (e.g. the form was pre-filled
    # from an upload for someone already in the database), merge into that record
    # instead of creating a duplicate.
    candidate, _action = crud.upsert_candidate_from_extraction(db, data, source_label)
    _reindex(candidate)
    _sync_after_write(db)
    return _serialize(candidate)


@router.put("/{candidate_id}", response_model=schemas.CandidateRead)
def update_candidate(candidate_id: int, payload: schemas.CandidateUpdate, db: Session = Depends(get_db)):
    candidate = crud.get_candidate(db, candidate_id)
    if not candidate:
        raise HTTPException(404, "Candidate not found")
    candidate = crud.update_candidate(db, candidate, payload.model_dump(exclude_unset=True))
    _reindex(candidate)
    _sync_after_write(db)
    return _serialize(candidate)


@router.delete("/{candidate_id}")
def delete_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = crud.get_candidate(db, candidate_id)
    if not candidate:
        raise HTTPException(404, "Candidate not found")
    remove_candidate(candidate_id)
    crud.delete_candidate(db, candidate)
    _sync_after_write(db)
    return {"ok": True}


@router.post("/extract")
async def extract_resumes(files: List[UploadFile] = File(...)):
    """
    Extraction ONLY - nothing is saved to the database here. Every uploaded
    file is parsed with Gemini individually, then automatically clustered by
    candidate (matching normalized email/phone) - so dropping in a resume +
    Naukri export for ONE person merges into a single set of fields, while
    dropping in resumes for SEVERAL different people produces one group per
    person. The frontend opens one Add Candidate tab per group, pre-filled;
    nothing is saved to the database until the user confirms each tab (POST
    /api/candidates), which is also where de-duplication against candidates
    already in the database happens.
    """
    items: list[tuple[str, dict]] = []
    errors = []
    for f in files:
        try:
            content = await f.read()
            if len(content) > MAX_UPLOAD_MB * 1024 * 1024:
                raise ValueError(f"File exceeds {MAX_UPLOAD_MB}MB limit")
            extracted = extract_from_file(f.filename, content)
            items.append((f.filename, extracted_to_candidate_dict(extracted)))
        except Exception as e:
            errors.append({"filename": f.filename, "message": str(e)})

    if not items:
        raise HTTPException(400, f"Could not extract any candidate data. Errors: {errors}")

    groups = crud.group_extracted_dicts(items)
    candidates = []
    for g in groups:
        data = dict(g["data"])
        data["source_files"] = "\n".join(g["files"])
        candidates.append({"data": data, "files": g["files"]})

    return {"candidates": candidates, "errors": errors}


@router.get("/export/excel")
def download_excel(db: Session = Depends(get_db)):
    _sync_after_write(db)
    if not EXCEL_PATH.exists():
        raise HTTPException(404, "No export available yet")
    return FileResponse(
        EXCEL_PATH,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="Master_Candidate_Database.xlsx",
    )
