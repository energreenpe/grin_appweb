import React, { useState } from 'react';
import { useWizardStore } from '../../store/wizardStore';

export default function StepCargasCriticas({ onNext }) {
  const { data, setData } = useWizardStore();
  
  // Estado local para el formulario de nuevo equipo
  const [nombre, setNombre] = useState('');
  const [qty, setQty] = useState(1);
  const [horas, setHoras] = useState(4);
  const [watts, setWatts] = useState('');

  const handleAdd = (e) => {
    e.preventDefault();
    if (!nombre || !watts) return;
    
    const newItem = {
      nombre,
      cantidad_unidades: Number(qty),
      horas_dia: Number(horas),
      potencia_w: Number(watts)
    };

    setData({ cargas_aislado: [...data.cargas_aislado, newItem] });
    
    // Resetear formulario
    setNombre(''); setQty(1); setHoras(4); setWatts('');
  };

  const handleRemove = (index) => {
    const list = [...data.cargas_aislado];
    list.splice(index, 1);
    setData({ cargas_aislado: list });
  };

  // Mostrar ~4 filas y habilitar scroll vertical cuando hay más equipos.
  const scrollable = data.cargas_aislado.length > 4;
  const stickyTh = { position: 'sticky', top: 0, zIndex: 1 };

  return (
    <div>
      <h2 style={{ marginBottom: '1rem', textAlign: 'center' }}>Levantamiento de Cargas (Equipos)</h2>
      <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: '2rem' }}>
        Añade los equipos principales que el sistema deberá alimentar.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '2rem', maxWidth: '800px', margin: '0 auto', minWidth: 0, width: '100%' }}>

        {/* Formulario de entrada */}
        <form className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem', minWidth: 0 }} onSubmit={handleAdd}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '1rem', minWidth: 0 }}>
            <div style={{ minWidth: 0 }}>
              <label>Equipo (Ej. Refri)</label>
              <input type="text" className="input-field" value={nombre} onChange={e => setNombre(e.target.value)} required />
            </div>
            <div style={{ minWidth: 0 }}>
              <label>Cantidad</label>
              <input type="number" min="1" className="input-field" value={qty} onChange={e => setQty(e.target.value)} required />
            </div>
            <div style={{ minWidth: 0 }}>
              <label>Potencia (Watts)</label>
              <input type="number" min="1" className="input-field" value={watts} onChange={e => setWatts(e.target.value)} required />
            </div>
            <div style={{ minWidth: 0 }}>
              <label>Horas/día uso</label>
              <input type="number" min="0.1" step="0.1" max="24" className="input-field" value={horas} onChange={e => setHoras(e.target.value)} required />
            </div>
          </div>
          <button type="submit" className="btn btn-secondary" style={{ alignSelf: 'flex-start' }}>+ Agregar Equipo</button>
        </form>

        {/* Lista de cargas */}
        <div className="glass-panel" style={{ padding: '1.5rem', minWidth: 0 }}>
          <h3>Equipos Registrados ({data.cargas_aislado.length})</h3>

          {data.cargas_aislado.length === 0 ? (
            <p style={{ color: 'var(--text-secondary)', marginTop: '1rem' }}>No hay equipos agregados todavía.</p>
          ) : (
            <div
              className="table-container"
              style={{
                marginTop: '1rem',
                ...(scrollable ? { maxHeight: '235px', overflowY: 'auto' } : {}),
              }}
            >
              <table style={{ minWidth: '460px' }}>
                <thead>
                  <tr>
                    <th style={stickyTh}>Equipo</th>
                    <th style={stickyTh}>Cant.</th>
                    <th style={stickyTh}>Watts c/u</th>
                    <th style={stickyTh}>Hrs/Día</th>
                    <th style={stickyTh}>Total Energía (Wh/día)</th>
                    <th style={stickyTh}></th>
                  </tr>
                </thead>
                <tbody>
                  {data.cargas_aislado.map((item, i) => (
                    <tr key={i}>
                      <td>{item.nombre}</td>
                      <td>{item.cantidad_unidades}</td>
                      <td>{item.potencia_w} W</td>
                      <td>{item.horas_dia} h</td>
                      <td><strong>{Math.round(item.cantidad_unidades * item.potencia_w * item.horas_dia)}</strong></td>
                      <td style={{ textAlign: 'right' }}>
                        <button className="btn" style={{ background: 'transparent', color: 'red', padding: '0.2rem' }} onClick={() => handleRemove(i)}>
                          🗑️
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1rem' }}>
          <button className="btn btn-primary" onClick={() => onNext()}>
            Continuar →
          </button>
        </div>
      </div>
    </div>
  );
}
