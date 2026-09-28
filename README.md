# TalentMatch AI

A candidate database + AI recruiting assistant, built for resource mapping /
technical recruiting. Upload resumes and Naukri profiles, it builds one
clean, de-duplicated master record per candidate (and keeps a live master
Excel file in sync), and it gives you a chatbot that can answer natural
-language questions about your whole candidate pool with sources cited.

**What it does:**

- **Upload resumes / Naukri profile PDFs (or DOCX/TXT).** Gemini reads each
  one and extracts name, contact info, skills, work history, certifications,
  education, projects, achievements, and more into a structured record.
- **No duplicates.** If you upload a second document for someone already in
  the database (matched by email or phone), it's merged into their existing
  record instead of creating a new row.
- **Master Excel, always up to date.** Every add/edit/delete/upload
  automatically regenerates `Master_Candidate_Database.xlsx` (also
  downloadable any time from the app).
- **Full CRUD** - add candidates manually, edit any field, delete, filter and
  search the table.
- **"Ask AI" chatbot** - ask things like *"Who has the most Kubernetes
  experience?"* or *"Compare my DBA candidates for a MongoDB-heavy role"* and
  get an answer grounded in your actual candidate data, with the specific
  candidates/records it used shown underneath the answer.

It runs entirely on your own computer. Your candidate data never leaves your
machine except for the specific text sent to Google's Gemini API to do the
extraction/chat (see [GEMINI_SETUP.md](GEMINI_SETUP.md) for what that means
for privacy and cost).

---

## 1. One-time setup (5-10 minutes)

You need two things installed on your computer first:

