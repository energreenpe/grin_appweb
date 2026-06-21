import { create } from 'zustand';

// Estado del editor LIST (reemplaza el useState + history manual del LIST original).
// Las coordenadas de fields/overlays están en PDF points.

const clone = (arr) => JSON.parse(JSON.stringify(arr));

const initial = {
  doc: null,                 // { pdf_name, original_name }
  documentId: null,          // id del ListDocumento persistido (autoguardado)
  fields: [],
  overlays: [],
  selected: null,
  activeTool: 'select',      // select | text | overlay
  zoom: 1.0,
  currentPage: 1,
  numPages: 0,
  pageScale: { scaleX: 1, scaleY: 1 },
  history: [],
  historyIndex: -1,
};

export const useListStore = create((set, get) => ({
  ...initial,

  // ── Historial (undo/redo) ───────────────────────────────────────────────────
  _pushHistory: (fields, overlays) => set((s) => {
    const next = s.history.slice(0, s.historyIndex + 1);
    next.push({ fields: clone(fields), overlays: clone(overlays) });
    return { history: next, historyIndex: next.length - 1 };
  }),

  // ── Viewport / herramientas ─────────────────────────────────────────────────
  setActiveTool: (t) => set({ activeTool: t }),
  setZoom: (z) => set((s) => ({ zoom: typeof z === 'function' ? z(s.zoom) : z })),
  setCurrentPage: (p) => set((s) => ({ currentPage: typeof p === 'function' ? p(s.currentPage) : p })),
  setNumPages: (n) => set({ numPages: n }),
  setPageScale: (sc) => set({ pageScale: sc }),
  setSelected: (id) => set({ selected: id }),

  // ── Documento ─────────────────────────────────────────────────────────────--
  // Abre un documento persistido en el editor (con su avance). Asigna ids de cliente
  // a fields/overlays para selección/keying. `documentId` activa el autoguardado.
  openDocument: ({ id, nombre, pdf_name, fields = [], overlays = [] }) => {
    const f = fields.map((x, i) => ({ id: `field_${i}_${Date.now()}`, ...x }));
    const o = overlays.map((x, i) => ({ id: `overlay_${i}_${Date.now()}`, ...x }));
    set({
      doc: { pdf_name, original_name: nombre },
      documentId: id,
      fields: f,
      overlays: o,
      selected: null,
      activeTool: 'select',
      zoom: 1.0,
      currentPage: 1,
      numPages: 0,
      pageScale: { scaleX: 1, scaleY: 1 },
      history: [{ fields: clone(f), overlays: clone(o) }],
      historyIndex: 0,
    });
  },
  reset: () => set({ ...initial }),

  // ── Elementos ─────────────────────────────────────────────────────────────--
  addField: (pageIndex, x, y) => {
    const id = `field_${Date.now()}`;
    const nf = {
      id, page: pageIndex, x, y, width: 150, height: 24, text: '',
      font_family: 'Helvetica', font_size: 12, font_color: [0, 0, 0], bg_color: null,
    };
    const fields = [...get().fields, nf];
    set({ fields, selected: id, activeTool: 'select' });
    get()._pushHistory(fields, get().overlays);
  },
  addOverlay: (pageIndex, x, y) => {
    const id = `overlay_${Date.now()}`;
    const no = { id, page: pageIndex, x, y, width: 120, height: 30, color: [1, 1, 1] };
    const overlays = [...get().overlays, no];
    set({ overlays, selected: id, activeTool: 'select' });
    get()._pushHistory(get().fields, overlays);
  },
  updateField: (id, updates, commit = true) => {
    const fields = get().fields.map((f) => (f.id === id ? { ...f, ...updates } : f));
    set({ fields });
    if (commit) get()._pushHistory(fields, get().overlays);
  },
  updateOverlay: (id, updates, commit = true) => {
    const overlays = get().overlays.map((o) => (o.id === id ? { ...o, ...updates } : o));
    set({ overlays });
    if (commit) get()._pushHistory(get().fields, overlays);
  },
  deleteSelected: () => {
    const { selected, fields, overlays } = get();
    if (!selected) return;
    const nf = fields.filter((f) => f.id !== selected);
    const no = overlays.filter((o) => o.id !== selected);
    set({ fields: nf, overlays: no, selected: null });
    get()._pushHistory(nf, no);
  },

  // ── Undo / Redo ─────────────────────────────────────────────────────────────
  undo: () => {
    const { historyIndex, history } = get();
    if (historyIndex > 0) {
      const prev = history[historyIndex - 1];
      set({ fields: clone(prev.fields), overlays: clone(prev.overlays), historyIndex: historyIndex - 1, selected: null });
    }
  },
  redo: () => {
    const { historyIndex, history } = get();
    if (historyIndex < history.length - 1) {
      const nxt = history[historyIndex + 1];
      set({ fields: clone(nxt.fields), overlays: clone(nxt.overlays), historyIndex: historyIndex + 1, selected: null });
    }
  },

  // ── Plantillas ─────────────────────────────────────────────────────────────-
  loadTemplate: (fields, overlays) => {
    const f = (fields || []).map((x, i) => ({ id: `field_load_${i}_${Date.now()}`, ...x }));
    const o = (overlays || []).map((x, i) => ({ id: `overlay_load_${i}_${Date.now()}`, ...x }));
    set({ fields: f, overlays: o, selected: null });
    get()._pushHistory(f, o);
  },
}));
