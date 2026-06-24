import { create } from 'zustand';

export const usePlannerStore = create((set) => ({
  proyectos: [],
  proyectoActivo: null,
  kpis: null,
  filtroEstado: null,

  setProyectos: (d) => set({ proyectos: d }),
  setProyectoActivo: (d) => set({ proyectoActivo: d }),
  setKpis: (d) => set({ kpis: d }),
  setFiltroEstado: (d) => set({ filtroEstado: d }),
  reset: () => set({ proyectoActivo: null }),
}));
