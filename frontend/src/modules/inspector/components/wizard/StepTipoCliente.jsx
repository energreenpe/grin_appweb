import React from 'react';
import { useWizardStore } from '../../store/wizardStore';

export default function StepTipoCliente({ onNext }) {
  const { setData, data } = useWizardStore();

  const handleSelect = (tipo) => {
    setData({ tipo_cliente: tipo });
    // Simulamos un retraso sutil para UX móvil, pero avanzamos automático
    setTimeout(() => onNext({ ...data, tipo_cliente: tipo }), 100);
  };

  const cardStyle = {
    padding: '2rem',
    borderRadius: '12px',
    border: '2px solid var(--border-color)',
    cursor: 'pointer',
    textAlign: 'center',
    transition: 'all 0.2s ease',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '1rem',
    background: 'rgba(255,255,255,0.05)'
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <h2 style={{ marginBottom: '2rem', textAlign: 'center' }}>¿Qué tipo de cliente es?</h2>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '2rem', width: '100%' }}>
        <div 
          style={{
            ...cardStyle,
            borderColor: data.tipo_cliente === 'Persona' ? 'var(--primary-color)' : 'var(--border-color)',
            background: data.tipo_cliente === 'Persona' ? 'rgba(98, 185, 137, 0.1)' : cardStyle.background
          }}
          onClick={() => handleSelect('Persona')}
        >
          <span style={{ fontSize: '3rem' }}>👤</span>
          <h3>Persona (DNI)</h3>
        </div>

        <div 
          style={{
            ...cardStyle,
            borderColor: data.tipo_cliente === 'Empresa' ? 'var(--primary-color)' : 'var(--border-color)',
            background: data.tipo_cliente === 'Empresa' ? 'rgba(98, 185, 137, 0.1)' : cardStyle.background
          }}
          onClick={() => handleSelect('Empresa')}
        >
          <span style={{ fontSize: '3rem' }}>🏢</span>
          <h3>Empresa (RUC)</h3>
        </div>
      </div>
    </div>
  );
}
