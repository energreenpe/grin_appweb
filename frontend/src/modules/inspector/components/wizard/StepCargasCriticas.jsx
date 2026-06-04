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

  return (
    <div>
      <h2 style={{ marginBottom: '1rem', textAlign: 'center' }}>Levantamiento de Cargas (Equipos)</h2>
      <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: '2rem' }}>
        Añade los equipos principales que el sistema deberá alimentar.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '2rem', maxWidth: '800px', margin: '0 auto' }}>
        
        {/* Formulario de entrada */}
        <form className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }} onSubmit={handleAdd}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '1rem' }}>
            <div>
              <label>Equipo (Ej. Refri)</label>
              <input type="text" className="form-control" value={nombre} onChange={e => setNombre(e.target.value)} required />
            </div>
            <div>
              <label>Cantidad</label>
              <input type="number" min="1" className="form-control" value={qty} onChange={e => setQty(e.target.value)} required />
            </div>
            <div>
              <label>Potencia (Watts)</label>
              <input type="number" min="1" className="form-control" value={watts} onChange={e => setWatts(e.target.value)} required />
            </div>
            <div>
              <label>Horas/día uso</label>
              <input type="number" min="0.1" step="0.1" max="24" className="form-control" value={horas} onChange={e => setHoras(e.target.value)} required />
            </div>
          </div>
          <button type="submit" className="btn btn-secondary" style={{ alignSelf: 'flex-start' }}>+ Agregar Equipo</button>
        </form>

        {/* Lista de cargas */}
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <h3>Equipos Registrados ({data.cargas_aislado.length})</h3>
          
          {data.cargas_aislado.length === 0 ? (
            <p style={{ color: 'var(--text-secondary)', marginTop: '1rem' }}>No hay equipos agregados todavía.</p>
          ) : (
            <table className="table" style={{ marginTop: '1rem' }}>
              <thead>
                <tr>
                  <th>Equipo</th>
                  <th>Cant.</th>
                  <th>Watts c/u</th>
                  <th>Hrs/Día</th>
                  <th>Total Energía (Wh/día)</th>
                  <th></th>
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
