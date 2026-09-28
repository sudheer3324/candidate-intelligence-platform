"""
Regenerates the Master Candidate Database Excel file from the SQLite database.
Called automatically after every create/update/delete/upload so the .xlsx on
disk always matches what's in the app (this is the "CRUD updates the master
Excel" behaviour).
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from app.config import EXCEL_PATH

FONT_NAME = "Arial"

COLUMNS = [
    ("Candidate ID", "candidate_code", 12),
    ("Full Name", "name", 24),
    ("Email", "email", 26),
    ("Phone", "phone", 16),
    ("Current Location", "current_location", 18),
    ("Preferred Locations", "preferred_locations", 22),
    ("Total Experience (Yrs)", "total_experience_years", 12),
    ("Current Company", "current_company", 20),
    ("Current Designation", "current_designation", 20),
    ("Current Role Since", "current_role_since", 14),
    ("Current CTC (LPA)", "current_ctc_lpa", 12),
    ("Expected CTC (LPA)", "expected_ctc_lpa", 12),
    ("Notice Period", "notice_period", 12),
    ("Domain / Specialization", "domain", 30),
    ("Primary Skills", "primary_skills", 32),
    ("All Skills (Full List)", "all_skills", 40),
    ("Certifications", "certifications", 32),
    ("Highest Education", "highest_education", 30),
    ("Education Details", "education_details", 34),
    ("Work History", "work_history", 45),
    ("No. of Companies Worked", "total_companies", 12),
    ("Previous Companies", "previous_companies", 30),
    ("Key Projects / Clients", "key_projects_clients", 40),
    ("Achievements / Highlights", "achievements", 40),
    ("Languages Known", "languages_known", 22),
    ("Telugu", "telugu", 10),
    ("Date of Birth", "date_of_birth", 12),
    ("Gender", "gender", 10),
    ("Marital Status", "marital_status", 14),
    ("Work Authorization / Visa", "work_authorization", 24),
    ("Profile Summary", "profile_summary", 45),
    ("Source Files Merged", "source_files", 45),
    ("Recruiter Notes", "recruiter_notes", 30),
    ("Status", "status", 14),
    ("Date Added", "date_added", 14),
    ("Last Updated", "last_updated", 14),
]

HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(name=FONT_NAME, size=10, bold=True, color="FFFFFF")
BODY_FONT = Font(name=FONT_NAME, size=10)
THIN = Side(style="thin", color="D9D9D9")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP_TOP = Alignment(wrap_text=True, vertical="top", horizontal="left")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
STRIPE_FILL = PatternFill("solid", fgColor="F2F7FC")


def export_candidates_to_excel(candidates: list):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Candidate Master"

    ws.append([c[0] for c in COLUMNS])
    for col_idx, (header, key, width) in enumerate(COLUMNS, start=1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = CENTER
        cell.border = BORDER
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    for r, cand in enumerate(candidates, start=2):
        for col_idx, (header, key, width) in enumerate(COLUMNS, start=1):
            val = getattr(cand, key, "")
            if val is None:
                val = ""
            if hasattr(val, "strftime"):
                val = val.strftime("%Y-%m-%d")
            cell = ws.cell(row=r, column=col_idx, value=val)
            cell.font = BODY_FONT
            cell.alignment = WRAP_TOP
            cell.border = BORDER
            if r % 2 == 0:
                cell.fill = STRIPE_FILL
        ws.row_dimensions[r].height = 90

    status_col_idx = [i for i, c in enumerate(COLUMNS, start=1) if c[1] == "status"][0]
    status_letter = get_column_letter(status_col_idx)
    dv = DataValidation(
        type="list",
        formula1='"New,Screened,Submitted,Interviewing,Offered,Placed,Rejected,On Hold"',
        allow_blank=True,
    )
    ws.add_data_validation(dv)
    dv.add(f"{status_letter}2:{status_letter}5000")

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(COLUMNS))}{max(len(candidates)+1, 1)}"

    def col_letter(field_key: str) -> str:
        idx = [i for i, c in enumerate(COLUMNS, start=1) if c[1] == field_key][0]
        return get_column_letter(idx)

    id_col = col_letter("candidate_code")
    exp_col = col_letter("total_experience_years")
    ctc_col = col_letter("current_ctc_lpa")
    status_col_ref = col_letter("status")

    dash = wb.create_sheet("Dashboard")
    dash["B2"] = "Candidate Database - Live Summary"
    dash["B2"].font = Font(name=FONT_NAME, size=14, bold=True, color="1F4E78")
    stats = [
        ("Total Candidates", f"=COUNTA('Candidate Master'!{id_col}2:{id_col}5000)"),
        ("Average Experience (Yrs)", f"=ROUND(AVERAGE('Candidate Master'!{exp_col}2:{exp_col}5000),1)"),
        ("Average Current CTC (LPA)", f"=ROUND(AVERAGE('Candidate Master'!{ctc_col}2:{ctc_col}5000),1)"),
        ("Candidates Marked 'New'", f"=COUNTIF('Candidate Master'!{status_col_ref}2:{status_col_ref}5000,\"New\")"),
        ("Candidates Marked 'Placed'", f"=COUNTIF('Candidate Master'!{status_col_ref}2:{status_col_ref}5000,\"Placed\")"),
    ]
    row = 4
    for label, formula in stats:
        dash.cell(row=row, column=2, value=label).font = Font(name=FONT_NAME, bold=True)
        fcell = dash.cell(row=row, column=4, value=formula)
        fcell.fill = PatternFill("solid", fgColor="FFF2CC")
        fcell.border = BORDER
        row += 1
    dash.column_dimensions["B"].width = 28
    dash.column_dimensions["D"].width = 14

    EXCEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    wb.save(EXCEL_PATH)
    return EXCEL_PATH
