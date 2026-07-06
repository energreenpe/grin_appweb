import React from 'react';
import { useCalculoStore } from '../../../store/calculoStore';

const TARGET_LABEL = { min: 'Mínima', opt: 'Óptima', max: 'Máxima' };

export default function ResultadoAutoconsumo({ onNext, readOnly = false }) {
  const { data, setData } = useCalculoStore();
  const r = data.resultado;

  if (!r || !r.opciones) {
    return <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>Calculando…</div>;
  }

  const elegir = (target) => { if (!readOnly) setData({ opcion_elegida: target }); };
  const opcionSel = r.opciones.find((o) => o.target === data.opcion_elegida) || null;

  return (
    <div>
      <h2 style={{ marginBottom: '0.5rem', textAlign: 'center' }}>Configuraciones — Autoconsumo</h2>
      <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
        {data.nombre_proyecto} · Elige una opción para definir el nº de paneles
      </p>

      {/* Equipos elegidos */}
      <div className="glass-panel" style={{ padding: '1.25rem', marginBottom: '1rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
        <div>☀️ {r.panel.descripcion} <span style={{ color: 'var(--text-secondary)' }}>({r.panel.potencia_w} Wp)</span></div>
        <div>🔌 {r.inversor.descripcion} <span style={{ color: 'var(--text-secondary)' }}>({r.inversor.wout_w} W)</span></div>
      </div>

      {r.parametros && (
        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
          Consumo: <strong>{r.parametros.consumo_mensual}</strong> kWh/mes · Potencia contratada: <strong>{r.parametros.potencia_contratada}</strong> kW ·
          Autarquía: <strong>{r.parametros.autarquia}%</strong> · Potencia mínima: <strong>{r.parametros.potencia_minima_kw}</strong> kW
        </div>
      )}

      {/* Tabla de 3 opciones */}
      <div className="glass-panel" style={{ padding: '1.25rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>Opciones de configuración</h3>
        <div className="table-container">
          <table style={{ minWidth: '520px' }}>
            <thead>
              <tr>
                <th></th>
                <th>Opción</th>
                <th>Paneles serie</th>
                <th>Total paneles</th>
                <th>Potencia</th>
                <th>Ratio DC/AC</th>
              </tr>
            </thead>
            <tbody>
              {r.opciones.map((o) => {
                const sel = data.opcion_elegida === o.target;
                const bg = sel ? 'rgba(98,185,137,0.15)' : (o.excede_contratada ? 'rgba(220,50,50,0.12)' : 'transparent');
                return (
                  <tr key={o.target} onClick={() => elegir(o.target)} style={{ cursor: 'pointer', background: bg }}>
                    <td><input type="radio" name="opcion-ac" checked={sel} onChange={() => elegir(o.target)} /></td>
                    <td><strong style={{ color: sel ? 'var(--primary-color)' : 'inherit' }}>{TARGET_LABEL[o.target]}</strong></td>
                    <td>{o.paneles_serie}</td>
                    <td><strong>{o.paneles_total}</strong></td>
                    <td>{o.potencia_sistema_kW} kW {o.excede_contratada && <span title="Excede la potencia contratada">⚠️</span>}</td>
                    <td>{o.ratio_dc_ac}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {r.opciones.some((o) => o.excede_contratada) && (
          <div style={{ fontSize: '0.8rem', color: '#ff6b6b', marginTop: '0.75rem' }}>
            ⚠️ Las opciones marcadas exceden la potencia contratada ({r.parametros?.potencia_contratada} kW).
          </div>
        )}
      </div>

      {/* Resumen de la opción elegida */}
      {opcionSel && (
        <div className="glass-panel" style={{ padding: '1.25rem', marginTop: '1rem', border: '1px solid rgba(98,185,137,0.35)' }}>
          <div style={{ fontWeight: 700, color: 'var(--primary-color)', marginBottom: '0.5rem' }}>
            Opción {TARGET_LABEL[opcionSel.target]} seleccionada
          </div>
          <div>☀️ <strong>{opcionSel.paneles_total} ×</strong> {r.panel.descripcion}</div>
          <div>🔌 <strong>1 ×</strong> {r.inversor.descripcion}</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.25rem' }}>
            Potencia del sistema: {opcionSel.potencia_sistema_kW} kW · Ratio DC/AC: {opcionSel.ratio_dc_ac}
          </div>
        </div>
      )}

      {!readOnly && (
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
          <button
            className="btn btn-primary"
            onClick={() => onNext()}
            disabled={!data.opcion_elegida}
            style={{ opacity: data.opcion_elegida ? 1 : 0.5, cursor: data.opcion_elegida ? 'pointer' : 'not-allowed' }}
          >
            ✓ Completar cálculo
          </button>
        </div>
      )}
    </div>
  );
}
