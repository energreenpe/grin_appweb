// Conversión/compresión de imágenes a WebP en el cliente.
// Reduce el peso antes de subir y garantiza el formato .webp incluso para HEIC
// de iPhone. El backend igual revalida y reconvierte (defensa en profundidad).

const MAX_DIM = 1600;   // lado mayor máximo en px
const QUALITY = 0.8;    // calidad WebP

// Tope del archivo de ORIGEN (antes de comprimir). Una foto de celular pesa
// 2–12 MB; 30 MB cubre incluso cámaras de 48 MP. Evita intentar decodificar
// archivos enormes que colgarían el navegador. El backend reimpone su propio
// límite de 10 MB sobre el archivo ya comprimido.
export const MAX_INPUT_BYTES = 30 * 1024 * 1024;

// Dibuja el `source` redimensionado en un canvas y lo exporta como File .webp.
// Devuelve null si el navegador no soporta codificar WebP por canvas.
async function exportWebp(draw, srcW, srcH, { maxDim = MAX_DIM, quality = QUALITY }, baseName) {
  const scale = Math.min(1, maxDim / Math.max(srcW, srcH || 1));
  const w = Math.max(1, Math.round(srcW * scale));
  const h = Math.max(1, Math.round(srcH * scale));

  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d');
  draw(ctx, w, h);

  const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/webp', quality));
  if (!blob) return null;
  return new File([blob], `${baseName}.webp`, { type: 'image/webp' });
}

function loadViaImg(blob) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(blob);
    const img = new Image();
    img.onload = () => { URL.revokeObjectURL(url); resolve(img); };
    img.onerror = (e) => { URL.revokeObjectURL(url); reject(e); };
    img.src = url;
  });
}

// Convierte un File/Blob (galería o archivo) a un File .webp redimensionado.
export async function toWebpFile(fileOrBlob, opts = {}) {
  const baseName = fileOrBlob.name ? fileOrBlob.name.replace(/\.[^.]+$/, '') : 'foto';

  let source, srcW, srcH, bitmap;
  try {
    // createImageBitmap respeta la orientación EXIF en navegadores modernos.
    bitmap = await createImageBitmap(fileOrBlob, { imageOrientation: 'from-image' });
    source = bitmap; srcW = bitmap.width; srcH = bitmap.height;
  } catch {
    source = await loadViaImg(fileOrBlob);
    srcW = source.naturalWidth; srcH = source.naturalHeight;
  }

  const file = await exportWebp((ctx, w, h) => ctx.drawImage(source, 0, 0, w, h), srcW, srcH, opts, baseName);
  if (bitmap && bitmap.close) bitmap.close();

  // Fallback: si el navegador no codifica webp, sube el original (el backend convierte).
  return file || (fileOrBlob instanceof File
    ? fileOrBlob
    : new File([fileOrBlob], baseName, { type: fileOrBlob.type || 'image/jpeg' }));
}

// Captura el fotograma actual de un <video> y lo devuelve como File .webp.
export async function videoFrameToWebpFile(video, opts = {}) {
  return exportWebp(
    (ctx, w, h) => ctx.drawImage(video, 0, 0, w, h),
    video.videoWidth, video.videoHeight,
    opts, `captura_${Date.now()}`
  );
}
