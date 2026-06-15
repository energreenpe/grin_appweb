import { create } from 'zustand';
import { quoteApi } from '../api/quoteApi';

export const useQuoteStore = create((set, get) => ({
  cotizacion: null,
  items: [],
  totales: { subtotal: 0, igv: 0, total: 0, por_particion: {} },
  loading: false,
  error: null,

  loadCotizacion: async (id) => {
    set({ loading: true, error: null });
    try {
      const data = await quoteApi.getCotizacion(id);
      set({ 
        cotizacion: data, 
        items: data.items || [], 
        totales: data.totales || { subtotal: 0, igv: 0, total: 0, por_particion: {} },
        loading: false 
      });
    } catch (err) {
      set({ error: err.message, loading: false });
    }
  },

  updateHeader: async (id, data) => {
    try {
      const updated = await quoteApi.updateCotizacion(id, data);
      set({
        cotizacion: updated,
        items: updated.items || [],   // subtotales reconvertidos (moneda/TC/margen)
        totales: updated.totales
      });
    } catch (err) {
      console.error(err);
    }
  },

  changeEstado: async (id, estado) => {
    try {
      const updated = await quoteApi.changeEstado(id, estado);
      set({
        cotizacion: updated,
        items: updated.items || [],
        totales: updated.totales
      });
      return { ok: true };
    } catch (err) {
      const error = err?.response?.data?.detail || 'No se pudo cambiar el estado';
      return { ok: false, error };
    }
  },

  addItem: async (cotizacionId, product, qty = 1, particion = 'Principal', subparticion = null) => {
    try {
      const newItem = {
        producto_id: product.id,
        nombre: product.nombre,
        descripcion: product.descripcion,
        marca: product.marca,
        unidad: product.unidad,
        cantidad: qty,
        precio_unit: product.precio,
        moneda: product.moneda,
        particion: particion,
        subparticion: subparticion,
        orden: get().items.length
      };
      const added = await quoteApi.addItem(cotizacionId, newItem);
      
      // Reload para obtener totales actualizados del backend
      await get().loadCotizacion(cotizacionId);
    } catch (err) {
      console.error(err);
    }
  },

  reorderItems: async (cotizacionId, itemIds) => {
    try {
      // Optimistic update
      const { items } = get();
      const newItems = itemIds.map(id => items.find(i => i.id === id)).filter(Boolean);
      set({ items: newItems });
      
      const updatedCot = await quoteApi.reorderItems(cotizacionId, itemIds);
      set({ 
        items: updatedCot.items.sort((a, b) => a.orden - b.orden),
        totales: updatedCot.totales 
      });
    } catch (err) {
      console.error("Error reordering items:", err);
      // Revert on error by reloading
      await get().loadCotizacion(cotizacionId);
    }
  },

  removeItem: async (cotizacionId, itemId) => {
    try {
      await quoteApi.deleteItem(cotizacionId, itemId);
      await get().loadCotizacion(cotizacionId);
    } catch (err) {
      console.error(err);
    }
  },

  updateItem: async (cotizacionId, itemId, data) => {
    try {
      await quoteApi.updateItem(cotizacionId, itemId, data);
      await get().loadCotizacion(cotizacionId);
    } catch (err) {
      console.error(err);
    }
  }
}));
