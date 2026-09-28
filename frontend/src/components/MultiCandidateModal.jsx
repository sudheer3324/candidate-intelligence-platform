import React, { useState } from "react";
import CandidateFormFields, { EMPTY_CANDIDATE, toPayload } from "./CandidateFormFields";

/**
 * Shown after an upload that produced MULTIPLE candidates (e.g. a recruiter
 * drops in 5 different people's resumes at once). One tab per candidate the
 * extraction step detected; each tab is a full, editable Add Candidate form
 * pre-filled from the extracted document(s) for that person. Confirming a
 * tab saves ONLY that candidate (via onSaveOne) and removes its tab; the
 * modal closes itself once every tab has been confirmed or skipped.
 */
export default function MultiCandidateModal({ candidates, onClose, onSaveOne }) {
  const [tabs, setTabs] = useState(() =>
    candidates.map((c, i) => ({
      id: i,
      files: c.files || [],
      form: { ...EMPTY_CANDIDATE, ...c.data },
    }))
  );
  const [activeId, setActiveId] = useState(0);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const activeIndex = tabs.findIndex((t) => t.id === activeId);
  const active = tabs[activeIndex];

  function set(key, value) {
    setTabs((ts) => ts.map((t) => (t.id === activeId ? { ...t, form: { ...t.form, [key]: value } } : t)));
  }

  function goToNextAfterRemoving(remainingTabs) {
    if (remainingTabs.length === 0) {
      onClose();
      return;
    }
    setActiveId(remainingTabs[0].id);
  }

  function handleSkip() {
    setError(null);
    const remaining = tabs.filter((t) => t.id !== activeId);
    setTabs(remaining);
    goToNextAfterRemoving(remaining);
  }

  async function handleConfirm(e) {
    e.preventDefault();
    if (!active) return;
    setSaving(true);
    setError(null);
    try {
      const payload = toPayload(active.form);
      await onSaveOne(payload);
      const remaining = tabs.filter((t) => t.id !== activeId);
      setTabs(remaining);
      goToNextAfterRemoving(remaining);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  if (!active) return null;

  return (
    <div className="modal-overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" style={{ maxWidth: 860 }}>
        <h2>Confirm extracted candidates</h2>
        <p className="helper-text">
          Found {tabs.length} candidate{tabs.length === 1 ? "" : "s"} in the uploaded documents.
          Review each tab, edit anything that needs fixing, then click "Add Candidate" to save it
          to the master database - it will disappear from this list once saved.
        </p>

        <div className="tab-bar">
          {tabs.map((t, i) => (
            <button
              key={t.id}
              type="button"
              className={`tab-chip ${t.id === activeId ? "active" : ""}`}
              onClick={() => setActiveId(t.id)}
            >
              {t.form.name?.trim() || `Candidate ${i + 1}`}
            </button>
          ))}
        </div>
        <p className="helper-text" style={{ marginTop: 0 }}>
          Files: {active.files.join(", ") || "-"} &nbsp;|&nbsp; {activeIndex + 1} of {tabs.length} remaining
        </p>

        <form onSubmit={handleConfirm}>
          <CandidateFormFields form={active.form} set={set} />

          {error && <p style={{ color: "#c0392b", fontSize: "0.85rem" }}>{error}</p>}

          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel All Remaining
            </button>
            <button type="button" className="btn btn-secondary" onClick={handleSkip} disabled={saving}>
              Skip This One
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? "Saving..." : "Add Candidate"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
