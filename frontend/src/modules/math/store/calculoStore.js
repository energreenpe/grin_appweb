import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { STEP_ORDER } from '../wizardSteps';

const initialData = {
  // Paso inicio
  nombre_proyecto: '',
  tipo_cliente: null,
  cliente_id: null,
  cliente_info: null,   // solo UI
  ingeniero_id: null,
  ingeniero_info: null, // solo UI
  region: null,
  tipo_sistema: null,
  // Entrada del Aislado
  cargas: [],
  dias_autonomia: 2,
  tipo_hsp: 'promedio',
  tipo_bateria: 'Lead acid',  // se deriva de la batería elegida
  panel_id: null,
  panel_info: null,
  bateria_id: null,
  bateria_info: null,
  voltaje_sistema: null,      // null = automático
  // Resultado del motor
  resultado: null,
};

export const VALID_STEPS = STEP_ORDER;

export const useCalculoStore = create(
  persist(
    (set, get) => ({
      calculoId: null,
      currentStep: 'inicio',
      stepHistory: [],
      data: { ...initialData },

      setData: (partial) => set((s) => ({ data: { ...s.data, ...partial } })),
      setCalculoId: (id) => set({ calculoId: id }),

      goToStep: (step) => set((s) => ({
        currentStep: step,
        stepHistory: [...s.stepHistory, s.currentStep],
      })),

      goBack: () => set((s) => {
        const history = [...s.stepHistory];
        const prev = history.pop();
        return { currentStep: prev || 'inicio', stepHistory: history };
      }),

      resumeAt: (step, history = []) => set({ currentStep: step, stepHistory: history }),

      reset: () => set({
        calculoId: null,
        currentStep: 'inicio',
        stepHistory: [],
        data: { ...initialData },
      }),
    }),
    {
      name: 'math-calculo-storage',
      storage: createJSONStorage(() => localStorage),
      version: 1,
      migrate: (persisted) => {
        if (!VALID_STEPS.includes(persisted?.currentStep)) {
          return { calculoId: null, currentStep: 'inicio', stepHistory: [], data: { ...initialData } };
        }
        return persisted;
      },
    }
  )
);
