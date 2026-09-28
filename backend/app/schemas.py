from typing import Optional, List
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Schema Gemini must fill in when parsing a resume / Naukri profile.
# Keeping this separate from the DB schema lets the model return clean lists
# (which we then join into the DB's text columns) instead of guessing at
# formatting.
# ---------------------------------------------------------------------------
class WorkHistoryItem(BaseModel):
    company: str = Field(description="Employer name")
    title: str = Field(description="Job title / designation held there")
    duration: str = Field(description="Duration as stated in the document, e.g. 'Mar 2022 - Present (4y 6m)'")
    location: Optional[str] = Field(default=None, description="City/office location if mentioned")


class ExtractedCandidate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    current_location: Optional[str] = None
    preferred_locations: Optional[str] = None
    total_experience_years: Optional[float] = Field(
        default=None, description="Total professional experience in years, as a decimal number, e.g. 6.5"
    )
    current_company: Optional[str] = None
    current_designation: Optional[str] = None
    current_role_since: Optional[str] = None
    current_ctc_lpa: Optional[float] = Field(default=None, description="Current CTC in Lakhs Per Annum (India), numeric only")
    expected_ctc_lpa: Optional[float] = Field(default=None, description="Expected CTC in Lakhs Per Annum, numeric only")
    notice_period: Optional[str] = None
    domain: Optional[str] = Field(default=None, description="1-2 sentence description of the candidate's domain/specialization")
    primary_skills: List[str] = Field(default_factory=list, description="5-10 headline skills")
    all_skills: List[str] = Field(default_factory=list, description="Every skill, tool, technology or platform mentioned anywhere in the document")
    certifications: List[str] = Field(default_factory=list)
    highest_education: Optional[str] = None
    education_details: List[str] = Field(default_factory=list, description="One entry per degree/qualification with institute and year")
    work_history: List[WorkHistoryItem] = Field(default_factory=list)
    previous_companies: List[str] = Field(default_factory=list, description="All employers EXCLUDING the current one")
    key_projects_clients: List[str] = Field(default_factory=list, description="Notable projects, clients, or products worked on")
    achievements: List[str] = Field(default_factory=list, description="Awards, quantified impact, notable accomplishments")
    languages_known: List[str] = Field(default_factory=list)
    telugu: Optional[str] = Field(default=None, description="'Yes' if the candidate knows/speaks Telugu, otherwise 'No'")
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    work_authorization: Optional[str] = Field(default=None, description="Visa status / work authorization notes if mentioned")
    profile_summary: Optional[str] = Field(default=None, description="2-4 sentence professional summary")


# ---------------------------------------------------------------------------
# API-facing schemas
# ---------------------------------------------------------------------------
class CandidateCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    current_location: Optional[str] = None
    preferred_locations: Optional[str] = None
    total_experience_years: Optional[float] = None
    current_company: Optional[str] = None
    current_designation: Optional[str] = None
    current_role_since: Optional[str] = None
    current_ctc_lpa: Optional[float] = None
    expected_ctc_lpa: Optional[float] = None
    notice_period: Optional[str] = None
    domain: Optional[str] = None
    primary_skills: Optional[str] = ""
    all_skills: Optional[str] = ""
    certifications: Optional[str] = ""
    highest_education: Optional[str] = None
    education_details: Optional[str] = ""
    work_history: Optional[str] = ""
    total_companies: Optional[int] = None
    previous_companies: Optional[str] = ""
    key_projects_clients: Optional[str] = ""
    achievements: Optional[str] = ""
    languages_known: Optional[str] = ""
    telugu: Optional[str] = "No"
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    work_authorization: Optional[str] = None
    profile_summary: Optional[str] = ""
    recruiter_notes: Optional[str] = ""
    status: Optional[str] = "New"
    source_files: Optional[str] = None  # lets the frontend carry filenames through from an upload-prefill


class CandidateUpdate(CandidateCreate):
    name: Optional[str] = None


class CandidateRead(CandidateCreate):
    id: int
    candidate_code: str
    source_files: Optional[str] = ""
    date_added: Optional[str] = None
    last_updated: Optional[str] = None

    class Config:
        from_attributes = True


class UploadResult(BaseModel):
    filename: str
    status: str  # "created" | "merged" | "error"
    candidate_id: Optional[int] = None
    candidate_name: Optional[str] = None
    message: Optional[str] = None


class ChatSource(BaseModel):
    candidate_id: int
    candidate_name: str
    chunk_type: str
    snippet: str
    source_files: Optional[str] = None


class ChatRequest(BaseModel):
    question: str
    top_k: int = 10


class ChatResponse(BaseModel):
    answer: str
    sources: List[ChatSource]
