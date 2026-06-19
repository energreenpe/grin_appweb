import React, { useState, useEffect } from 'react';
import { useCalculoStore } from '../../../store/calculoStore';
import { mathApi } from '../../../api/mathApi';
import SearchableSelect from '../../SearchableSelect';

const normalizarTipoBateria = (tipo) =>
  (tipo || '').toLowerCase().includes('li') ? 'Lithium' : 'Lead acid';

export default function StepSeleccionAislado({ onNext }) {
  const { data, setData } = useCalculoStore();

  const [paneles, setPaneles] = useState([]);
  const [baterias, setBaterias] = useState([]);
  const [regionHsp, setRegionHsp] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const [pan, bat, regs] = await Promise.all([
          mathApi.getEquipos('panel'),
          mathApi.getEquipos('bateria'),
          mathApi.getRegiones(),
        ]);
        setPaneles(pan);
        setBaterias(bat);
        setRegionHsp(regs.find((r) => r.nombre === data.region) || null);
      } catch (e) {
        console.error('Error cargando equipos', e);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const hspActual = regionHsp ? regionHsp[`hsp_${data.tipo_hsp}`] : null;

  const handlePanel = (id) => {
    const panel = paneles.find((p) => p.id === Number(id)) || null;
    setData({ panel_id: panel ? panel.id : null, panel_info: panel });
  };

  const handleBateria = (id) => {
    const bateria = baterias.find((b) => b.id === Number(id)) || null;
    setData({
      bateria_id: bateria ? bateria.id : null,
      bateria_info: bateria,
      tipo_bateria: bateria ? normalizarTipoBateria(bateria.specs?.tipo) : data.tipo_bateria,
    });
  };

  const handleContinuar = () => {
    setError('');
    if (!data.panel_id) { setError('Selecciona un panel.'); return; }
    if (!data.bateria_id) { setError('Selecciona una batería.'); return; }
    onNext();
  };

  const labelStyle = { display: 'block', marginBottom: '0.4rem', color: 'var(--text-secondary)', fontSize: '0.9rem' };

  // Opciones de los selects (las etiquetas conservan todos los datos).
  const hspOptions = [
    { value: 'minimo', label: `Mínimo${regionHsp ? ` (${regionHsp.hsp_minimo})` : ''}` },
    { value: 'promedio', label: `Promedio${regionHsp ? ` (${regionHsp.hsp_promedio})` : ''}` },
    { value: 'mayor', label: `Mayor${regionHsp ? ` (${regionHsp.hsp_mayor})` : ''}` },
  ];
  const panelOptions = paneles.map((p) => ({ value: p.id, label: `${p.descripcion} — ${p.specs?.Potencia} Wp` }));
  const bateriaOptions = baterias.map((b) => ({ value: b.id, label: `${b.descripcion} — ${b.specs?.Vbat}V / ${b.specs?.capacidad}Ah` }));
  const voltajeOptions = [
    { value: '', label: 'Automático (según consumo)' },
    { value: 12, label: '12 V' },
    { value: 24, label: '24 V' },
    { value: 48, label: '48 V' },
  ];

  return (
    <div style={{ maxWidth: '640px', margin: '0 auto' }}>
      <h2 style={{ marginBottom: '1.5rem', textAlign: 'center' }}>Selección de Equipos</h2>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {/* Días de autonomía + HSP */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', minWidth: 0 }}>
          <div style={{ minWidth: 0 }}>
            <label style={labelStyle}>Días de autonomía</label>
            <input
              type="number" min="1" max="15" className="input-field"
              value={data.dias_autonomia}
              onChange={(e) => setData({ dias_autonomia: Number(e.target.value) })}
            />
          </div>
          <div style={{ minWidth: 0 }}>
            <label style={labelStyle}>HSP a usar (región {data.region})</label>
            <SearchableSelect options={hspOptions} value={data.tipo_hsp} onChange={(v) => setData({ tipo_hsp: v })} placeholder="HSP…" />
          </div>
        </div>
        {hspActual != null && (
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '-0.5rem' }}>
            HSP seleccionado: <strong style={{ color: 'var(--primary-color)' }}>{hspActual}</strong> h
          </div>
        )}

        {/* Panel */}
        <div>
          <label style={labelStyle}>Panel solar</label>
          <SearchableSelect options={panelOptions} value={data.panel_id ?? ''} onChange={handlePanel} placeholder="Selecciona un panel…" />
        </div>

        {/* Batería */}
        <div>
          <label style={labelStyle}>Batería</label>
          <SearchableSelect options={bateriaOptions} value={data.bateria_id ?? ''} onChange={handleBateria} placeholder="Selecciona una batería…" />
          {data.bateria_id && (
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.4rem' }}>
              Tipo detectado: <strong>{data.tipo_bateria}</strong> (DoD y eficiencia se ajustan según el tipo)
            </div>
          )}
        </div>

        {/* Voltaje de sistema (override opcional) */}
        <div>
          <label style={labelStyle}>Voltaje de sistema</label>
          <SearchableSelect
            options={voltajeOptions}
            value={data.voltaje_sistema ?? ''}
            onChange={(v) => setData({ voltaje_sistema: v ? Number(v) : null })}
            placeholder="Automático (según consumo)"
          />
        </div>

        {error && (
          <div style={{ background: 'rgba(220,50,50,0.12)', border: '1px solid rgba(220,50,50,0.4)', borderRadius: '8px', padding: '0.75rem 1rem', color: '#ff6b6b', fontSize: '0.9rem' }}>
            ⚠️ {error}
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button className="btn btn-primary" onClick={handleContinuar}>Calcular →</button>
        </div>
      </div>
    </div>
  );
}
