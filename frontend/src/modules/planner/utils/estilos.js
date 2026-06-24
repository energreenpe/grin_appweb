// estilos.js — Colores de estado/badges para el tema OSCURO de grin.
// Devuelven un objeto de estilo inline { background, color } translúcido.

const make = (rgb) => ({ background: `rgba(${rgb}, 0.18)`, color: `rgb(${rgb})` });

const NEUTRAL = { background: 'rgba(160,160,160,0.15)', color: '#cfcfcf' };
const GREEN = make('98,185,137');
const BLUE = make('122,183,255');
const YELLOW = make('240,180,41');
const RED = make('255,138,138');
const PURPLE = make('192,132,252');
const TEAL = make('45,212,191');
const ORANGE = make('251,146,60');

export function estadoBadge(estado) {
  switch (estado) {
    case 'En Progreso': return BLUE;
    case 'Completado': return GREEN;
    case 'Cancelado': return RED;
    case 'Pendiente':
    default: return NEUTRAL;
  }
}

export function estadoActividadBadge(estado) {
  switch (estado) {
    case 'En curso': return BLUE;
    case 'Completado': return GREEN;
    case 'Bloqueado': return RED;
    case 'Pendiente':
    default: return NEUTRAL;
  }
}

export function prioridadColor(prioridad) {
  switch (prioridad) {
    case 'Alta': return '#ff8a8a';
    case 'Media': return '#f0b429';
    case 'Baja': return '#62B989';
    default: return 'var(--text-secondary)';
  }
}

export function asistenciaBadge(estado) {
  switch (estado) {
    case 'Presente': return GREEN;
    case 'Tardanza': return YELLOW;
    case 'Ausente': return RED;
    default: return NEUTRAL;
  }
}

export function rolBadge(rol) {
  switch (rol) {
    case 'Jefe de Cuadrilla': return PURPLE;
    case 'Capataz': return BLUE;
    case 'Técnico': return TEAL;
    case 'Instalador': return GREEN;
    case 'Operario': return YELLOW;
    case 'Supervisor': return ORANGE;
    case 'Ingeniero': return PURPLE;
    case 'Peón':
    case 'Otro':
    default: return NEUTRAL;
  }
}
