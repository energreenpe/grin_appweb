import { api, SERVER_BASE } from '../../../lib/api';

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export const listApi = {
  // ── Subida + conversión (async vía worker) ─────────────────────────────────
  upload: async (file) => {
    const fd = new FormData();
    fd.append('file', file);
    const res = await api.post('/list/upload', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data; // { job_id, status, pdf_name, pdf_url }
  },

  jobStatus: async (jobId) => (await api.get(`/list/jobs/${jobId}`)).data,

  /** Polling de un job hasta finished/failed. Devuelve el JobStatusOut final. */
  pollJob: async (jobId, { intervalMs = 1200, timeoutMs = 120000 } = {}) => {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      const j = await listApi.jobStatus(jobId);
      if (j.status === 'finished') return j;
      if (j.status === 'failed') throw new Error(j.error || 'La tarea falló.');
      await sleep(intervalMs);
    }
    throw new Error('Tiempo de espera agotado esperando el documento.');
  },

  // ── Estampado / exportación (async vía worker) ─────────────────────────────
  export: async (payload) => (await api.post('/list/export', payload)).data, // { job_id, status }

  /** URL absoluta del PDF base servido por el backend (para react-pdf). */
  pdfSrc: (pdfName) => `${SERVER_BASE}/api/list/pdf/${pdfName}`,

  /** Descarga el PDF estampado del /output. */
  downloadOutput: async (outputName, downloadName = 'LIST_editado.pdf') => {
    const res = await api.get(`/list/output/${outputName}`, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', downloadName);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  // ── Plantillas (PostgreSQL) ────────────────────────────────────────────────
  saveTemplate: async (payload) => (await api.post('/list/templates', payload)).data,
  listTemplates: async () => (await api.get('/list/templates')).data,
  getTemplate: async (id) => (await api.get(`/list/templates/${id}`)).data,
  deleteTemplate: async (id) => (await api.delete(`/list/templates/${id}`)).data,

  // ── Documentos (persistencia + resume) ─────────────────────────────────────
  createDocumento: async (payload) => (await api.post('/list/documentos', payload)).data,
  listDocumentos: async () => (await api.get('/list/documentos')).data,
  getDocumento: async (id) => (await api.get(`/list/documentos/${id}`)).data,
  updateDocumento: async (id, payload) => (await api.put(`/list/documentos/${id}`, payload)).data,
  deleteDocumento: async (id) => (await api.delete(`/list/documentos/${id}`)).data,
};
