const BASE = "/api";

async function handle(res) {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch (_) {}
    throw new Error(detail || `Request failed (${res.status})`);
  }
  return res.status === 204 ? null : res.json();
}

export const api = {
  listCandidates: () => fetch(`${BASE}/candidates`).then(handle),

  getCandidate: (id) => fetch(`${BASE}/candidates/${id}`).then(handle),

  createCandidate: (data) =>
    fetch(`${BASE}/candidates`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }).then(handle),

  updateCandidate: (id, data) =>
    fetch(`${BASE}/candidates/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }).then(handle),

  deleteCandidate: (id) =>
    fetch(`${BASE}/candidates/${id}`, { method: "DELETE" }).then(handle),

  // Extraction only - does NOT save anything. Returns { candidates, errors } where
  // `candidates` is a list of { data, files } - one per distinct candidate detected
  // across all uploaded files (files for the same person are merged automatically).
  extractResumes: (files) => {
    const form = new FormData();
    for (const f of files) form.append("files", f);
    return fetch(`${BASE}/candidates/extract`, { method: "POST", body: form }).then(handle);
  },

  downloadExcelUrl: () => `${BASE}/candidates/export/excel`,

  chat: (question, top_k = 8) =>
    fetch(`${BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, top_k }),
    }).then(handle),
};
