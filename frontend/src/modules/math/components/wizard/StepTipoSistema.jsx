import React from 'react';
import { useCalculoStore } from '../../store/calculoStore';

// Aislado activo en este entregable. Autoconsumo se habilita en el siguiente;
// Híbrido y Bombeo Solar quedan marcados "En desarrollo".
const OPCIONES = [
  { id: 'SFV Aislado',     img: '/math/aislado.png',     label: 'SFV Aislado',     activo: true },
  { id: 'SFV Autoconsumo', img: '/math/autoconsumo.png', label: 'SFV Autoconsumo', activo: true },
  { id: 'SFV Híbrido',     img: '/math/hibrido.png',     label: 'SFV Híbrido',     activo: false },
  { id: 'Bombeo Solar',    img: '/math/bombeo_solar.png', label: 'Bombeo Solar',   activo: false },
];

export default function StepTipoSistema({ onNext }) {
  const { data, setData } = useCalculoStore();

  const handleSelect = (opt) => {
    if (!opt.activo) return;
    setData({ tipo_sistema: opt.id });
    setTimeout(() => onNext({ ...data, tipo_sistema: opt.id }), 100);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <h2 style={{ marginBottom: '0.5rem', textAlign: 'center' }}>¿Qué tipo de sistema vas a calcular?</h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem', textAlign: 'center' }}>
        Selecciona el tipo de sistema fotovoltaico
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.25rem', width: '100%' }}>
        {OPCIONES.map((opt) => {
          const selected = data.tipo_sistema === opt.id;
          return (
            <div
              key={opt.id}
              onClick={() => handleSelect(opt)}
              title={opt.activo ? opt.label : 'En desarrollo'}
              style={{
                position: 'relative',
                padding: '1.25rem',
                borderRadius: '12px',
                border: `2px solid ${selected ? 'var(--primary-color)' : 'var(--border-color)'}`,
                background: selected ? 'rgba(98,185,137,0.1)' : 'rgba(255,255,255,0.04)',
                cursor: opt.activo ? 'pointer' : 'not-allowed',
                textAlign: 'center',
                transition: 'all 0.2s ease',
                opacity: opt.activo ? 1 : 0.5,
              }}
            >
              {!opt.activo && (
                <span style={{
                  position: 'absolute', top: '8px', right: '8px', fontSize: '0.65rem', fontWeight: 700,
                  padding: '2px 8px', borderRadius: '10px', background: 'rgba(255,193,7,0.15)', color: '#ffc107',
                }}>
                  En desarrollo
                </span>
              )}
              <img
                src={opt.img} alt={opt.label}
                style={{ width: '100%', height: '120px', objectFit: 'contain', marginBottom: '0.75rem', filter: opt.activo ? 'none' : 'grayscale(1)' }}
              />
              <h4 style={{ margin: 0 }}>{opt.label}</h4>
            </div>
          );
        })}
      </div>
    </div>
  );
}
