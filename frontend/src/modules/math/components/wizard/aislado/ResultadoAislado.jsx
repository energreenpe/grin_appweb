import React from 'react';
import { useCalculoStore } from '../../../store/calculoStore';

function Metric({ label, value, unit, highlight }) {
  return (
    <div className="glass-panel" style={{ padding: '1rem', textAlign: 'center' }}>
      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</div>
      <div style={{ fontSize: '1.6rem', fontWeight: 700, color: highlight ? 'var(--primary-color)' : 'var(--text-primary)', marginTop: '0.25rem' }}>
        {value}{unit ? <span style={{ fontSize: '0.9rem', marginLeft: '2px' }}>{unit}</span> : null}
      </div>
    </div>
  );
}

export default function ResultadoAislado({ onNext, readOnly = false }) {
  const { data } = useCalculoStore();
  const r = data.resultado;

  if (!r) {
    return <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>Calculando…</div>;
  }

  return (
    <div>
      <h2 style={{ marginBottom: '0.5rem', textAlign: 'center' }}>Resultado del Dimensionamiento</h2>
      <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: '2rem' }}>
        {data.nombre_proyecto} · {data.region} · Sistema {r.voltaje_sistema}V
      </p>

      {/* Métricas principales */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <Metric label="Energía diaria" value={r.consumo.energia_diaria_wh} unit="Wh" />
        <Metric label="Potencia pico" value={r.potencia_pico_wp} unit="Wp" />
        <Metric label="N° de paneles" value={r.num_paneles} highlight />
        <Metric label="N° de baterías" value={r.num_baterias} highlight />
        <Metric label="Banco baterías" value={r.capacidad_ah} unit="Ah" />
        <Metric label="Potencia inversor" value={r.potencia_inversor_w} unit="W" />
      </div>

      {/* Equipos elegidos */}
      <div className="glass-panel" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '0.5rem' }}>
          <div>☀️ <strong>{r.num_paneles} ×</strong> {r.panel.descripcion} <span style={{ color: 'var(--text-secondary)' }}>({r.panel.potencia_w} Wp)</span></div>
          <div>🔋 <strong>{r.num_baterias} ×</strong> {r.bateria.descripcion} <span style={{ color: 'var(--text-secondary)' }}>({r.bateria.vbat}V / {r.bateria.capacidad_ah}Ah)</span></div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.25rem' }}>
            Voltaje de sistema: {r.voltaje_sistema}V · HSP: {r.hsp} h · Potencia máx: {r.consumo.potencia_maxima_w} W · Potencia AC: {r.consumo.potencia_ac_w} W
          </div>
        </div>
      </div>

      {/* Inversores sugeridos */}
      <div className="glass-panel" style={{ padding: '1.25rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>Inversores sugeridos (para {r.potencia_inversor_w} W)</h3>
        {r.inversores_sugeridos.length === 0 ? (
          <p style={{ color: 'var(--text-secondary)' }}>No se encontraron inversores compatibles.</p>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr><th>Modelo</th><th>Marca</th><th>W c/u</th><th>Cant.</th><th>Potencia total</th></tr>
              </thead>
              <tbody>
                {r.inversores_sugeridos.map((inv, i) => (
                  <tr key={i}>
                    <td>{inv.modelo}</td>
                    <td>{inv.marca || '—'}</td>
                    <td>{inv.wout} W</td>
                    <td><strong>{inv.cantidad}</strong></td>
                    <td>{inv.potencia_total} W</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {!readOnly && (
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
          <button className="btn btn-primary" onClick={() => onNext()}>✓ Completar cálculo</button>
        </div>
      )}
    </div>
  );
}
