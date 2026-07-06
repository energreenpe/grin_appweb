import React, { useState, useEffect } from 'react';
import { useCalculoStore } from '../../../store/calculoStore';
import { mathApi } from '../../../api/mathApi';
import SearchableSelect from '../../../../../components/SearchableSelect';

const TIPO_CONEXION_OPTS = [
  { value: 'Monofásico', label: 'Monofásico' },
  { value: 'Trifásico', label: 'Trifásico' },
];
const VOLTAJE_OPTS = [
  { value: '220', label: '220' },
  { value: '380', label: '380' },
];

// Ayuda por campo: imagen fija (frontend) o texto.
const HELP = {
  tipo_conexion: { title: 'Tipo de conexión', img: '/math/tipoconexion.png' },
  voltaje_red: { title: 'Voltaje de Red', img: '/math/voltajered.png' },
  consumo_mensual: { title: 'Consumo Mensual', img: '/math/consumomensual.png' },
  potencia_contratada: { title: 'Potencia Contratada', img: '/math/potenciacontratada.png' },
  autarquia: {
    title: 'Autarquía',
    text: 'Porcentaje de la energía que deseas cubrir con el sistema solar. ' +
      'Valores típicos entre 30% y 70%; a mayor autarquía, mayor inversión inicial.',
  },
};

function HelpBtn({ onClick }) {
  return (
    <button type="button" onClick={onClick} title="Ayuda"
      style={{ width: '32px', height: '32px', borderRadius: '50%', background: '#8ecae6',
        color: '#023047', border: 'none', fontWeight: 'bold', cursor: 'pointer', flexShrink: 0 }}>
      ?
    </button>
  );
}

