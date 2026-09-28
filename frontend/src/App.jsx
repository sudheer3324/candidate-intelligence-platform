import React, { useEffect, useMemo, useState } from "react";
import { api } from "./api";
import { STATUS_OPTIONS } from "./utils";
import CandidateTable from "./components/CandidateTable";
import CandidateModal from "./components/CandidateModal";
import MultiCandidateModal from "./components/MultiCandidateModal";
import UploadPanel from "./components/UploadPanel";
import ChatPanel from "./components/ChatPanel";

export default function App() {
  const [tab, setTab] = useState("candidates");
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [modalCandidate, setModalCandidate] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [addPrefill, setAddPrefill] = useState(null);
  const [uploadQueue, setUploadQueue] = useState(null); // array of {data, files} once an upload extracts candidates
  const [showUpload, setShowUpload] = useState(false);
  const [toast, setToast] = useState(null);

  async function refresh() {
    setLoading(true);
    try {
      setCandidates(await api.listCandidates());
    } catch (err) {
      showToast(err.message, true);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { refresh(); }, []);

  function showToast(text, isError = false) {
    setToast({ text, isError });
    setTimeout(() => setToast(null), 4000);
  }

  const filtered = useMemo(() => {
    return candidates.filter((c) => {
      if (statusFilter && c.status !== statusFilter) return false;
      if (!search.trim()) return true;
      const haystack = [
        c.name, c.email, c.phone, c.current_company, c.current_designation,
        c.domain, c.primary_skills, c.all_skills, c.current_location,
      ].join(" ").toLowerCase();
      return haystack.includes(search.toLowerCase());
    });
  }, [candidates, search, statusFilter]);

  async function handleSaveNew(data) {
    await api.createCandidate(data);
    setShowAddModal(false);
    setAddPrefill(null);
    showToast("Candidate added and master Excel updated.");
    refresh();
  }

  function handleExtracted(candidates) {
    setShowUpload(false);
    if (candidates.length === 1) {
      // Single candidate found - go straight to the familiar single Add Candidate form.
      setAddPrefill({ ...candidates[0].data, source_files: candidates[0].data.source_files });
      setShowAddModal(true);
    } else {
      // Multiple candidates found in this batch of uploads - one tab each.
      setUploadQueue(candidates);
    }
  }

  async function handleSaveFromQueue(data) {
    await api.createCandidate(data);
    showToast("Candidate added and master Excel updated.");
    refresh();
  }

  async function handleSaveEdit(data) {
    await api.updateCandidate(modalCandidate.id, data);
    setModalCandidate(null);
    showToast("Candidate updated.");
    refresh();
  }

  async function handleDelete(candidate) {
    if (!confirm(`Delete ${candidate.name}? This cannot be undone.`)) return;
    await api.deleteCandidate(candidate.id);
    showToast("Candidate deleted.");
    refresh();
  }

  return (
    <>
      <header className="app-header">
        <div>
          <h1>TalentMatch AI</h1>
          <div className="subtitle">Candidate database + AI-powered recruiter assistant</div>
        </div>
        <div className="tabs">
          <button className={tab === "candidates" ? "active" : ""} onClick={() => setTab("candidates")}>
            Candidates
          </button>
          <button className={tab === "chat" ? "active" : ""} onClick={() => setTab("chat")}>
            Ask AI
          </button>
        </div>
      </header>

      <main className="main">
        {tab === "candidates" && (
          <>
            <div className="toolbar">
              <input
                className="search-input"
                placeholder="Search by name, skill, company, location..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
              <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                <option value="">All statuses</option>
                {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
              <button className="btn btn-secondary" onClick={() => setShowUpload(true)}>
                Upload Resume (auto-fill)
              </button>
              <button className="btn btn-secondary" onClick={() => { setAddPrefill(null); setShowAddModal(true); }}>
                + Add Candidate
              </button>
              <a className="btn btn-primary" href={api.downloadExcelUrl()}>
                Download Excel
              </a>
            </div>

            {loading ? (
              <p className="muted">Loading candidates...</p>
            ) : (
              <>
                <p className="muted" style={{ marginTop: -6 }}>
                  {filtered.length} of {candidates.length} candidate{candidates.length === 1 ? "" : "s"}
                </p>
                <CandidateTable
                  candidates={filtered}
                  onEdit={(c) => setModalCandidate(c)}
                  onDelete={handleDelete}
                />
              </>
            )}
          </>
        )}

        {tab === "chat" && <ChatPanel />}
      </main>

      {showAddModal && (
        <CandidateModal
          initial={addPrefill}
          onClose={() => { setShowAddModal(false); setAddPrefill(null); }}
          onSave={handleSaveNew}
        />
      )}
      {modalCandidate && (
        <CandidateModal
          initial={modalCandidate}
          onClose={() => setModalCandidate(null)}
          onSave={handleSaveEdit}
        />
      )}
      {showUpload && (
        <UploadPanel onClose={() => setShowUpload(false)} onExtracted={handleExtracted} />
      )}
      {uploadQueue && (
        <MultiCandidateModal
          candidates={uploadQueue}
          onClose={() => setUploadQueue(null)}
          onSaveOne={handleSaveFromQueue}
        />
      )}

      {toast && <div className={`toast ${toast.isError ? "error" : ""}`}>{toast.text}</div>}
    </>
  );
}
