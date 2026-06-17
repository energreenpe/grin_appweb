import axios from 'axios';

// Base del servidor (sin /api): para archivos estáticos servidos en /uploads.
export const SERVER_BASE = 'http://localhost:8000';

export const api = axios.create({
  baseURL: `${SERVER_BASE}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Convierte una ruta relativa de uploads ("uploads/banks/x.webp") en URL absoluta.
export const fileUrl = (relPath) =>
  relPath ? `${SERVER_BASE}/${String(relPath).replace(/^\/+/, '')}` : null;
