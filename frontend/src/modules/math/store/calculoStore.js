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
  // Entrada del Autoconsumo (reusa panel_id como panel FV)
  inversor_id: null,
  inversor_info: null,
  tipo_conexion: 'Monofásico',
  voltaje_red: '220',
  consumo_mensual: '',        // kWh/mes
  potencia_contratada: '',    // kW
  autarquia: 40,              // %
  opcion_elegida: null,       // "min" | "opt" | "max"
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
      readOnly: false,          // true al ver un cálculo completado (solo lectura)
      data: { ...initialData },

      setData: (partial) => set((s) => ({ data: { ...s.data, ...partial } })),
      setCalculoId: (id) => set({ calculoId: id }),
      setReadOnly: (v) => set({ readOnly: v }),

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
        readOnly: false,
        data: { ...initialData },
      }),
    }),
    {
      name: 'math-calculo-storage',
      storage: createJSONStorage(() => localStorage),
      version: 2,
      migrate: (persisted) => {
        if (!persisted || !VALID_STEPS.includes(persisted.currentStep)) {
          return { calculoId: null, currentStep: 'inicio', stepHistory: [], data: { ...initialData } };
        }
        // Fusiona con initialData para que los campos nuevos tengan defaults.
        return { ...persisted, data: { ...initialData, ...(persisted.data || {}) } };
      },
    }
  )
);
