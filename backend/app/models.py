import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from app.database import Base


class Candidate(Base):
    """
    One row = one candidate, merged from every resume / Naukri profile /
    other document we've seen for them (see crud.merge_candidate for the
    de-duplication logic). Columns mirror the Master Excel export 1:1 so
    exporting is a straight column-for-column dump.
    """
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    candidate_code = Column(String, unique=True, index=True)  # e.g. CAND-0001

    name = Column(String, index=True)
    email = Column(String, index=True)
    phone = Column(String, index=True)
    current_location = Column(String)
    preferred_locations = Column(String)

    total_experience_years = Column(Float)
    current_company = Column(String)
    current_designation = Column(String)
    current_role_since = Column(String)
    current_ctc_lpa = Column(Float, nullable=True)
    expected_ctc_lpa = Column(Float, nullable=True)
    notice_period = Column(String, nullable=True)

    domain = Column(String)
    primary_skills = Column(Text)
    all_skills = Column(Text)
    certifications = Column(Text)

    highest_education = Column(String)
    education_details = Column(Text)

    work_history = Column(Text)
    total_companies = Column(Integer, nullable=True)
    previous_companies = Column(Text)
    key_projects_clients = Column(Text)
    achievements = Column(Text)

    languages_known = Column(String)
    telugu = Column(String, default="No")  # "Yes" / "No" - knows Telugu
    date_of_birth = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    marital_status = Column(String, nullable=True)
    work_authorization = Column(String, nullable=True)

    profile_summary = Column(Text)
    source_files = Column(Text)  # newline separated list of filenames merged into this record

    recruiter_notes = Column(Text, default="")
    status = Column(String, default="New")

    date_added = Column(DateTime, default=datetime.datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Normalized fields used purely for de-duplication matching (not shown in UI)
    email_norm = Column(String, index=True, nullable=True)
    phone_norm = Column(String, index=True, nullable=True)
