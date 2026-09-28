import React from "react";
import { STATUS_OPTIONS } from "../utils";

export const EMPTY_CANDIDATE = {
  name: "", email: "", phone: "", current_location: "", preferred_locations: "",
  total_experience_years: "", current_company: "", current_designation: "",
  current_role_since: "", current_ctc_lpa: "", expected_ctc_lpa: "", notice_period: "",
  domain: "", primary_skills: "", all_skills: "", certifications: "",
  highest_education: "", education_details: "", work_history: "", total_companies: "",
  previous_companies: "", key_projects_clients: "", achievements: "", languages_known: "",
  telugu: "No",
  date_of_birth: "", gender: "", marital_status: "", work_authorization: "",
  profile_summary: "", recruiter_notes: "", status: "New", source_files: "",
};

export const NUMERIC_FIELDS = new Set([
  "total_experience_years", "current_ctc_lpa", "expected_ctc_lpa", "total_companies",
]);

/** Coerce a raw form object into the shape the API expects (numbers as numbers, name required). */
export function toPayload(form) {
  const payload = { ...form };
  for (const key of NUMERIC_FIELDS) {
    payload[key] = payload[key] === "" || payload[key] === null ? null : Number(payload[key]);
  }
  if (!payload.name?.trim()) throw new Error("Name is required.");
  return payload;
}

/** The full set of candidate fields, reused by the single Add/Edit modal and the
 * multi-candidate (tabbed bulk-upload) modal so both stay in sync automatically. */
export default function CandidateFormFields({ form, set }) {
  const Field = ({ label, k, type = "text", full = false, textarea = false, options = null }) => (
    <div className={full ? "full" : ""}>
      <label>{label}</label>
      {options ? (
        <select value={form[k] ?? ""} onChange={(e) => set(k, e.target.value)}>
          {options.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
      ) : textarea ? (
        <textarea value={form[k] ?? ""} onChange={(e) => set(k, e.target.value)} />
      ) : (
        <input
          type={type}
          value={form[k] ?? ""}
          onChange={(e) => set(k, e.target.value)}
          step={type === "number" ? "0.1" : undefined}
        />
      )}
    </div>
  );

  return (
    <>
      <div className="section-title">Basic Info</div>
      <div className="form-grid">
        <Field label="Full Name *" k="name" />
        <Field label="Status" k="status" options={STATUS_OPTIONS} />
        <Field label="Email" k="email" type="email" />
        <Field label="Phone" k="phone" />
        <Field label="Current Location" k="current_location" />
        <Field label="Preferred Locations" k="preferred_locations" />
      </div>

      <div className="section-title">Current Role & Compensation</div>
      <div className="form-grid">
        <Field label="Total Experience (Yrs)" k="total_experience_years" type="number" />
        <Field label="Current Company" k="current_company" />
        <Field label="Current Designation" k="current_designation" />
        <Field label="Current Role Since" k="current_role_since" />
        <Field label="Current CTC (LPA)" k="current_ctc_lpa" type="number" />
        <Field label="Expected CTC (LPA)" k="expected_ctc_lpa" type="number" />
        <Field label="Notice Period" k="notice_period" />
        <Field label="Domain / Specialization" k="domain" />
      </div>

      <div className="section-title">Skills & Education</div>
      <div className="form-grid">
        <Field label="Primary Skills (separate with ;)" k="primary_skills" full textarea />
        <Field label="All Skills (separate with ;)" k="all_skills" full textarea />
        <Field label="Certifications (separate with ;)" k="certifications" full textarea />
        <Field label="Highest Education" k="highest_education" />
        <Field label="No. of Companies Worked" k="total_companies" type="number" />
        <Field label="Education Details" k="education_details" full textarea />
      </div>

      <div className="section-title">Experience & Projects</div>
      <div className="form-grid">
        <Field label="Work History (one per line)" k="work_history" full textarea />
        <Field label="Previous Companies (separate with ;)" k="previous_companies" full />
        <Field label="Key Projects / Clients" k="key_projects_clients" full textarea />
        <Field label="Achievements / Highlights" k="achievements" full textarea />
        <Field label="Profile Summary" k="profile_summary" full textarea />
      </div>

      <div className="section-title">Personal & Notes</div>
      <div className="form-grid">
        <Field label="Languages Known" k="languages_known" />
        <Field label="Telugu" k="telugu" options={["No", "Yes"]} />
        <Field label="Work Authorization / Visa" k="work_authorization" />
        <Field label="Date of Birth" k="date_of_birth" />
        <Field label="Gender" k="gender" />
        <Field label="Marital Status" k="marital_status" />
        <Field label="Recruiter Notes" k="recruiter_notes" full textarea />
      </div>
    </>
  );
}
