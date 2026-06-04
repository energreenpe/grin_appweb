import { api } from '../../../lib/api';

export const quoteApi = {
  // Productos
  getProducts: async (search = '') => {
    const res = await api.get('/quote/products', { params: { search } });
    return res.data;
  },
  createProduct: async (data) => {
    const res = await api.post('/quote/products', data);
    return res.data;
  },
  updateProduct: async (id, data) => {
    const res = await api.put(`/quote/products/${id}`, data);
    return res.data;
  },
  deleteProduct: async (id) => {
    const res = await api.delete(`/quote/products/${id}`);
    return res.data;
  },

  // Cotizaciones
  getCotizaciones: async () => {
    const res = await api.get('/quote/cotizaciones');
    return res.data;
  },
  
  getCotizacion: async (id) => {
    const res = await api.get(`/quote/cotizaciones/${id}`);
    return res.data;
  },
  
  createCotizacion: async (data) => {
    const res = await api.post('/quote/cotizaciones', data);
    return res.data;
  },
  
  updateCotizacion: async (id, data) => {
    const res = await api.put(`/quote/cotizaciones/${id}`, data);
    return res.data;
  },
  
  deleteCotizacion: async (id) => {
    await api.delete(`/quote/cotizaciones/${id}`);
  },

  // Ítems
  addItem: async (cotizacionId, item) => {
    const res = await api.post(`/quote/cotizaciones/${cotizacionId}/items`, item);
    return res.data;
  },
  
  removeItem: async (cotizacionId, itemId) => {
    const res = await api.delete(`/quote/cotizaciones/${cotizacionId}/items/${itemId}`);
    return res.data;
  },
  
  reorderItems: async (cotizacionId, itemIds) => {
    const res = await api.put(`/quote/cotizaciones/${cotizacionId}/items/reorder`, { item_ids: itemIds });
    return res.data;
  },
  
  updateItem: async (cotizacionId, itemId, data) => {
    const res = await api.put(`/quote/cotizaciones/${cotizacionId}/items/${itemId}`, data);
    return res.data;
  },
  
  deleteItem: async (cotizacionId, itemId) => {
    await api.delete(`/quote/cotizaciones/${cotizacionId}/items/${itemId}`);
  },

  // PDF
  downloadPdf: async (id, filename) => {
    const res = await api.get(`/quote/cotizaciones/${id}/pdf`, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename || `cotizacion_${id}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  },

  // Empresa
  getEmpresa: async () => {
    const res = await api.get('/quote/empresa');
    return res.data;
  },
  
  updateEmpresa: async (data) => {
    const res = await api.put('/quote/empresa', data);
    return res.data;
  },
  
  uploadLogo: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post('/quote/empresa/logo', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
  },

  // Vendedores
  getVendedores: async () => {
    const res = await api.get('/quote/vendedores');
    return res.data;
  },

  // Clientes
  getClientes: async (search = '') => {
    const res = await api.get(`/quote/clientes?search=${search}`);
    return res.data;
  },

  createCliente: async (data) => {
    const res = await api.post('/quote/clientes', data);
    return res.data;
  },

  // Plantillas Globales
  getPlantillas: async () => {
    const res = await api.get('/quote/plantillas');
    return res.data;
  },
  
  updatePlantillas: async (data) => {
    const res = await api.put('/quote/plantillas', data);
    return res.data;
  }
};
