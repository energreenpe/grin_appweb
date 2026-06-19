import { api } from '../../../lib/api';

export const mathApi = {
  // ── Catálogos ──────────────────────────────────────────────
  getRegiones: async () => (await api.get('/math/regiones')).data,
  getEquipos: async (tipo) =>
    (await api.get('/math/equipos', { params: tipo ? { tipo } : {} })).data,
  getElectrodomesticos: async () => (await api.get('/math/electrodomesticos')).data,
  getIngenieros: async () => (await api.get('/math/ingenieros')).data,

  // ── Clientes (delegado a shared en el backend) ─────────────
  searchClientes: async (q) =>
    (await api.get('/math/clientes/search', { params: { q } })).data,
  createCliente: async (data) => (await api.post('/math/clientes', data)).data,

  // ── Cálculos (CRUD + motor) ────────────────────────────────
  getCalculos: async (params) => (await api.get('/math/calculos', { params })).data,
  getCalculo: async (id) => (await api.get(`/math/calculos/${id}`)).data,
  createCalculo: async (data) => (await api.post('/math/calculos', data)).data,
  updateCalculo: async (id, data) => (await api.put(`/math/calculos/${id}`, data)).data,
  deleteCalculo: async (id) => (await api.delete(`/math/calculos/${id}`)).data,
  calcularCalculo: async (id) => (await api.post(`/math/calculos/${id}/calcular`)).data,
  completarCalculo: async (id) => (await api.post(`/math/calculos/${id}/completar`)).data,
};
