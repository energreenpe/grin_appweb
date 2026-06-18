import React, { useEffect, useRef, useState } from 'react';
import { videoFrameToWebpFile } from '../lib/imageTools';
import { notify } from '../../../lib/notify';

// Modal de captura de foto con la cámara del dispositivo (funciona en escritorio
// y móvil vía getUserMedia). Requiere contexto seguro (HTTPS o localhost).
// onCapture(file) recibe un File .webp ya redimensionado; onClose() cierra.
export default function CameraCapture({ onCapture, onClose }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const [ready, setReady] = useState(false);
  // Soporte de cámara evaluado de forma síncrona al montar (evita setState en effect).
  const [error, setError] = useState(() =>
    navigator.mediaDevices?.getUserMedia ? null : 'Este navegador no soporta el acceso a la cámara. Usa "Subir Foto".'
  );
  const [capturing, setCapturing] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function start() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'environment' },
          audio: false,
        });
        if (cancelled) { stream.getTracks().forEach((t) => t.stop()); return; }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play().catch(() => {});
        }
        setReady(true);
      } catch (e) {
        console.error('getUserMedia', e);
        if (e.name === 'NotAllowedError') setError('Permiso de cámara denegado. Habilítalo en el navegador e inténtalo de nuevo.');
        else if (e.name === 'NotFoundError') setError('No se encontró ninguna cámara en el dispositivo.');
        else setError('No se pudo acceder a la cámara.');
      }
    }

    if (navigator.mediaDevices?.getUserMedia) start();

    return () => {
      cancelled = true;
      if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
    };
  }, []);

  const handleCapture = async () => {
    if (!videoRef.current || !ready) return;
    try {
      setCapturing(true);
      const file = await videoFrameToWebpFile(videoRef.current);
      if (!file) { notify('No se pudo procesar la foto en este navegador.'); return; }
      onCapture(file);
    } catch (e) {
      console.error('captura', e);
      notify('No se pudo capturar la foto.');
    } finally {
      setCapturing(false);
    }
  };

  return (
    <div style={overlay} onClick={onClose}>
      <div style={panel} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <strong style={{ fontSize: '1rem' }}>📷 Tomar foto</strong>
          <button onClick={onClose} style={closeBtn} title="Cerrar">✕</button>
        </div>

        {error ? (
          <div style={{ padding: '1.5rem 1rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🚫</div>
            <p style={{ fontSize: '0.9rem' }}>{error}</p>
            <button onClick={onClose} className="btn btn-secondary" style={{ marginTop: '0.5rem' }}>Cerrar</button>
          </div>
        ) : (
          <>
            <div style={videoWrap}>
              <video
                ref={videoRef}
                playsInline
                muted
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
              {!ready && (
                <div style={loadingOverlay}>Iniciando cámara…</div>
              )}
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
              <button onClick={onClose} className="btn btn-secondary" style={{ flex: 1 }} disabled={capturing}>
                Cancelar
              </button>
              <button onClick={handleCapture} className="btn btn-primary" style={{ flex: 2, fontWeight: 700 }} disabled={!ready || capturing}>
                {capturing ? 'Procesando…' : '📸 Capturar'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ── estilos ──
const overlay = {
  position: 'fixed', inset: 0, zIndex: 1000,
  background: 'rgba(0,0,0,0.7)',
  display: 'flex', alignItems: 'center', justifyContent: 'center',
  padding: '1rem',
};

const panel = {
  background: 'var(--card-bg, #1e1e2e)',
  border: '1px solid var(--border-color)',
  borderRadius: '14px',
  padding: '1rem',
  width: '100%', maxWidth: '460px',
  boxShadow: '0 12px 40px rgba(0,0,0,0.5)',
};

const videoWrap = {
  width: '100%', aspectRatio: '4/3',
  borderRadius: '10px', overflow: 'hidden',
  background: '#000', position: 'relative',
};

const loadingOverlay = {
  position: 'absolute', inset: 0,
  display: 'flex', alignItems: 'center', justifyContent: 'center',
  color: '#fff', fontSize: '0.9rem',
};

const closeBtn = {
  background: 'transparent', border: 'none', color: 'var(--text-secondary)',
  cursor: 'pointer', fontSize: '1.1rem', padding: '0.25rem',
};
