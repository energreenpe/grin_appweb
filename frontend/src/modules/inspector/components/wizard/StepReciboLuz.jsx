import React, { useState, useRef } from 'react';
import { useWizardStore } from '../../store/wizardStore';
import { inspectorApi } from '../../api/inspectorApi';

const BASE_URL = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL.replace('/api', '')
  : 'http://localhost:8000';

export default function StepReciboLuz({ onNext }) {
  const { data, setData, visitaId } = useWizardStore();
  const [loading, setLoading] = useState(false);
  const [previewLocal, setPreviewLocal] = useState(null); // blob URL previo a subir
  const inputCamaraRef = useRef(null);
  const inputGaleriaRef = useRef(null);

  const handleFileUpload = async (file) => {
    if (!file) return;
    if (!visitaId) { alert('Error: Visita no creada aún.'); return; }

    // Preview local inmediato
    setPreviewLocal(URL.createObjectURL(file));

    try {
      setLoading(true);
      const updatedVisita = await inspectorApi.uploadRecibo(visitaId, file);
      setData({ recibo_ruta: updatedVisita.recibo_ruta });
    } catch (error) {
      console.error('Error subiendo recibo', error);
      alert('Hubo un error subiendo la foto del recibo');
      setPreviewLocal(null);
    } finally {
      setLoading(false);
    }
  };

  const imageUrl = data.recibo_ruta
    ? `${BASE_URL}${data.recibo_ruta}`
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
        {/* Botón Cámara */}
        <label
          style={{
            ...btnBase,
            background: 'var(--primary-color, #62B989)',
            color: '#fff',
            opacity: loading ? 0.6 : 1,
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
          title="Abre la cámara del dispositivo"
        >
          📷 {imageUrl ? 'Tomar de nuevo' : 'Tomar Foto'}
          <input
            ref={inputCamaraRef}
            type="file"
            accept="image/*"
            capture="environment"
            style={{ display: 'none' }}
            disabled={loading}
            onChange={(e) => handleFileUpload(e.target.files[0])}
            onClick={(e) => { e.target.value = null; }}
          />
        </label>

        {/* Botón Galería */}
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
            ref={inputGaleriaRef}
            type="file"
            accept="image/*"
            style={{ display: 'none' }}
            disabled={loading}
            onChange={(e) => handleFileUpload(e.target.files[0])}
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
