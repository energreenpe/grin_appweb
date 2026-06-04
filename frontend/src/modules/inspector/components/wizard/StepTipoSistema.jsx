import React from 'react';
import { useWizardStore } from '../../store/wizardStore';

export default function StepTipoSistema({ onNext }) {
  const { data, setData } = useWizardStore();

  const handleSelect = (tipo) => {
    setData({ tipo_sistema: tipo });
    setTimeout(() => onNext({ ...data, tipo_sistema: tipo }), 100);
  };

  const opciones = [
    { id: 'SFV Autoconsumo', icon: '☀️', label: 'SFV Autoconsumo' },
    { id: 'SFV Híbrido', icon: '🔋', label: 'SFV Híbrido' },
    { id: 'SFV Aislado', icon: '🏝️', label: 'SFV Aislado' },
    { id: 'Terma Solar', icon: '🌡️', label: 'Terma Solar' },
    { id: 'BESS', icon: '⚡', label: 'BESS (Solo Baterías)' }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <h2 style={{ marginBottom: '2rem', textAlign: 'center' }}>¿Qué tipo de sistema se cotizará?</h2>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', width: '100%' }}>
        {opciones.map(opt => (
          <div 
            key={opt.id}
            style={{
              padding: '1.5rem',
              borderRadius: '12px',
              border: `2px solid ${data.tipo_sistema === opt.id ? 'var(--primary-color)' : 'var(--border-color)'}`,
              background: data.tipo_sistema === opt.id ? 'rgba(98, 185, 137, 0.1)' : 'rgba(255,255,255,0.05)',
              cursor: 'pointer',
              textAlign: 'center',
              transition: 'all 0.2s ease'
            }}
            onClick={() => handleSelect(opt.id)}
          >
            <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>{opt.icon}</div>
            <h4 style={{ margin: 0 }}>{opt.label}</h4>
          </div>
        ))}
      </div>
    </div>
  );
}
