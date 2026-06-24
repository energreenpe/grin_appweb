import { useEffect, useState } from 'react';
import { getCuadrillas, createCuadrilla, deleteCuadrilla, getPersonal, createPersona, deletePersona, asignarMiembro, removerMiembro, cambiarCuadrilla } from '../api/plannerApi';
import { rolBadge, estadoBadge } from '../utils/estilos';

const ROLES = ['Jefe de Cuadrilla', 'Capataz', 'Técnico', 'Instalador', 'Operario', 'Peón', 'Supervisor', 'Ingeniero', 'Otro'];
const PROFESIONES = ['Ingeniero Eléctrico', 'Ingeniero Civil', 'Técnico Electricista', 'Técnico en Energía Solar', 'Instalador de Paneles Solares', 'Instalador Eléctrico', 'Operario de Montaje', 'Operario de Cableado', 'Supervisor de Obra', 'Jefe de Cuadrilla', 'Otro'];

const iniciales = (n) => (n || '').split(' ').map((x) => x[0]).slice(0, 2).join('');

export default function CuadrillaTab({ proyectoId }) {
  const [cuadrillas, setCuadrillas] = useState([]);
  const [personal, setPersonal] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('cuadrillas');

  const [showNuevaCuadrilla, setShowNuevaCuadrilla] = useState(false);
  const [nombreCuadrilla, setNombreCuadrilla] = useState('');
  const [showNuevaPersona, setShowNuevaPersona] = useState(false);
  const [formPersona, setFormPersona] = useState({ nombre: '', dni: '', celular: '', profesion: 'Técnico Electricista', estado: 'Activo' });
  const [showAsignar, setShowAsignar] = useState(null);
  const [asignarForm, setAsignarForm] = useState({ persona_id: '', rol_interno: 'Técnico' });
  const [showCambiar, setShowCambiar] = useState(null);
  const [cambiarForm, setCambiarForm] = useState({ nueva_cuadrilla_id: '', rol_interno: 'Técnico' });

  const cargar = async () => {
    setLoading(true);
    const [cRes, pRes] = await Promise.all([getCuadrillas(proyectoId), getPersonal()]);
    setCuadrillas(cRes.data); setPersonal(pRes.data); setLoading(false);
  };
  useEffect(() => { cargar(); /* eslint-disable-next-line */ }, [proyectoId]);

  const handleNuevaCuadrilla = async (e) => { e.preventDefault(); await createCuadrilla({ proyecto_id: proyectoId, nombre: nombreCuadrilla }); setShowNuevaCuadrilla(false); setNombreCuadrilla(''); cargar(); };
  const handleNuevaPersona = async (e) => { e.preventDefault(); await createPersona(formPersona); setShowNuevaPersona(false); setFormPersona({ nombre: '', dni: '', celular: '', profesion: 'Técnico Electricista', estado: 'Activo' }); cargar(); };
  const handleAsignar = async (e) => { e.preventDefault(); await asignarMiembro(showAsignar, { persona_id: Number(asignarForm.persona_id), rol_interno: asignarForm.rol_interno }); setShowAsignar(null); setAsignarForm({ persona_id: '', rol_interno: 'Técnico' }); cargar(); };
  const handleCambiar = async (e) => { e.preventDefault(); await cambiarCuadrilla(showCambiar, { nueva_cuadrilla_id: Number(cambiarForm.nueva_cuadrilla_id), rol_interno: cambiarForm.rol_interno }); setShowCambiar(null); setCambiarForm({ nueva_cuadrilla_id: '', rol_interno: 'Técnico' }); cargar(); };
  const handleRemover = async (mid) => { if (!window.confirm('¿Remover de esta cuadrilla?')) return; await removerMiembro(mid); cargar(); };
  const handleEliminarCuadrilla = async (id) => { if (!window.confirm('¿Eliminar esta cuadrilla y sus miembros?')) return; await deleteCuadrilla(id); cargar(); };
  const handleEliminarPersona = async (id) => { if (!window.confirm('¿Eliminar esta persona del sistema?')) return; try { await deletePersona(id); cargar(); } catch { window.alert('No se puede eliminar, puede estar asignada a una cuadrilla.'); } };

  return (
    <div className="pl-page">
      <div className="pl-between">
        <div className="pl-row" style={{ gap: '.25rem' }}>
          {[['cuadrillas', '👥 Cuadrillas'], ['personal', '🧑 Todo el Personal']].map(([k, l]) => (
            <button key={k} onClick={() => setTab(k)} className={`pl-btn pl-btn-sm ${tab === k ? 'pl-btn-primary' : 'pl-btn-outline'}`}>{l}</button>
          ))}
        </div>
        {tab === 'cuadrillas'
          ? <button className="pl-btn pl-btn-primary pl-btn-sm" onClick={() => setShowNuevaCuadrilla(true)}>+ Nueva Cuadrilla</button>
          : <button className="pl-btn pl-btn-primary pl-btn-sm" onClick={() => setShowNuevaPersona(true)}>+ Nueva Persona</button>}
      </div>

      {showNuevaCuadrilla && (
        <form onSubmit={handleNuevaCuadrilla} className="pl-card pl-card-pad pl-row" style={{ gap: '.5rem' }}>
          <input className="pl-input" required value={nombreCuadrilla} onChange={(e) => setNombreCuadrilla(e.target.value)} placeholder="Nombre de la cuadrilla (ej: Cuadrilla 1)" style={{ flex: 1 }} />
          <button type="button" className="pl-btn pl-btn-outline" onClick={() => setShowNuevaCuadrilla(false)}>Cancelar</button>
          <button type="submit" className="pl-btn pl-btn-primary">Crear</button>
        </form>
      )}

      {showNuevaPersona && (
        <form onSubmit={handleNuevaPersona} className="pl-card pl-card-pad">
          <div className="pl-grid pl-grid-2" style={{ marginBottom: '.5rem' }}>
            <input className="pl-input" required value={formPersona.nombre} onChange={(e) => setFormPersona((f) => ({ ...f, nombre: e.target.value }))} placeholder="Nombre completo *" style={{ gridColumn: '1 / -1' }} />
            <input className="pl-input" value={formPersona.dni} onChange={(e) => setFormPersona((f) => ({ ...f, dni: e.target.value }))} placeholder="DNI" />
            <input className="pl-input" value={formPersona.celular} onChange={(e) => setFormPersona((f) => ({ ...f, celular: e.target.value }))} placeholder="Celular" />
            <select className="pl-select" value={formPersona.profesion} onChange={(e) => setFormPersona((f) => ({ ...f, profesion: e.target.value }))} style={{ gridColumn: '1 / -1' }}>
              {PROFESIONES.map((p) => <option key={p}>{p}</option>)}
            </select>
          </div>
          <div className="pl-row" style={{ gap: '.5rem' }}>
            <button type="button" className="pl-btn pl-btn-outline" style={{ flex: 1 }} onClick={() => setShowNuevaPersona(false)}>Cancelar</button>
            <button type="submit" className="pl-btn pl-btn-primary" style={{ flex: 1 }}>Crear</button>
          </div>
        </form>
      )}

      {loading ? <p className="pl-empty">Cargando...</p>
        : tab === 'cuadrillas' ? (
          <div className="pl-page">
            {cuadrillas.length === 0 ? (
              <div className="pl-empty"><div className="pl-empty-icon">👥</div><p>Sin cuadrillas. Crea la primera.</p></div>
            ) : cuadrillas.map((c) => (
              <div key={c.id} className="pl-card" style={{ overflow: 'hidden' }}>
                <div className="pl-between" style={{ padding: '.75rem 1rem', background: 'var(--bg-color)', borderBottom: '1px solid var(--border-color)' }}>
                  <div>
                    <h3 className="pl-h3" style={{ margin: 0 }}>{c.nombre}</h3>
                    {c.descripcion && <p className="pl-muted" style={{ fontSize: '.72rem' }}>{c.descripcion}</p>}
                  </div>
                  <div className="pl-row">
                    <button className="pl-btn pl-btn-outline pl-btn-sm" onClick={() => setShowAsignar(c.id)}>+ Asignar persona</button>
                    <button className="pl-link pl-link-danger" onClick={() => handleEliminarCuadrilla(c.id)}>✕</button>
                  </div>
                </div>

                {showAsignar === c.id && (
                  <form onSubmit={handleAsignar} className="pl-row" style={{ padding: '.75rem', borderBottom: '1px solid var(--border-color)', background: 'rgba(98,185,137,.06)', alignItems: 'flex-end' }}>
                    <select className="pl-select" required value={asignarForm.persona_id} onChange={(e) => setAsignarForm((f) => ({ ...f, persona_id: e.target.value }))} style={{ flex: 1, minWidth: 130 }}>
                      <option value="">Seleccionar persona</option>
                      {personal.map((p) => <option key={p.id} value={p.id}>{p.nombre}</option>)}
                    </select>
                    <select className="pl-select" value={asignarForm.rol_interno} onChange={(e) => setAsignarForm((f) => ({ ...f, rol_interno: e.target.value }))} style={{ width: 'auto' }}>
                      {ROLES.map((r) => <option key={r}>{r}</option>)}
                    </select>
                    <button type="button" className="pl-btn pl-btn-outline pl-btn-sm" onClick={() => setShowAsignar(null)}>Cancelar</button>
                    <button type="submit" className="pl-btn pl-btn-primary pl-btn-sm">Asignar</button>
                  </form>
                )}

                {c.miembros?.filter((m) => m.activo).length === 0 ? (
                  <p className="pl-muted" style={{ padding: '.75rem 1rem', fontSize: '.85rem' }}>Sin miembros asignados</p>
                ) : c.miembros.filter((m) => m.activo).map((m) => (
                  <div key={m.id} className="pl-row" style={{ padding: '.6rem 1rem', borderTop: '1px solid var(--border-color)', gap: '.75rem' }}>
                    <div className="pl-avatar">{iniciales(m.nombre_persona)}</div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <p style={{ fontSize: '.85rem', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{m.nombre_persona}</p>
                      <p className="pl-muted" style={{ fontSize: '.72rem' }}>{m.profesion}</p>
                    </div>
                    <span className="pl-badge" style={rolBadge(m.rol_interno)}>{m.rol_interno}</span>
                    <button className="pl-link" onClick={() => { setShowCambiar(m.id); setCambiarForm({ nueva_cuadrilla_id: '', rol_interno: m.rol_interno }); }}>Mover</button>
                    <button className="pl-link pl-link-danger" onClick={() => handleRemover(m.id)}>✕</button>
                  </div>
                ))}
              </div>
            ))}

            {showCambiar && (
              <div className="pl-modal-overlay" onClick={() => setShowCambiar(null)}>
                <div className="pl-modal pl-modal-sm" onClick={(e) => e.stopPropagation()}>
                  <div className="pl-modal-head"><h3 className="pl-h2">Mover a otra cuadrilla</h3><button className="pl-x" onClick={() => setShowCambiar(null)}>✕</button></div>
                  <form onSubmit={handleCambiar} className="pl-modal-body">
                    <select className="pl-select" required value={cambiarForm.nueva_cuadrilla_id} onChange={(e) => setCambiarForm((f) => ({ ...f, nueva_cuadrilla_id: e.target.value }))}>
                      <option value="">Seleccionar nueva cuadrilla</option>
                      {cuadrillas.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
                    </select>
                    <select className="pl-select" value={cambiarForm.rol_interno} onChange={(e) => setCambiarForm((f) => ({ ...f, rol_interno: e.target.value }))}>
                      {ROLES.map((r) => <option key={r}>{r}</option>)}
                    </select>
                    <div className="pl-row" style={{ gap: '.5rem' }}>
                      <button type="button" className="pl-btn pl-btn-outline" style={{ flex: 1 }} onClick={() => setShowCambiar(null)}>Cancelar</button>
                      <button type="submit" className="pl-btn pl-btn-primary" style={{ flex: 1 }}>Mover</button>
                    </div>
                  </form>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '.5rem' }}>
            {personal.length === 0 ? <div className="pl-empty"><div className="pl-empty-icon">🧑</div><p>Sin personal registrado.</p></div>
              : personal.map((p) => (
                <div key={p.id} className="pl-card pl-card-pad pl-row" style={{ gap: '.75rem' }}>
                  <div className="pl-avatar" style={{ background: 'rgba(122,183,255,.15)', color: '#7ab7ff' }}>{iniciales(p.nombre)}</div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ fontSize: '.85rem', fontWeight: 600 }}>{p.nombre}</p>
                    <p className="pl-muted" style={{ fontSize: '.72rem' }}>{p.profesion} · DNI: {p.dni || '—'} · {p.celular || '—'}</p>
                  </div>
                  <span className="pl-badge" style={estadoBadge(p.estado === 'Activo' ? 'Completado' : 'Pendiente')}>{p.estado}</span>
                  <button className="pl-link pl-link-danger" onClick={() => handleEliminarPersona(p.id)}>✕</button>
                </div>
              ))}
          </div>
        )}
    </div>
  );
}
