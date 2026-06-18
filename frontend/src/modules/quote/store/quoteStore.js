import { create } from 'zustand';
import { quoteApi } from '../api/quoteApi';
import { notify } from '../../../lib/notify';

const NET_SAVE_ERR = 'No se pudieron guardar los cambios. Revisa tu conexión.';

const SAVE_DELAY = 600; // ms de inactividad antes de persistir

// Estado de debounce a nivel de módulo (no reactivo). Acumula los cambios y los
// envía en una sola petición cuando el usuario hace una pausa al escribir.
let headerTimer = null;
let headerPending = {};
const itemTimers = {};
const itemPending = {};

const EMPTY_TOTALES = { subtotal: 0, igv: 0, total: 0, por_particion: {} };

// Fusiona los subtotales calculados por el servidor en los ítems locales sin pisar
// los campos editables (el usuario pudo seguir escribiendo mientras se guardaba).
function applyComputed(localItems, serverItems) {
  if (!serverItems) return localItems;
  const byId = {};
  for (const i of serverItems) byId[i.id] = i;
  return localItems.map(li => (byId[li.id] ? { ...li, subtotal: byId[li.id].subtotal } : li));
}

export const useQuoteStore = create((set, get) => ({
  cotizacion: null,
  items: [],
  totales: EMPTY_TOTALES,
  loading: false,
  error: null,

  // Subidas de logo en curso (bancos + empresa). Mientras sea > 0 se bloquea el PDF
  // para que no salga con el logo anterior.
  logoUploads: 0,
  beginLogoUpload: () => set(s => ({ logoUploads: s.logoUploads + 1 })),
  endLogoUpload: () => set(s => ({ logoUploads: Math.max(0, s.logoUploads - 1) })),

  loadCotizacion: async (id) => {
    set({ loading: true, error: null });
    try {
      const data = await quoteApi.getCotizacion(id);
      set({
        cotizacion: data,
        items: data.items || [],
        totales: data.totales || EMPTY_TOTALES,
        loading: false,
      });
    } catch (err) {
      set({ error: err.message, loading: false });
      notify('No se pudo cargar la cotización. Revisa tu conexión.');
    }
  },

  // ── Cabecera / condiciones: actualización optimista + guardado con debounce ──
  updateHeader: (id, data) => {
    set(state => ({ cotizacion: { ...state.cotizacion, ...data } }));
    headerPending = { ...headerPending, ...data };
    clearTimeout(headerTimer);
    headerTimer = setTimeout(() => get()._flushHeader(id), SAVE_DELAY);
  },

  _flushHeader: async (id) => {
    clearTimeout(headerTimer);
    if (Object.keys(headerPending).length === 0) return;
    const payload = headerPending;
    headerPending = {};
    try {
      const updated = await quoteApi.updateCotizacion(id, payload);
      // Solo tomamos del servidor lo CALCULADO (totales y subtotales); los campos
      // editables siguen siendo los locales para no pisar lo que el usuario teclea.
      set(state => ({
        totales: updated.totales,
        items: applyComputed(state.items, updated.items),
      }));
    } catch (err) {
      console.error(err);
      // Devolvemos lo pendiente a la cola para reintentar en el próximo cambio.
      headerPending = { ...payload, ...headerPending };
      notify(NET_SAVE_ERR);
    }
  },

  // ── Edición de un ítem: optimista + guardado con debounce (por ítem) ─────────
  updateItem: (cotizacionId, itemId, data) => {
    set(state => ({
      items: state.items.map(i => (i.id === itemId ? { ...i, ...data } : i)),
    }));
    itemPending[itemId] = { ...(itemPending[itemId] || {}), ...data };
    clearTimeout(itemTimers[itemId]);
    itemTimers[itemId] = setTimeout(() => get()._flushItem(cotizacionId, itemId), SAVE_DELAY);
  },

  _flushItem: async (cotizacionId, itemId) => {
    clearTimeout(itemTimers[itemId]);
    const payload = itemPending[itemId];
    if (!payload) return;
    delete itemPending[itemId];
    try {
      const updated = await quoteApi.updateItem(cotizacionId, itemId, payload);
      set(state => ({
        totales: updated.totales,
        items: applyComputed(state.items, updated.items),
      }));
    } catch (err) {
      console.error(err);
      // Devolvemos lo pendiente a la cola para reintentar en el próximo cambio.
      itemPending[itemId] = { ...payload, ...(itemPending[itemId] || {}) };
      notify(NET_SAVE_ERR);
    }
  },

  // Fuerza el guardado de TODO lo pendiente. Llamar antes de generar PDF,
  // cambiar de estado o salir del editor, para no perder lo último tecleado.
  flushPending: async () => {
    const id = get().cotizacion?.id;
    if (!id) return;
    const tasks = [];
    if (Object.keys(headerPending).length > 0) tasks.push(get()._flushHeader(id));
    for (const itemId of Object.keys(itemPending)) tasks.push(get()._flushItem(id, Number(itemId)));
    await Promise.all(tasks);
  },

  changeEstado: async (id, estado) => {
    await get().flushPending();
    try {
      const updated = await quoteApi.changeEstado(id, estado);
      set({ cotizacion: updated, items: updated.items || [], totales: updated.totales });
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
        particion,
        subparticion,
        orden: get().items.length,
      };
      await quoteApi.addItem(cotizacionId, newItem);
      // Recarga puntual (acción discreta, no por tecla) para traer el ítem nuevo.
      await get().loadCotizacion(cotizacionId);
    } catch (err) {
      console.error(err);
      notify('No se pudo agregar el ítem. Revisa tu conexión.');
    }
  },

  reorderItems: async (cotizacionId, itemIds) => {
    try {
      const { items } = get();
      const newItems = itemIds.map(id => items.find(i => i.id === id)).filter(Boolean);
      set({ items: newItems }); // optimista
      const updatedCot = await quoteApi.reorderItems(cotizacionId, itemIds);
      set({
        items: updatedCot.items.sort((a, b) => a.orden - b.orden),
        totales: updatedCot.totales,
      });
    } catch (err) {
      console.error('Error reordering items:', err);
      notify('No se pudo reordenar los ítems. Revisa tu conexión.');
      await get().loadCotizacion(cotizacionId);
    }
  },

  removeItem: async (cotizacionId, itemId) => {
    // Cancela cualquier guardado pendiente de ese ítem antes de borrarlo.
    clearTimeout(itemTimers[itemId]);
    delete itemPending[itemId];
    try {
      await quoteApi.deleteItem(cotizacionId, itemId);
      await get().loadCotizacion(cotizacionId);
    } catch (err) {
      console.error(err);
      notify('No se pudo eliminar el ítem. Revisa tu conexión.');
    }
  },
}));
