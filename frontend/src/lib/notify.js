import { create } from 'zustand';

// Sistema de avisos (toasts) ligero y global. Reemplaza los alert()/console.error
// silenciosos para dar feedback claro ante fallos de red u otras acciones.
let nextId = 1;

export const useNotify = create((set, get) => ({
  toasts: [],

  notify: (message, type = 'error', timeout = 4500) => {
    // Evita duplicados (ej. fallos de guardado repetidos mientras no hay red).
    const existing = get().toasts.find(t => t.message === message);
    if (existing) return existing.id;

    const id = nextId++;
    set(state => ({ toasts: [...state.toasts, { id, message, type }] }));
    if (timeout) setTimeout(() => get().dismiss(id), timeout);
    return id;
  },

  dismiss: (id) => set(state => ({ toasts: state.toasts.filter(t => t.id !== id) })),
}));

// Helper para usar fuera de componentes (p. ej. dentro de stores).
export const notify = (message, type, timeout) =>
  useNotify.getState().notify(message, type, timeout);
