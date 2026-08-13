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
  // Redondeado a px entero: el <canvas> del PDF ya cae en una grilla de píxeles
  // físicos (pdf.js la redondea internamente al pintar). Si nuestra capa de
  // texto queda en una posición fraccionaria (ej. 676.23px), el navegador la
  // redondea por su cuenta al pintar — y con devicePixelRatio fraccionario
  // (1.5, 2.625, típico de Windows a 150%/250%+ de escala) ese redondeo puede
  // no coincidir con el del canvas, produciendo un desfase visible sobre todo
  // a zooms bajos (filas muy chicas en píxeles). Redondear acá evita esa
  // segunda ronda de redondeo impredecible del navegador.
  return {
    left: Math.round((pdfX / sX) * z),
    top: Math.round((pdfY / sY) * z),
    width: Math.round((pdfWidth / sX) * z),
    height: Math.round((pdfHeight / sY) * z),
  };
}

let _measureCtx = null;
function _getMeasureCtx() {
  if (!_measureCtx) _measureCtx = document.createElement('canvas').getContext('2d');
  return _measureCtx;
}

/** Ancho aproximado (points PDF, 1px≈1pt) de una sola línea de texto con la
 * fuente/tamaño dados. Usa la fuente web más parecida — el PDF final se
 * genera con fuentes estándar (Helvetica/Times/Courier) que no miden
 * exactamente igual, por eso getMinFieldSize aplica un margen de seguridad
 * sobre este valor en vez de usarlo tal cual. */
function measureLineWidth(line, fontFamily, fontSize) {
  const ctx = _getMeasureCtx();
  const family = fontFamily === 'Courier' ? 'monospace' : 'sans-serif';
  ctx.font = `${fontSize}px ${family}`;
  return ctx.measureText(line).width;
}

/** Tamaño mínimo (points PDF) para que el texto de un campo entre completo y
 * no desaparezca al exportar (pdf_stamp.py recorta silenciosamente lo que no
 * entra en el cuadro). Alto = una línea por cada salto de línea explícito
 * (leading = font_size*1.2, igual fórmula que usa el backend); ancho = lo que
 * mide la línea más larga, con margen de seguridad. */
export function getMinFieldSize(text, fontFamily, fontSize) {
  const lines = (text || '').split('\n');
  const minHeight = Math.max(16, Math.ceil(fontSize * 1.2 * lines.length));
  const widest = Math.max(0, ...lines.map((l) => measureLineWidth(l, fontFamily, fontSize)));
  const minWidth = Math.max(30, Math.ceil(widest * 1.15) + 8);
  return { minWidth, minHeight };
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
