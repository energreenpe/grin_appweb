import React, { useState } from 'react';
import { useWizardStore } from '../../store/wizardStore';
import { inspectorApi } from '../../api/inspectorApi';
import { notify } from '../../../../lib/notify';
import { fileUrl } from '../../../../lib/api';
import { toWebpFile, MAX_INPUT_BYTES } from '../../lib/imageTools';
import CameraCapture from '../CameraCapture';

export default function StepReciboLuz({ onNext }) {
  const { data, setData, visitaId } = useWizardStore();
  const [loading, setLoading] = useState(false);
  const [previewLocal, setPreviewLocal] = useState(null); // blob URL previo a subir
  const [showCamera, setShowCamera] = useState(false);

  const handleFileUpload = async (file) => {
    if (!file) return;
    if (!visitaId) { notify('La visita aún no se ha creado. Vuelve al primer paso.'); return; }

    // Preview local inmediato
    setPreviewLocal(URL.createObjectURL(file));

    try {
      setLoading(true);
      const updatedVisita = await inspectorApi.uploadRecibo(visitaId, file);
      setData({ recibo_ruta: updatedVisita.recibo_ruta });
    } catch (error) {
      console.error('Error subiendo recibo', error);
      notify('No se pudo subir la foto del recibo. Revisa tu conexión.');
      setPreviewLocal(null);
    } finally {
      setLoading(false);
    }
  };

  // Galería/archivo: comprimir a WebP en el cliente antes de subir.
  const handleGalleryPick = async (file) => {
    if (!file) return;
    if (file.size > MAX_INPUT_BYTES) {
      notify(`La imagen es demasiado grande (máx ${MAX_INPUT_BYTES / (1024 * 1024)} MB). Elige una foto más liviana.`);
      return;
    }
    try {
      const webp = await toWebpFile(file);
      await handleFileUpload(webp);
    } catch (e) {
      console.error('procesando imagen', e);
      notify('No se pudo procesar la imagen.');
    }
  };

  // Cámara: ya devuelve un File .webp listo para subir.
  const handleCameraCapture = async (file) => {
    setShowCamera(false);
    await handleFileUpload(file);
  };

  const imageUrl = data.recibo_ruta
    ? fileUrl(data.recibo_ruta)
    : previewLocal;

  const btnBase = {
    flex: 1,
    padding: '0.75rem 1rem',
    borderRadius: '10px',
    border: 'none',
    cursor: 'pointer',
    fontWeight: 600,
    fontSize: '0.9rem',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.4rem',
    transition: 'opacity 0.2s',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.5rem' }}>
      {showCamera && (
        <CameraCapture onCapture={handleCameraCapture} onClose={() => setShowCamera(false)} />
      )}

      <div style={{ textAlign: 'center' }}>
        <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: '0.3rem' }}>
          Foto del Recibo de Luz
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
          Toma una foto clara donde se vea el historial de consumo mensual
        </p>
      </div>

      {/* ── Preview de la imagen ── */}
      <div style={{
        width: '100%',
        maxWidth: '480px',
        aspectRatio: '4/3',
        borderRadius: '14px',
        overflow: 'hidden',
        border: imageUrl ? '2px solid var(--primary-color, #62B989)' : '2px dashed var(--border-color)',
        background: 'rgba(255,255,255,0.04)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
      }}>
        {imageUrl ? (
          <>
            <img
              src={imageUrl}
              alt="Recibo de luz"
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
            {loading && (
              <div style={{
                position: 'absolute', inset: 0,
                background: 'rgba(0,0,0,0.55)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: '#fff', fontWeight: 600, fontSize: '0.9rem',
              }}>
                Subiendo...
              </div>
            )}
            {/* Badge OK */}
            {!loading && data.recibo_ruta && (
              <div style={{
                position: 'absolute', top: '10px', right: '10px',
                background: 'rgba(98,185,137,0.9)', color: '#fff',
                borderRadius: '20px', padding: '3px 10px', fontSize: '0.78rem', fontWeight: 700,
              }}>
                Guardado
              </div>
            )}
          </>
        ) : (
          <div style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
            <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>🧾</div>
            <div style={{ fontSize: '0.88rem' }}>Aquí aparecerá la foto del recibo</div>
          </div>
        )}
      </div>

      {/* ── Botones: Tomar Foto / Galería ── */}
      <div style={{ display: 'flex', gap: '0.75rem', width: '100%', maxWidth: '480px' }}>
        {/* Botón Cámara (getUserMedia) */}
        <button
          type="button"
          style={{
            ...btnBase,
            fontFamily: 'inherit',
            background: 'var(--primary-color, #62B989)',
            color: '#fff',
            opacity: loading ? 0.6 : 1,
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
          disabled={loading}
          onClick={() => setShowCamera(true)}
          title="Abre la cámara del dispositivo"
        >
          📷 {imageUrl ? 'Tomar de nuevo' : 'Tomar Foto'}
        </button>

        {/* Botón Galería (se comprime a WebP) */}
        <label
          style={{
            ...btnBase,
            background: 'transparent',
            border: '1px solid var(--border-color)',
            color: 'var(--text-primary)',
            opacity: loading ? 0.6 : 1,
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
          title="Selecciona una imagen de tu galería o archivos"
        >
          📁 Subir Foto
          <input
            type="file"
            accept="image/*"
            style={{ display: 'none' }}
            disabled={loading}
            onChange={(e) => handleGalleryPick(e.target.files[0])}
            onClick={(e) => { e.target.value = null; }}
          />
        </label>
      </div>

      {/* ── Botón Continuar ── */}
      <div style={{ width: '100%', maxWidth: '480px' }}>
        <button
          id="btn-continuar-recibo"
          className="btn btn-primary"
          style={{ width: '100%', padding: '0.85rem', fontWeight: 700 }}
          onClick={() => onNext()}
          disabled={loading || !data.recibo_ruta}
        >
          Continuar →
        </button>
        {!data.recibo_ruta && (
          <p style={{ textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '0.5rem' }}>
            Sube la foto del recibo para continuar
          </p>
        )}
      </div>
    </div>
  );
}
