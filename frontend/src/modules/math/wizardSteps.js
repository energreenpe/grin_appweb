// Máquina de estados del wizard de cálculos MATH. Fuente única de verdad,
// consumida por el store (VALID_STEPS) y por WizardContainer.
// El flujo ramifica según tipo_sistema. Por ahora solo "SFV Aislado" está activo.

export const STEP_ORDER = [
  'inicio', 'tipo_sistema',
  'cargas', 'seleccion', 'resultado',            // rama Aislado
  'seleccion_auto', 'resultado_auto',            // rama Autoconsumo
  'done',
];

export const STEP_LABELS = {
  inicio:          'Cliente e Ingeniero',
  tipo_sistema:    'Tipo de Sistema',
  cargas:          'Cargas / Equipos',
  seleccion:       'Selección de Equipos',
  resultado:       'Resultado',
  seleccion_auto:  'Panel e Inversor',
  resultado_auto:  'Resultado',
  done:            'Completado',
};

export function getNextStep(step, data) {
  switch (step) {
    case 'inicio':
      return 'tipo_sistema';
    case 'tipo_sistema':
      if (data.tipo_sistema === 'SFV Aislado') return 'cargas';
      if (data.tipo_sistema === 'SFV Autoconsumo') return 'seleccion_auto';
      // Híbrido y Bombeo Solar: en desarrollo.
      return null;
    case 'cargas':
      return 'seleccion';
    case 'seleccion':
      return 'resultado';
    case 'resultado':
      return 'done';
    case 'seleccion_auto':
      return 'resultado_auto';
    case 'resultado_auto':
      return 'done';
    default:
      return null;
  }
}

export function getStepLabel(step) {
  return STEP_LABELS[step] || step;
}

export function getProgress(step) {
  const idx = STEP_ORDER.indexOf(step);
  return Math.max(5, Math.min(100, (idx / (STEP_ORDER.length - 1)) * 100));
}

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
