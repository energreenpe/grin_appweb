import { useEffect, useState } from 'react';
import { getAsistencia, bulkAsistencia, deleteAsistencia, getCuadrillas } from '../api/plannerApi';
import { asistenciaBadge } from '../utils/estilos';

const hoy = () => new Date().toISOString().split('T')[0];
const ESTADO_BTN = {
  Presente: { background: '#3a7a52', color: '#fff', border: '#3a7a52' },
  Tardanza: { background: '#a07d1a', color: '#fff', border: '#a07d1a' },
  Ausente: { background: '#a33', color: '#fff', border: '#a33' },
};

export default function AsistenciaTab({ proyectoId }) {
  const [registros, setRegistros] = useState([]);
  const [cuadrillas, setCuadrillas] = useState([]);
  const [fecha, setFecha] = useState(hoy());
  const [cuadrillaFil, setCuadrillaFil] = useState('');
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [marcas, setMarcas] = useState({});
  const [guardando, setGuardando] = useState(false);

  const cargar = async () => {
    setLoading(true);
    const [rRes, cRes] = await Promise.all([
      getAsistencia(proyectoId, { fecha }),
      getCuadrillas(proyectoId),
    ]);
    let regs = rRes.data;
    if (cuadrillaFil) regs = regs.filter((r) => String(r.cuadrilla_id) === String(cuadrillaFil));
    setRegistros(regs);
    setCuadrillas(cRes.data);
    setLoading(false);
  };

  useEffect(() => { cargar(); /* eslint-disable-next-line */ }, [proyectoId, fecha, cuadrillaFil]);

  const abrirForm = () => {
    const init = {};
    cuadrillas.forEach((c) => {
      c.miembros?.filter((m) => m.activo).forEach((m) => {
        const ex = registros.find((r) => r.persona_id === m.persona_id);
        init[`${c.id}_${m.persona_id}`] = {
          persona_id: m.persona_id, cuadrilla_id: c.id, nombre: m.nombre_persona,
          estado: ex?.estado || 'Presente',
          hora: ex?.hora || new Date().toTimeString().slice(0, 5),
          observacion: ex?.observacion || '',
        };
      });
    });
    setMarcas(init);
    setShowForm(true);
  };

  const handleGuardar = async () => {
    setGuardando(true);
    try {
      const registros_payload = Object.values(marcas).map((m) => ({
        persona_id: m.persona_id, estado: m.estado, hora: m.hora, observacion: m.observacion,
      }));
      await bulkAsistencia({ proyecto_id: proyectoId, fecha, registros: registros_payload });
      setShowForm(false); cargar();
    } catch { window.alert('Error al guardar'); }
    finally { setGuardando(false); }
  };

  const resumen = {
    presentes: registros.filter((r) => r.estado === 'Presente').length,
    tardanzas: registros.filter((r) => r.estado === 'Tardanza').length,
    ausentes: registros.filter((r) => r.estado === 'Ausente').length,
  };
  const totalMiembros = cuadrillas.reduce((acc, c) => acc + (c.miembros?.filter((m) => m.activo).length || 0), 0);

  return (
    <div className="pl-page">
      <div className="pl-between">
        <div className="pl-row">
          <h2 className="pl-h2">Asistencia Diaria</h2>
          <input className="pl-input" style={{ width: 'auto' }} type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} />
          <select className="pl-select" style={{ width: 'auto' }} value={cuadrillaFil} onChange={(e) => setCuadrillaFil(e.target.value)}>
            <option value="">Todas las cuadrillas</option>
            {cuadrillas.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
          </select>
        </div>
        <button className="pl-btn pl-btn-primary" onClick={abrirForm} disabled={totalMiembros === 0}>📝 Registrar Asistencia</button>
      </div>

      {registros.length > 0 && (
        <div className="pl-grid pl-grid-3">
          {[['Presentes', resumen.presentes, '#62B989'], ['Tardanzas', resumen.tardanzas, '#f0b429'], ['Ausentes', resumen.ausentes, '#ff8a8a']].map(([l, v, c]) => (
            <div key={l} className="pl-kpi" style={{ textAlign: 'center' }}>
              <p className="pl-kpi-value" style={{ color: c }}>{v}</p>
              <p className="pl-kpi-label" style={{ color: c }}>{l}</p>
            </div>
          ))}
        </div>
      )}

      {showForm && (
        <div className="pl-card pl-card-pad">
          <h3 className="pl-h3">📅 Asistencia del {fecha}</h3>
          <div style={{ maxHeight: 320, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1rem' }}>
            {cuadrillas.map((c) => (
              <div key={c.id}>
                <p className="pl-muted" style={{ fontSize: '.72rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '.5rem' }}>{c.nombre}</p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '.5rem' }}>
                  {c.miembros?.filter((m) => m.activo).map((m) => {
                    const key = `${c.id}_${m.persona_id}`;
                    const mk = marcas[key] || {};
                    return (
                      <div key={key} className="pl-card pl-card-pad" style={{ background: 'var(--bg-color)' }}>
                        <p style={{ fontSize: '.85rem', fontWeight: 600, marginBottom: '.5rem' }}>{m.nombre_persona}
                          <span className="pl-muted" style={{ fontSize: '.72rem', marginLeft: '.5rem' }}>{m.rol_interno}</span>
                        </p>
                        <div className="pl-row">
                          {['Presente', 'Tardanza', 'Ausente'].map((e) => {
                            const active = mk.estado === e;
                            return (
                              <button key={e} type="button" onClick={() => setMarcas((p) => ({ ...p, [key]: { ...p[key], estado: e } }))}
                                className="pl-btn pl-btn-sm"
                                style={active
                                  ? { background: ESTADO_BTN[e].background, color: ESTADO_BTN[e].color, border: `1px solid ${ESTADO_BTN[e].border}` }
                                  : { background: 'transparent', color: 'var(--text-secondary)', border: '1px solid var(--border-color)' }}>
                                {e}
                              </button>
                            );
                          })}
                          <input className="pl-input" style={{ width: 'auto' }} type="time" value={mk.hora || ''} onChange={(e) => setMarcas((p) => ({ ...p, [key]: { ...p[key], hora: e.target.value } }))} />
                          <input className="pl-input" style={{ flex: 1, minWidth: 100 }} value={mk.observacion || ''} placeholder="Observación" onChange={(e) => setMarcas((p) => ({ ...p, [key]: { ...p[key], observacion: e.target.value } }))} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
          <div className="pl-row" style={{ gap: '.5rem' }}>
            <button className="pl-btn pl-btn-outline" style={{ flex: 1 }} onClick={() => setShowForm(false)}>Cancelar</button>
            <button className="pl-btn pl-btn-primary" style={{ flex: 1 }} onClick={handleGuardar} disabled={guardando}>{guardando ? 'Guardando...' : 'Guardar Asistencia'}</button>
          </div>
        </div>
      )}

      {loading ? <p className="pl-empty">Cargando...</p>
        : registros.length === 0 ? <p className="pl-empty">Sin registros para {fecha}.</p>
          : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '.5rem' }}>
              {registros.map((r) => (
                <div key={r.id} className="pl-card pl-card-pad pl-row" style={{ gap: '.75rem' }}>
                  <span className="pl-badge" style={asistenciaBadge(r.estado)}>{r.estado}</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ fontSize: '.85rem', fontWeight: 600 }}>{r.nombre_persona || `Persona #${r.persona_id}`}</p>
                    <p className="pl-muted" style={{ fontSize: '.72rem' }}>🕐 {r.hora || '—'} · {r.observacion || 'Sin observación'}</p>
                  </div>
                  <button className="pl-link pl-link-danger" onClick={() => { if (window.confirm('¿Eliminar?')) deleteAsistencia(r.id).then(cargar); }}>✕</button>
                </div>
              ))}
            </div>
          )}
    </div>
  );
}
