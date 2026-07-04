import { api } from '../../../lib/api';

export const inspectorApi = {
  getVisitas: async (params) => {
    const res = await api.get('/inspector/visitas', { params });
    return res.data;
  },
  getVisita: async (id) => {
    const res = await api.get(`/inspector/visitas/${id}`);
    return res.data;
  },
  createVisita: async (data) => {
    const res = await api.post('/inspector/visitas', data);
    return res.data;
  },
  updateVisita: async (id, data) => {
    const res = await api.put(`/inspector/visitas/${id}`, data);
    return res.data;
  },
  completarVisita: async (id) => {
    const res = await api.post(`/inspector/visitas/${id}/completar`);
    return res.data;
  },
  cancelarVisita: async (id) => {
    const res = await api.delete(`/inspector/visitas/${id}`);
    return res.data;
  },
  uploadFotoTecho: async (id, file) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post(`/inspector/visitas/${id}/fotos-techo`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
  },
  uploadFotoInterior: async (id, file) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post(`/inspector/visitas/${id}/fotos-interior`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
  },
  uploadRecibo: async (id, file) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post(`/inspector/visitas/${id}/recibo`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
  },
  deleteFotoTecho: async (id, index) => {
    const res = await api.delete(`/inspector/visitas/${id}/fotos-techo/${index}`);
    return res.data;
  },
  deleteFotoInterior: async (id, index) => {
    const res = await api.delete(`/inspector/visitas/${id}/fotos-interior/${index}`);
    return res.data;
  },
  searchClientes: async (q) => {
    const res = await api.get('/inspector/clientes/search', { params: { q } });
    return res.data;
  },
  createCliente: async (data) => {
    const res = await api.post('/inspector/clientes', data);
    return res.data;
  },
  getTecnicos: async () => {
    const res = await api.get('/inspector/tecnicos');
    return res.data;
  },
  geocodeReverse: async (lat, lng) => {
    const res = await api.get('/inspector/geocode/reverse', { params: { lat, lng } });
    return res.data;
  },
  downloadPdf: async (id, filename) => {
    const res = await api.get(`/inspector/visitas/${id}/pdf`, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename || `visita_${id}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  }
};
