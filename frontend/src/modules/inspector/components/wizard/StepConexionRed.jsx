import React from 'react';
import { useWizardStore } from '../../store/wizardStore';

export default function StepConexionRed({ onNext }) {
  const { data, setData } = useWizardStore();

  const handleSelect = (tieneConexion) => {
    setData({ conexion_red: tieneConexion });
    setTimeout(() => onNext({ ...data, conexion_red: tieneConexion }), 100);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <h2 style={{ marginBottom: '2rem', textAlign: 'center' }}>¿El predio tiene conexión a la Red Eléctrica?</h2>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', width: '100%', maxWidth: '500px' }}>
        <div 
          style={{
            padding: '2rem',
            borderRadius: '12px',
            border: `2px solid ${data.conexion_red === 'Si' ? 'var(--primary-color)' : 'var(--border-color)'}`,
            background: data.conexion_red === 'Si' ? 'rgba(98, 185, 137, 0.1)' : 'rgba(255,255,255,0.05)',
            cursor: 'pointer',
            textAlign: 'center'
          }}
          onClick={() => handleSelect('Si')}
        >
          <span style={{ fontSize: '3rem' }}>🔌</span>
          <h3>Sí tiene</h3>
        </div>

        <div 
          style={{
            padding: '2rem',
            borderRadius: '12px',
            border: `2px solid ${data.conexion_red === 'No' ? 'var(--primary-color)' : 'var(--border-color)'}`,
            background: data.conexion_red === 'No' ? 'rgba(98, 185, 137, 0.1)' : 'rgba(255,255,255,0.05)',
            cursor: 'pointer',
            textAlign: 'center'
          }}
          onClick={() => handleSelect('No')}
        >
          <span style={{ fontSize: '3rem' }}>🚫</span>
          <h3>No tiene</h3>
        </div>
      </div>
    </div>
  );
}