1. **Python 3.10 or newer.** Get it from [python.org/downloads](https://www.python.org/downloads/).
   Windows users: on the first install screen, tick **"Add python.exe to PATH"**
   before clicking Install.
2. **A free Gemini API key.** Full walkthrough with screensheet-by-step
   instructions and current pricing: **[GEMINI_SETUP.md](GEMINI_SETUP.md)**.
   Takes about 2 minutes and costs nothing to create.

That's it - you do **not** need to install Node.js, Docker, or any database
software. Everything else is handled automatically.

## 2. Starting the app

**Windows:** double-click `start.bat`.

**Mac / Linux:** double-click `start.sh` (if your Mac says it can't verify
the app, right-click it and choose "Open" instead), or open a terminal in
this folder and run `./start.sh`.

The first time you run it, it will:
1. Set up a private Python environment for the app (~1-2 minutes).
2. Create a `backend/.env` file for you and pause so you can paste in your
   Gemini API key (open `backend/.env` in Notepad/TextEdit, paste your key
   after `GEMINI_API_KEY=`, save, then re-run the start script).
3. Start the app.

Once you see `Application startup complete`, open your browser to:

```
http://127.0.0.1:8000
```

That's the whole app - candidate database and chatbot in one page. Leave the
terminal/command window open while you use it; closing it stops the app.
Run the same start script any time you want to reopen it later.

## 3. Using it

- **Candidates tab:** click **Upload Resumes** and drop in PDF/DOCX files
  (Naukri profile exports and/or resumes). Each one is parsed automatically.
  Use **+ Add Candidate** to type one in by hand, click **Edit** on any row
  to fix/fill in details, and **Download Excel** any time to get the master
  spreadsheet.
- **Ask AI tab:** type a question about your candidate pool in plain English.

## 4. Where your data lives

Everything is stored locally inside the `backend/data/` folder:

- `app.db` - the real database (SQLite - a single file, no server needed).
- `Master_Candidate_Database.xlsx` - the master Excel, regenerated automatically.
- `chroma_db/` - the local vector database that powers the chatbot's search.

**Back this folder up** (or the whole project folder) the same way you'd
back up any important spreadsheet - copying `backend/data/` elsewhere is a
complete backup.

## 5. Sharing this app with someone else

Zip up this whole folder (minus `backend/.venv` and `backend/data` if you
don't want to share your candidate data) and send it to them. They run the
same setup steps above with their own Gemini API key. No accounts, servers,
or subscriptions to set up on your end.

## 6. Troubleshooting

- **"python3: command not found" / "python is not recognized"** - Python
  isn't installed or wasn't added to PATH. Reinstall from python.org and
  make sure to check the "Add to PATH" box (Windows).
- **The chatbot says it "couldn't reach Gemini"** - open `backend/.env` and
  make sure `GEMINI_API_KEY=` has your real key (no quotes, no extra
  spaces), and that you have an internet connection. See GEMINI_SETUP.md.
- **Port 8000 already in use** - another program is using that port. Edit
  the last line of `start.sh`/`start.bat` and change `--port 8000` to e.g.
  `--port 8010`, then open `http://127.0.0.1:8010` instead.
- **Want to start over completely** - close the app, delete the
  `backend/data` folder, and restart. This wipes all candidates.
- **Upload says a file failed to parse** - make sure it's a real PDF, DOCX,
  or TXT (not a scanned image with no text layer, and not password
  protected).

## 7. Project structure (for developers)

```
talentmatch-ai/
  backend/                 FastAPI app (Python)
    app/
      main.py              App entrypoint, serves the built frontend too
      config.py            All settings (reads backend/.env)
      models.py            SQLAlchemy Candidate model
      schemas.py           Pydantic schemas (incl. the Gemini extraction schema)
      crud.py              Create/read/update/delete + de-duplication merge logic
      extraction.py        Turns an uploaded file into structured fields via Gemini
      gemini_client.py     All Gemini API calls live here
      excel_export.py      Regenerates the master .xlsx from the database
      rag/
        vector_store.py    Chroma vector DB wrapper
        chat.py            Retrieval + answer generation for the chatbot
      routers/
        candidates.py      CRUD + upload + Excel export endpoints
        chat_router.py     Chatbot endpoint
    requirements.txt
    .env.example
    data/                  Created at runtime: app.db, chroma_db/, uploads/, the .xlsx
  frontend/                React app (Vite)
    src/                   Source code
    dist/                  Pre-built production files (this is what actually ships/runs -
                            you do not need Node.js installed to use the app)
  start.sh / start.bat     One-click setup + launch scripts
  GEMINI_SETUP.md          Gemini account setup + current pricing
```

To modify the frontend, edit files under `frontend/src/`, then (with Node.js
installed) run `cd frontend && npm install && npm run build` to regenerate
`frontend/dist/` - the backend serves whatever is in that folder.

To modify the backend, edit files under `backend/app/` - changes take effect
on next restart (or immediately if you run
`uvicorn app.main:app --reload` during development).

## 8. Ideas for further improvement

The app is fully functional as shipped, but if you keep using it, these are the
next things worth considering, roughly in order of impact:

- **Structured filter queries for the chatbot.** Right now "Ask AI" always
  does semantic (vector) search, which is great for fuzzy questions
  ("who's a strong fit for a fintech client?") but can miss exact filters at
  scale ("everyone with 5+ years AND based in Hyderabad AND notice period
  under 30 days"). A worthwhile upgrade is detecting filter-style questions
  and running them as real SQL queries against the database (exact, complete
  results) instead of/alongside vector search.
- **Resume file storage.** The original uploaded PDF/DOCX isn't kept anywhere
  after extraction - only the extracted fields are. If you want to reopen the
  original document later (e.g. to double check a detail), you'd want to
  save uploads into `backend/data/uploads/` and link them from each
  candidate record.
- **Bulk actions on the candidate table** - select multiple rows to bulk
  change status, tag, or export a filtered subset to its own Excel file.
- **Basic auth / login**, if this ever moves off "my own computer only" to a
  shared server - right now anyone who can reach the URL can use the app.
- **Audit trail** - a simple history log of who changed what and when on
  each candidate record (useful once more than one recruiter is using it).
- **Smarter dedup matching** - current de-dup matches by exact
  email/phone only; a fuzzy name + company match (with a "possible
  duplicate, please confirm" prompt rather than silent auto-merge) would
  catch more real-world duplicates where contact info is missing or slightly
  different across documents.
- **Re-rank chat results with a cheap second pass** - the chatbot currently
  ranks by embedding similarity only; for very large candidate pools (1,000+)
  adding a fast keyword/BM25 pre-filter before the vector search would keep
  answers accurate as the database grows well past "a few hundred."




# Copy this file to ".env" (same folder) and fill in your key.
# Get a free key at https://aistudio.google.com/app/apikey
# See the top-level GEMINI_SETUP.md file in this project for full instructions
# and current pricing.

GEMINI_API_KEY=

# Model used to parse resumes/profiles (runs on every upload - high volume,
# mechanical task, so the cheaper "Lite" model is plenty).
GEMINI_EXTRACTION_MODEL=gemini-3.5-flash-lite

# Model used to answer chatbot questions (lower volume, quality matters more).
GEMINI_CHAT_MODEL=gemini-3.5-flash

# Change either any time - no code changes needed. See GEMINI_SETUP.md for options.

# Model used to build the searchable vector database.
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIMENSIONS=768

# Max size (MB) for a single uploaded resume/profile file.
MAX_UPLOAD_MB=20
