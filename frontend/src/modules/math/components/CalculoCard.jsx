import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { mathApi } from '../api/mathApi';
import { useCalculoStore } from '../store/calculoStore';
import { buildHistory } from '../wizardSteps';
import { notify } from '../../../lib/notify';

export default function CalculoCard({ calculo, onChange }) {
  const { id, nombre_proyecto, cliente, tipo_sistema, tipo_cliente, region, fecha, estado } = calculo;
  const dateObj = new Date(fecha);
  const navigate = useNavigate();
  const { setCalculoId, setData, resumeAt, setReadOnly } = useCalculoStore();
  const [loading, setLoading] = useState(false);

  const abrir = async () => {
    try {
      setLoading(true);
      const full = await mathApi.getCalculo(id);
      const entrada = full.entrada || {};
      const mapped = {
        nombre_proyecto: full.nombre_proyecto,
        tipo_cliente: full.tipo_cliente,
        cliente_id: full.cliente_id,
        cliente_info: full.cliente || null,
        ingeniero_id: full.ingeniero_id,
        ingeniero_info: full.ingeniero || null,
        region: full.region,
        tipo_sistema: full.tipo_sistema,
        cargas: entrada.cargas || [],
        dias_autonomia: entrada.dias_autonomia ?? 2,
        tipo_hsp: entrada.tipo_hsp || 'promedio',
        tipo_bateria: entrada.tipo_bateria || 'Lead acid',
        panel_id: entrada.panel_id || null,
        panel_info: null,
        bateria_id: entrada.bateria_id || null,
        bateria_info: null,
        voltaje_sistema: entrada.voltaje_sistema || null,
        // Autoconsumo
        inversor_id: entrada.inversor_id || null,
        inversor_info: null,
        tipo_conexion: entrada.tipo_conexion || 'Monofásico',
        voltaje_red: entrada.voltaje_red || '220',
        consumo_mensual: entrada.consumo_mensual ?? '',
        potencia_contratada: entrada.potencia_contratada ?? '',
        autarquia: entrada.autarquia ?? 40,
        opcion_elegida: entrada.opcion_elegida || null,
        resultado: full.resultado || null,
      };
      setCalculoId(full.id);
      setData(mapped);
      // Completado -> modo lectura, aterrizando en el paso de resultado (no en "done").
      const esCompletado = full.estado === 'completado';
      const resultStep = full.tipo_sistema === 'SFV Autoconsumo' ? 'resultado_auto' : 'resultado';
      const target = esCompletado ? resultStep : (full.paso_actual || 'inicio');
      setReadOnly(esCompletado);
      resumeAt(target, buildHistory(target, mapped));
      navigate('/math/new');
    } catch (err) {
      console.error('Error abriendo cálculo', err);
      notify('No se pudo abrir el cálculo. Revisa tu conexión.');
    } finally {
      setLoading(false);
    }
  };

  const eliminar = async () => {
    if (!window.confirm(`¿Eliminar el cálculo "${nombre_proyecto}"?`)) return;
    try {
      await mathApi.deleteCalculo(id);
      onChange?.();
    } catch (err) {
      console.error('Error eliminando cálculo', err);
      notify('No se pudo eliminar el cálculo.');
    }
  };

  return (
    <div className="glass-panel hover-bg" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
            {dateObj.toLocaleDateString()} {dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
          <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem' }}>{nombre_proyecto}</h3>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '12px', background: 'rgba(255,255,255,0.1)' }}>{tipo_cliente}</span>
            {tipo_sistema && (
              <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '12px', background: 'rgba(98,185,137,0.2)', color: 'var(--primary-color)' }}>{tipo_sistema}</span>
            )}
            <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '12px', background: estado === 'completado' ? 'rgba(98,185,137,0.1)' : 'rgba(255,193,7,0.1)' }}>
              {estado === 'borrador' ? '🔄 Borrador' : '✅ Completado'}
            </span>
          </div>
        </div>
        <button className={`btn ${estado === 'borrador' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ padding: '0.5rem 1rem' }} onClick={abrir} disabled={loading}>
          {loading ? 'Cargando...' : (estado === 'borrador' ? '▶ Continuar' : '👁 Ver')}
        </button>
      </div>

      <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
        <div>🧑 {cliente?.nombre || 'Sin cliente'}</div>
        <div>📍 {region || 'Sin región'}</div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <button className="btn" style={{ background: 'transparent', color: '#ff6b6b', padding: '0.25rem 0.5rem', fontSize: '0.85rem' }} onClick={eliminar}>
          🗑️ Eliminar
        </button>
      </div>
    </div>
  );
}
