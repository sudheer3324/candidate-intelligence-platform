import React from "react";
import { splitList, statusClass } from "../utils";

export default function CandidateTable({ candidates, onEdit, onDelete }) {
  if (candidates.length === 0) {
    return (
      <div className="empty-state card">
        <p>No candidates yet. Upload a resume/Naukri profile or add one manually to get started.</p>
      </div>
    );
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Contact</th>
            <th>Experience</th>
            <th>Current Role</th>
            <th>Domain</th>
            <th>Primary Skills</th>
            <th>CTC (LPA)</th>
            <th>Telugu</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {candidates.map((c) => (
            <tr key={c.id}>
              <td className="muted">{c.candidate_code}</td>
              <td><strong>{c.name}</strong></td>
              <td>
                <div>{c.email || "-"}</div>
                <div className="muted">{c.phone || ""}</div>
              </td>
              <td>{c.total_experience_years != null ? `${c.total_experience_years} yrs` : "-"}</td>
              <td>
                <div>{c.current_designation || "-"}</div>
                <div className="muted">{c.current_company || ""}</div>
              </td>
              <td className="muted">{c.domain || "-"}</td>
              <td>
                <div className="skills-cell">
                  {splitList(c.primary_skills).slice(0, 6).map((s) => (
                    <span className="chip" key={s}>{s}</span>
                  ))}
                </div>
              </td>
              <td>
                <div>{c.current_ctc_lpa ?? "-"}</div>
                {c.expected_ctc_lpa ? <div className="muted">exp {c.expected_ctc_lpa}</div> : null}
              </td>
              <td>{c.telugu === "Yes" ? "Yes" : "No"}</td>
              <td><span className={`pill ${statusClass(c.status)}`}>{c.status || "New"}</span></td>
              <td>
                <div className="row-actions">
                  <button className="icon-btn" onClick={() => onEdit(c)}>Edit</button>
                  <button className="icon-btn" onClick={() => onDelete(c)}>Delete</button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