export default function StepSeleccionAutoconsumo({ onNext }) {
  const { data, setData } = useCalculoStore();

  const [paneles, setPaneles] = useState([]);
  const [inversores, setInversores] = useState([]);
  const [error, setError] = useState('');
  const [help, setHelp] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const [pan, inv] = await Promise.all([
          mathApi.getEquipos('panel'),
          mathApi.getEquipos('inversor_autoconsumo'),
        ]);
        setPaneles(pan);
        setInversores(inv);
      } catch (e) {
        console.error('Error cargando equipos', e);
      }
    })();
  }, []);

  // Inversores filtrados por tipo de conexión + voltaje de red (como el legacy).
  const inversoresFiltrados = inversores.filter((i) =>
    (i.specs?.tipo_conexion || '').toLowerCase() === (data.tipo_conexion || '').toLowerCase() &&
    String(i.specs?.Vgrid) === String(data.voltaje_red)
  );
  const panelOptions = paneles.map((p) => ({ value: p.id, label: `${p.descripcion} — ${p.specs?.Potencia} Wp` }));
  const inversorOptions = inversoresFiltrados.map((i) => ({ value: i.id, label: `${i.descripcion} — ${i.specs?.Wout} W` }));

  const handlePanel = (id) => {
    const p = paneles.find((x) => x.id === Number(id)) || null;
    setData({ panel_id: p ? p.id : null, panel_info: p });
  };
  const handleInversor = (id) => {
    const i = inversores.find((x) => x.id === Number(id)) || null;
    setData({ inversor_id: i ? i.id : null, inversor_info: i });
  };
  // Al cambiar conexión/voltaje se limpia el inversor (la lista filtrada cambia).
  const handleConexion = (v) => setData({ tipo_conexion: v, inversor_id: null, inversor_info: null });
  const handleVoltaje = (v) => setData({ voltaje_red: v, inversor_id: null, inversor_info: null });

  const handleContinuar = () => {
    setError('');
    if (!data.consumo_mensual || Number(data.consumo_mensual) <= 0) { setError('Ingresa el Consumo Mensual (kWh) mayor a 0.'); return; }
    if (data.potencia_contratada === '' || Number(data.potencia_contratada) < 0) { setError('Ingresa la Potencia Contratada (kW).'); return; }
    if (!data.panel_id) { setError('Selecciona un panel solar.'); return; }
    if (!data.inversor_id) { setError('Selecciona un inversor.'); return; }
    onNext();
  };

  const labelStyle = { display: 'block', marginBottom: '0.4rem', color: 'var(--text-secondary)', fontSize: '0.9rem' };
  const rowConHelp = (children, helpKey) => (
    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
      <div style={{ flex: 1, minWidth: 0 }}>{children}</div>
      <HelpBtn onClick={() => setHelp(HELP[helpKey])} />
    </div>
  );

  return (
    <div style={{ maxWidth: '640px', margin: '0 auto' }}>
      <h2 style={{ marginBottom: '0.5rem', textAlign: 'center' }}>Gestión de Autoconsumo</h2>
      <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
        Completa los datos y elige el panel e inversor. El motor calculará 3 configuraciones.
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>
        <div>
          <label style={labelStyle}>Tipo de conexión</label>
          {rowConHelp(
            <SearchableSelect options={TIPO_CONEXION_OPTS} value={data.tipo_conexion} onChange={handleConexion} placeholder="Tipo de conexión" />,
            'tipo_conexion')}
        </div>

        <div>
          <label style={labelStyle}>Voltaje de Red</label>
          {rowConHelp(
            <SearchableSelect options={VOLTAJE_OPTS} value={data.voltaje_red} onChange={handleVoltaje} placeholder="Voltaje de red" />,
            'voltaje_red')}
        </div>

        <div>
          <label style={labelStyle}>Consumo Mensual (kWh)</label>
          {rowConHelp(
            <input type="number" min="0" step="0.01" className="input-field" placeholder="Ej. 300"
              value={data.consumo_mensual} onChange={(e) => setData({ consumo_mensual: e.target.value })} />,
            'consumo_mensual')}
        </div>

        <div>
          <label style={labelStyle}>Potencia Contratada (kW)</label>
          {rowConHelp(
            <input type="number" min="0" step="0.01" className="input-field" placeholder="Ej. 5.0"
              value={data.potencia_contratada} onChange={(e) => setData({ potencia_contratada: e.target.value })} />,
            'potencia_contratada')}
        </div>

        <div>
          <label style={labelStyle}>Autarquía (%)</label>
          {rowConHelp(
            <input type="number" min="0" max="100" step="1" className="input-field"
              value={data.autarquia} onChange={(e) => setData({ autarquia: Number(e.target.value) })} />,
            'autarquia')}
        </div>

        <div>
          <label style={labelStyle}>Panel Solar</label>
          <SearchableSelect options={panelOptions} value={data.panel_id ?? ''} onChange={handlePanel} placeholder="Selecciona un panel…" />
        </div>

        <div>
          <label style={labelStyle}>Inversor</label>
          <SearchableSelect options={inversorOptions} value={data.inversor_id ?? ''} onChange={handleInversor} placeholder="Selecciona un inversor…" />
          {inversorOptions.length === 0 && (
            <div style={{ fontSize: '0.8rem', color: '#ffc107', marginTop: '0.4rem' }}>
              No hay inversores para {data.tipo_conexion} / {data.voltaje_red}V. Cambia el tipo de conexión o el voltaje.
            </div>
          )}
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

      {/* Modal de ayuda (imagen fija o texto) */}
      {help && (
        <div onClick={() => setHelp(null)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
          <div onClick={(e) => e.stopPropagation()} className="glass-panel"
            style={{ padding: '1rem', maxWidth: '92vw', maxHeight: '90vh', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
              <strong>{help.title}</strong>
              <button onClick={() => setHelp(null)} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', fontSize: '1.3rem', cursor: 'pointer' }}>✕</button>
            </div>
            {help.img ? (
              <img src={help.img} alt={help.title} style={{ maxWidth: '100%', maxHeight: '75vh', objectFit: 'contain', borderRadius: '8px' }} />
            ) : (
              <p style={{ maxWidth: '420px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{help.text}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
