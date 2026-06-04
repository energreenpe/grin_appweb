import React, { useState } from 'react';
import { useWizardStore } from '../../store/wizardStore';
import { inspectorApi } from '../../api/inspectorApi';

const BASE_URL = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL.replace('/api', '')
  : 'http://localhost:8000';

export default function StepCapturaFotos({ seccion, onNext }) {
  const { data, setData, visitaId } = useWizardStore();
  const [loading, setLoading] = useState(false);
  const [deletingIdx, setDeletingIdx] = useState(null);

  const keyFotos = seccion === 'techo' ? 'fotos_techo' : 'fotos_interior';
  const fotos = data[keyFotos] || [];

  const title = seccion === 'techo'
    ? 'Fotos del Techo / Área Solar'
    : 'Fotos del Interior / Tablero Eléctrico';
  const desc = seccion === 'techo'
    ? 'Captura el área donde irán los paneles y las posibles sombras.'
    : 'Captura el tablero principal, llave termomagnética y el medidor.';

  const uploadFoto = async (file) => {
    if (!file || !visitaId) return;
    try {
      setLoading(true);
      let updatedVisita;
      if (seccion === 'techo') {
        updatedVisita = await inspectorApi.uploadFotoTecho(visitaId, file);
      } else {
        updatedVisita = await inspectorApi.uploadFotoInterior(visitaId, file);
      }
      setData({ [keyFotos]: updatedVisita[keyFotos] });
    } catch (error) {
      console.error('Error subiendo foto', error);
      alert('Hubo un error subiendo la foto');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (index) => {
    if (!window.confirm('¿Eliminar esta foto?')) return;
    try {
      setDeletingIdx(index);
      let updatedVisita;
      if (seccion === 'techo') {
        updatedVisita = await inspectorApi.deleteFotoTecho(visitaId, index);
      } else {
        updatedVisita = await inspectorApi.deleteFotoInterior(visitaId, index);
      }
      setData({ [keyFotos]: updatedVisita[keyFotos] });
    } catch (error) {
      console.error('Error eliminando foto', error);
      alert('Hubo un error eliminando la foto');
    } finally {
      setDeletingIdx(null);
    }
  };

  // Estilos reutilizables
  const addBtnLabel = {
    width: '130px',
    height: '130px',
    borderRadius: '12px',
    border: '2px dashed var(--primary-color, #62B989)',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: loading ? 'not-allowed' : 'pointer',
    background: 'rgba(98,185,137,0.06)',
    color: 'var(--primary-color, #62B989)',
    transition: 'background 0.2s',
    opacity: loading ? 0.6 : 1,
    fontSize: '0.8rem',
    fontWeight: 600,
    gap: '0.3rem',
    textAlign: 'center',
    flexShrink: 0,
  };

  return (
    <div>
      {/* Encabezado */}
      <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: '0.3rem' }}>{title}</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>{desc}</p>
        <span style={{
          display: 'inline-block', marginTop: '0.5rem',
          background: 'rgba(98,185,137,0.15)', color: 'var(--primary-color, #62B989)',
          borderRadius: '20px', padding: '2px 12px', fontSize: '0.8rem', fontWeight: 600,
        }}>
          {fotos.length} foto{fotos.length !== 1 ? 's' : ''} subida{fotos.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Grid de fotos + botones de agregar */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '0.75rem',
        marginBottom: '1.5rem',
        justifyContent: fotos.length === 0 ? 'center' : 'flex-start',
      }}>
        {/* Fotos existentes */}
        {fotos.map((foto, idx) => (
          <div
            key={idx}
            style={{
              position: 'relative',
              width: '130px',
              height: '130px',
              borderRadius: '12px',
              overflow: 'hidden',
              border: '1px solid var(--border-color)',
              flexShrink: 0,
            }}
          >
            <img
              src={`${BASE_URL}${foto.url}`}
              alt={`Foto ${idx + 1}`}
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
            {/* Overlay de eliminación */}
            {deletingIdx === idx ? (
              <div style={{
                position: 'absolute', inset: 0,
                background: 'rgba(0,0,0,0.6)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: '#fff', fontSize: '0.75rem',
              }}>
                Eliminando...
              </div>
            ) : (
              <button
                onClick={() => handleDelete(idx)}
                title="Eliminar foto (también se borra del servidor)"
                style={{
                  position: 'absolute', top: '6px', right: '6px',
                  background: 'rgba(220,38,38,0.85)', color: '#fff',
                  border: 'none', borderRadius: '50%',
                  width: '26px', height: '26px',
                  cursor: 'pointer', fontWeight: 700, fontSize: '0.85rem',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  backdropFilter: 'blur(2px)',
                }}
              >
                ✕
              </button>
            )}
            {/* Número de foto */}
            <div style={{
              position: 'absolute', bottom: '5px', left: '7px',
              background: 'rgba(0,0,0,0.55)', color: '#fff',
              borderRadius: '10px', padding: '1px 6px', fontSize: '0.72rem',
            }}>
              #{idx + 1}
            </div>
          </div>
        ))}

        {/* Botón: Tomar Foto con cámara */}
        <label style={addBtnLabel} title="Abre la cámara del dispositivo">
          <span style={{ fontSize: '1.8rem', lineHeight: 1 }}>📷</span>
          <span>{loading ? 'Subiendo...' : 'Tomar\nFoto'}</span>
          <input
            type="file"
            accept="image/*"
            capture="environment"
            style={{ display: 'none' }}
            disabled={loading}
            onChange={(e) => { uploadFoto(e.target.files[0]); e.target.value = null; }}
          />
        </label>

        {/* Botón: Subir desde galería */}
        <label
          style={{ ...addBtnLabel, border: '2px dashed var(--border-color)', color: 'var(--text-secondary)', background: 'rgba(255,255,255,0.03)' }}
          title="Selecciona una imagen de tu galería o archivos"
        >
          <span style={{ fontSize: '1.8rem', lineHeight: 1 }}>📁</span>
          <span>Subir{'\n'}Foto</span>
          <input
            type="file"
            accept="image/*"
            style={{ display: 'none' }}
            disabled={loading}
            onChange={(e) => { uploadFoto(e.target.files[0]); e.target.value = null; }}
          />
        </label>
      </div>

      {/* Nota informativa */}
      <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '1.5rem', textAlign: 'center' }}>
        Las fotos se guardan en formato WebP para optimizar el espacio. Al eliminar una foto, también se borra del servidor.
      </p>

      {/* Botón continuar */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', borderTop: '1px solid var(--border-color)', paddingTop: '1.5rem' }}>
        <button
          id={`btn-continuar-fotos-${seccion}`}
          className="btn btn-primary"
          style={{ padding: '0.75rem 2rem', fontWeight: 700 }}
          onClick={() => onNext()}
          disabled={loading}
        >
          {seccion === 'interior' ? 'Finalizar Inspección' : 'Continuar →'}
        </button>
      </div>
    </div>
  );
}
