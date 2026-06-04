import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

const initialData = {
  tipo_cliente: null,
  cliente_id: null,
  cliente_info: null, // Solo para UI
  tecnico_id: null,
  tecnico_info: null, // Solo para UI
  lat: null,
  lng: null,
  tipo_sistema: null,
  conexion_red: null,
  cargas_aislado: [],
  tipo_techo: null,
  obs_techo: '',
  obs_interior: '',
  fotos_techo: [],
  fotos_interior: [],
  recibo_ruta: null,
  notas: ''
};

// Pasos válidos del wizard (exportado para validación en WizardPage)
export const VALID_STEPS = [
  'inicio', 'tipo_sistema', 'conexion_red', 'recibo_luz',
  'cargas_criticas', 'tipo_techo', 'fotos_techo', 'fotos_interior', 'done'
];

export const useWizardStore = create(
  persist(
    (set, get) => ({
      visitaId: null,
      currentStep: 'inicio',
      stepHistory: [],
      data: { ...initialData },

      setData: (partial) => set((state) => ({
        data: { ...state.data, ...partial }
      })),

      setVisitaId: (id) => set({ visitaId: id }),

      goToStep: (step) => set((state) => ({
        currentStep: step,
        stepHistory: [...state.stepHistory, state.currentStep]
      })),

      goBack: () => set((state) => {
        const history = [...state.stepHistory];
        const prev = history.pop();
        return {
          currentStep: prev || 'inicio',
          stepHistory: history
        };
      }),

      reset: () => set({
        visitaId: null,
        currentStep: 'inicio',
        stepHistory: [],
        data: { ...initialData }
      })
    }),
    {
      name: 'inspector-wizard-storage',
      storage: createJSONStorage(() => localStorage),
      version: 2, // Incrementar versión invalida el estado guardado con pasos obsoletos
      migrate: (persistedState, version) => {
        // Si el paso guardado no es válido (ej: 'tipo_cliente' antiguo), resetear
        if (!VALID_STEPS.includes(persistedState?.currentStep)) {
          return {
            visitaId: null,
            currentStep: 'inicio',
            stepHistory: [],
            data: { ...initialData }
          };
        }
        return persistedState;
      },
    }
  )
);
