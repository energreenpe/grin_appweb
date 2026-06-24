import { api, SERVER_BASE } from '../../../lib/api';

// ── KPIs ──
export const getKpis           = ()            => api.get('/planner/kpis');

// ── Proyectos ──
export const getProyectos      = (p)           => api.get('/planner/proyectos', { params: p });
export const getProyecto       = (id)          => api.get(`/planner/proyectos/${id}`);
export const createProyecto    = (d)           => api.post('/planner/proyectos', d);
export const updateProyecto    = (id, d)       => api.patch(`/planner/proyectos/${id}`, d);
export const deleteProyecto    = (id)          => api.delete(`/planner/proyectos/${id}`);

// ── Personal ──
export const getPersonal       = (p)           => api.get('/planner/personal', { params: p });
export const createPersona     = (d)           => api.post('/planner/personal', d);
export const updatePersona     = (id, d)       => api.patch(`/planner/personal/${id}`, d);
export const deletePersona     = (id)          => api.delete(`/planner/personal/${id}`);

// ── Cuadrillas + miembros ──
export const getCuadrillas     = (pid)         => api.get(`/planner/proyectos/${pid}/cuadrillas`);
export const createCuadrilla   = (d)           => api.post('/planner/cuadrillas', d);
export const updateCuadrilla   = (id, d)       => api.patch(`/planner/cuadrillas/${id}`, d);
export const deleteCuadrilla   = (id)          => api.delete(`/planner/cuadrillas/${id}`);
export const asignarMiembro    = (cid, d)      => api.post(`/planner/cuadrillas/${cid}/miembros`, d);
export const cambiarCuadrilla  = (mid, d)      => api.post(`/planner/miembros/${mid}/cambiar-cuadrilla`, d);
export const removerMiembro    = (mid)         => api.delete(`/planner/miembros/${mid}`);

// ── Actividades / Gantt ──
export const getActividades    = (pid, p)      => api.get(`/planner/proyectos/${pid}/actividades`, { params: p });
export const createActividad   = (d)           => api.post('/planner/actividades', d);
export const updateActividad   = (id, d)       => api.patch(`/planner/actividades/${id}`, d);
export const deleteActividad   = (id)          => api.delete(`/planner/actividades/${id}`);
export const recalcularGantt   = (pid)         => api.post(`/planner/proyectos/${pid}/recalcular-gantt`);

// ── Feriados ──
export const getFeriados       = (anio, region)=> api.get('/planner/feriados', { params: { anio, region } });
export const createFeriado     = (d)           => api.post('/planner/feriados', d);
export const deleteFeriado     = (id)          => api.delete(`/planner/feriados/${id}`);

// ── Curva S ──
export const getCurvaS         = (pid)         => api.get(`/planner/proyectos/${pid}/curva-s`);
export const snapshotCurvaS    = (pid)         => api.post(`/planner/proyectos/${pid}/curva-s/snapshot`);

// ── Asistencia ──
export const getAsistencia     = (pid, p)      => api.get(`/planner/proyectos/${pid}/asistencia`, { params: p });
export const createAsistencia  = (d)           => api.post('/planner/asistencia', d);
export const bulkAsistencia    = (d)           => api.post('/planner/asistencia/bulk', d);
export const deleteAsistencia  = (id)          => api.delete(`/planner/asistencia/${id}`);

// ── Fotos (evidencia) ──
export const getFotos          = (pid, p)      => api.get(`/planner/proyectos/${pid}/fotos`, { params: p });
export const uploadFoto        = (pid, form)   => api.post(`/planner/proyectos/${pid}/fotos`, form, { headers: { 'Content-Type': 'multipart/form-data' } });
export const updateFoto        = (id, d)       => api.patch(`/planner/fotos/${id}`, d);
export const deleteFoto        = (id)          => api.delete(`/planner/fotos/${id}`);

// ── Reportes PDF (descarga blob) ──
export const descargarPdf = async (pid, tipoPdf, params) => {
  // tipoPdf: 'cliente' | 'oficina'. Devuelve un Blob de PDF.
  const res = await api.get(`/planner/proyectos/${pid}/pdf/${tipoPdf}`, {
    params,
    responseType: 'blob',
  });
  return res.data;
};
