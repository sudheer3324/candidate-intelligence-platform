import React, { useRef, useState } from "react";
import { api } from "../api";

export default function UploadPanel({ onClose, onExtracted }) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  async function handleFiles(fileList) {
    const files = Array.from(fileList || []);
    if (files.length === 0) return;
    setUploading(true);
    setError(null);
    try {
      const res = await api.extractResumes(files);
      if (res.errors?.length) {
        const msg = res.errors.map((e) => `${e.filename}: ${e.message}`).join("; ");
        setError(`Some files could not be read - ${msg}`);
      }
      if (!res.candidates?.length) return;
      // Hand the extracted, grouped-by-candidate data to the parent, which opens
      // one Add Candidate tab per candidate found. Nothing is saved yet.
      onExtracted(res.candidates);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="modal-overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" style={{ maxWidth: 560 }}>
        <h2>Upload Resumes / Naukri Profiles</h2>
        <p className="helper-text">
          Upload documents for one candidate (e.g. their resume + their Naukri profile export -
          these get merged into one record) or for several different candidates at once (each
          person gets their own tab). Gemini extracts the details and opens the Add Candidate
          form pre-filled per candidate for you to review and edit - nothing is added to the
          database until you confirm each one.
        </p>
        <div
          className={`dropzone ${dragging ? "drag" : ""}`}
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            handleFiles(e.dataTransfer.files);
          }}
        >
          {uploading ? "Reading and extracting with Gemini..." : "Click to choose files, or drag & drop here"}
          <input
            ref={inputRef}
            type="file"
            multiple
            accept=".pdf,.docx,.txt"
            style={{ display: "none" }}
            onChange={(e) => handleFiles(e.target.files)}
          />
        </div>

        {error && <p style={{ color: "#c0392b", fontSize: "0.85rem", marginTop: 12 }}>{error}</p>}

        <div className="modal-actions">
          <button className="btn btn-secondary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}
