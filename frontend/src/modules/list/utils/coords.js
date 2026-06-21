/**
 * LIST — Sincronización de coordenadas HTML ↔ PDF.
 *
 * El estado interno (fields/overlays) se guarda SIEMPRE en PDF points
 * (1 pulgada = 72 pt), independiente del zoom/pantalla. Estas utilidades traducen
 * entre píxeles de pantalla (a zoom actual) y points nativos del PDF.
 */

export function getScaleFactors(pdfWidthInPoints, pdfHeightInPoints, htmlWidthAtZoom1, htmlHeightAtZoom1) {
  if (!htmlWidthAtZoom1 || !htmlHeightAtZoom1) {
    return { scaleX: 1, scaleY: 1 };
  }
  return {
    scaleX: pdfWidthInPoints / htmlWidthAtZoom1,
    scaleY: pdfHeightInPoints / htmlHeightAtZoom1,
  };
}

export function htmlToPdf(htmlX, htmlY, htmlWidth, htmlHeight, scaleX, scaleY, zoom) {
  const z = zoom || 1.0;
  return {
    x: (htmlX / z) * scaleX,
    y: (htmlY / z) * scaleY,
    width: (htmlWidth / z) * scaleX,
    height: (htmlHeight / z) * scaleY,
  };
}

export function pdfToHtml(pdfX, pdfY, pdfWidth, pdfHeight, scaleX, scaleY, zoom) {
  const z = zoom || 1.0;
  const sX = scaleX || 1.0;
  const sY = scaleY || 1.0;
  return {
    left: (pdfX / sX) * z,
    top: (pdfY / sY) * z,
    width: (pdfWidth / sX) * z,
    height: (pdfHeight / sY) * z,
  };
}

/** RGB float [r,g,b] (0..1) → "#rrggbb". */
export function rgbToHex(rgb) {
  if (!rgb || !Array.isArray(rgb) || rgb.length < 3) return '#000000';
  return '#' + rgb.map((v) => {
    const byte = Math.max(0, Math.min(255, Math.round(v * 255)));
    return byte.toString(16).padStart(2, '0');
  }).join('');
}

/** "#rrggbb" → RGB float [r,g,b] (0..1). */
export function hexToRgb(hex) {
  const cleanHex = hex.startsWith('#') ? hex.slice(1) : hex;
  if (cleanHex.length < 6) return [0, 0, 0];
  return [
    parseInt(cleanHex.slice(0, 2), 16) / 255,
    parseInt(cleanHex.slice(2, 4), 16) / 255,
    parseInt(cleanHex.slice(4, 6), 16) / 255,
  ];
}
