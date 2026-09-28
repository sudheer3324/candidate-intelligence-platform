export const STATUS_OPTIONS = [
  "New", "Screened", "Submitted", "Interviewing", "Offered", "Placed", "Rejected", "On Hold",
];

export function statusClass(status) {
  return (status || "New").replace(/\s+/g, "");
}

export function splitList(text) {
  return (text || "")
    .split(/;|\n/)
    .map((s) => s.trim())
    .filter(Boolean);
}

export function chunkLabel(type) {
  return {
    overview: "Overview",
    work_history: "Work History",
    skills: "Skills & Certifications",
    projects_achievements: "Projects & Achievements",
  }[type] || type;
}
