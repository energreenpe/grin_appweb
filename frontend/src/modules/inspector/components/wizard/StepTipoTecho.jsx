import React from 'react';
import { useWizardStore } from '../../store/wizardStore';

export default function StepTipoTecho({ onNext }) {
  const { data, setData } = useWizardStore();

  const tipos = [
    { id: 'Calamina', label: 'Calamina Ondulada' },
    { id: 'Teja', label: 'Teja Andina / Arcilla' },
    { id: 'Concreto', label: 'Losa de Concreto' },
    { id: 'Suelo', label: 'Suelo / Piso' },
    { id: 'Eternit', label: 'Fibrocemento (Eternit)' },
    { id: 'Otro', label: 'Otro' }
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    onNext();
  };

  // Etiqueta de campo consistente con el tema oscuro (igual que el resto del wizard).
  const labelStyle = {
    display: 'block',
    marginBottom: '0.45rem',
    fontSize: '0.85rem',
    fontWeight: 600,
    color: 'var(--text-secondary)',
  };

  const textareaStyle = { resize: 'vertical', minHeight: '90px' };

  return (
    <div>
      <h2 style={{ marginBottom: '1rem', textAlign: 'center' }}>Evaluación del Techo</h2>
      
      <form onSubmit={handleSubmit} style={{ maxWidth: '600px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        
        <div>
          <label style={{ fontSize: '1.1rem', marginBottom: '1rem', display: 'block', textAlign: 'center' }}>
            ¿De qué material es el techo principal?
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
            {tipos.map(t => (
              <div 
                key={t.id}
                style={{
                  padding: '1rem',
                  borderRadius: '8px',
                  border: `2px solid ${data.tipo_techo === t.id ? 'var(--primary-color)' : 'var(--border-color)'}`,
                  background: data.tipo_techo === t.id ? 'rgba(98, 185, 137, 0.1)' : 'rgba(255,255,255,0.05)',
                  cursor: 'pointer',
                  textAlign: 'center'
                }}
                onClick={() => setData({ tipo_techo: t.id })}
              >
                {t.label}
              </div>
            ))}
          </div>
        </div>

        <div>
          <label style={labelStyle}>Observaciones del Techo / Sombras (Opcional)</label>
          <textarea
            className="input-field"
            style={textareaStyle}
            rows="3"
            placeholder="Ej: Tiene una antena parabólica que genera sombra de 2pm a 5pm..."
            value={data.obs_techo}
            onChange={(e) => setData({ obs_techo: e.target.value })}
          />
        </div>

        <div>
          <label style={labelStyle}>Observaciones de Instalación Interior / Tablero (Opcional)</label>
          <textarea
            className="input-field"
            style={textareaStyle}
            rows="3"
            placeholder="Ej: El tablero principal está a 15 metros del pase del techo..."
            value={data.obs_interior}
            onChange={(e) => setData({ obs_interior: e.target.value })}
          />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.5rem' }}>
          <button type="submit" className="btn btn-primary" disabled={!data.tipo_techo}>
            Continuar →
          </button>
          {!data.tipo_techo && (
            <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
              Selecciona el material del techo para continuar
            </p>
          )}
        </div>
      </form>
    </div>
  );
}
