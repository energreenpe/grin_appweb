// Fuente única de verdad de la máquina de estados del wizard de inspección.
// Antes esto estaba duplicado en wizardStore (VALID_STEPS) y WizardContainer
// (getNextStep / stepOrder / labels). Centralizarlo evita que se desincronicen.

export const STEP_ORDER = [
  'inicio', 'tipo_sistema', 'conexion_red', 'recibo_luz',
  'cargas_criticas', 'tipo_techo', 'fotos_techo', 'fotos_interior', 'done',
];

export const STEP_LABELS = {
  inicio:          'Cliente y Técnico',
  tipo_sistema:    'Tipo de Sistema',
  conexion_red:    'Conexión a Red',
  recibo_luz:      'Recibo de Luz',
  cargas_criticas: 'Cargas Críticas',
  tipo_techo:      'Tipo de Techo',
  fotos_techo:     'Fotos del Techo',
  fotos_interior:  'Fotos del Interior',
  done:            'Completado',
};

// Transición condicional: dado el paso actual y los datos, devuelve el siguiente.
export function getNextStep(step, data) {
  switch (step) {
    case 'inicio':
      return 'tipo_sistema';
    case 'tipo_sistema':
      if (['SFV Autoconsumo', 'SFV Híbrido'].includes(data.tipo_sistema)) return 'conexion_red';
      if (data.tipo_sistema === 'SFV Aislado') return 'cargas_criticas';
      return 'tipo_techo'; // Terma Solar, BESS
    case 'conexion_red':
      if (data.conexion_red === 'Si') return 'recibo_luz';
      return data.tipo_sistema === 'SFV Híbrido' ? 'cargas_criticas' : 'tipo_techo';
    case 'recibo_luz':
      return data.tipo_sistema === 'SFV Híbrido' ? 'cargas_criticas' : 'tipo_techo';
    case 'cargas_criticas':
      return 'tipo_techo';
    case 'tipo_techo':
      return 'fotos_techo';
    case 'fotos_techo':
      return 'fotos_interior';
    case 'fotos_interior':
      return 'done';
    default:
      return null;
  }
}

export function getStepLabel(step) {
  return STEP_LABELS[step] || step;
}

// Porcentaje aproximado de avance (mínimo 5% para que la barra no quede vacía).
export function getProgress(step) {
  const idx = STEP_ORDER.indexOf(step);
  return Math.max(5, Math.min(100, (idx / (STEP_ORDER.length - 1)) * 100));
}

// Reconstruye el historial de pasos recorridos hasta `target`, siguiendo la
// máquina desde 'inicio' con los datos dados. Permite que "Volver" funcione al
// reanudar un borrador en un paso intermedio.
export function buildHistory(target, data) {
  const history = [];
  let step = 'inicio';
  let guard = 0;
  while (step && step !== target && guard++ < STEP_ORDER.length) {
    history.push(step);
    step = getNextStep(step, data);
  }
  return history;
}
