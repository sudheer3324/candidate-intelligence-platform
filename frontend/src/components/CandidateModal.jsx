import React, { useState } from "react";
import CandidateFormFields, { EMPTY_CANDIDATE, toPayload } from "./CandidateFormFields";

export default function CandidateModal({ initial, onClose, onSave }) {
  const [form, setForm] = useState(() => ({ ...EMPTY_CANDIDATE, ...(initial || {}) }));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const isEdit = Boolean(initial?.id);

  function set(key, value) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await onSave(toPayload(form));
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="modal-overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <h2>{isEdit ? `Edit ${form.name || "Candidate"}` : "Add Candidate"}</h2>
        <form onSubmit={handleSubmit}>
          <CandidateFormFields form={form} set={set} />

          {error && <p style={{ color: "#c0392b", fontSize: "0.85rem" }}>{error}</p>}

          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? "Saving..." : isEdit ? "Save Changes" : "Add Candidate"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
