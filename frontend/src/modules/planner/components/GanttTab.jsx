import { useEffect, useState } from 'react';
import { getActividades, createActividad, updateActividad, deleteActividad, recalcularGantt } from '../api/plannerApi';
import { estadoActividadBadge, prioridadColor } from '../utils/estilos';

const NIVEL_PAD = { 0: 0, 1: 12, 2: 24, 3: 36, 4: 48 };
const hoy = () => new Date().toISOString().split('T')[0];
const emptyForm = (pid) => ({
  proyecto_id: pid, titulo: '', nivel: 1, orden: 0,
  fecha_inicio_plan: hoy(), duracion_dias: 1,
  estado: 'Pendiente', prioridad: 'Media', subtareas: [], es_hito: false,
});

function GanttBar({ act, proyectoInicio, totalDias }) {
  if (!act.fecha_inicio_plan || !act.fecha_fin_plan || !proyectoInicio) return null;
  const ini = new Date(proyectoInicio);
  const offset = Math.max(0, (new Date(act.fecha_inicio_plan) - ini) / 86400000);
  const dur = Math.max(1, (new Date(act.fecha_fin_plan) - new Date(act.fecha_inicio_plan)) / 86400000);
  const left = (offset / totalDias) * 100;
  const width = (dur / totalDias) * 100;
  const color = act.avance >= 100 ? '#62B989' : '#7ab7ff';
  if (act.es_hito) {
    return <div style={{ position: 'relative', height: 20 }}>
      <div title={`${act.titulo}: ${act.fecha_inicio_plan}`} style={{ position: 'absolute', left: `${Math.min(left, 95)}%`, top: 4, width: 12, height: 12, background: '#c084fc', transform: 'rotate(45deg)' }} />
    </div>;
  }
  return (
    <div style={{ position: 'relative', height: 20 }}>
      <div title={`${act.titulo}: ${act.fecha_inicio_plan} → ${act.fecha_fin_plan}`}
        style={{ position: 'absolute', left: `${Math.min(left, 95)}%`, width: `${Math.max(width, 2)}%`, top: 4, height: 14, background: 'rgba(122,183,255,.3)', borderRadius: 4, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${act.avance}%`, background: color, borderRadius: 4 }} />
      </div>
    </div>
  );
}

export default function GanttTab({ proyectoId, proyecto, onRefresh }) {
  const [actividades, setActividades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm(proyectoId));
  const [editId, setEditId] = useState(null);
  const [nuevaSub, setNuevaSub] = useState('');
  const [vistaGantt, setVistaGantt] = useState(true);

  const cargar = async () => { setLoading(true); const res = await getActividades(proyectoId); setActividades(res.data); setLoading(false); };
  useEffect(() => { cargar(); /* eslint-disable-next-line */ }, [proyectoId]);

  const totalDias = proyecto?.fecha_inicio && proyecto?.fecha_fin
    ? Math.max(1, (new Date(proyecto.fecha_fin) - new Date(proyecto.fecha_inicio)) / 86400000) : 30;

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        proyecto_id: form.proyecto_id, titulo: form.titulo, nivel: Number(form.nivel),
        orden: Number(form.orden) || 0, fecha_inicio_plan: form.fecha_inicio_plan || null,
        duracion_dias: Number(form.duracion_dias) || 1, estado: form.estado, prioridad: form.prioridad,
        subtareas: form.subtareas || [], es_hito: form.es_hito || false, dependencias: [],
      };
      if (editId) await updateActividad(editId, payload);
      else await createActividad(payload);
      setShowForm(false); setEditId(null); setForm(emptyForm(proyectoId)); cargar(); onRefresh();
    } catch (err) {
      window.alert(err?.response?.data?.detail || 'Error al guardar la actividad');
    }
  };

  const handleEdit = (a) => { setForm({ ...a, subtareas: a.subtareas || [] }); setEditId(a.id); setShowForm(true); };
  const handleDelete = async (id) => { if (!window.confirm('¿Eliminar esta actividad y sus hijos?')) return; await deleteActividad(id); cargar(); onRefresh(); };
  const toggleSubtarea = async (act, idx) => {
    const subs = [...(act.subtareas || [])];
    subs[idx] = { ...subs[idx], hecho: !subs[idx].hecho };
    const completadas = subs.filter((s) => s.hecho).length;
    const avance = subs.length > 0 ? Math.round((completadas / subs.length) * 100) : 0;
    const estado = avance === 100 ? 'Completado' : avance > 0 ? 'En curso' : 'Pendiente';
    await updateActividad(act.id, { subtareas: subs, avance, estado }); cargar(); onRefresh();
  };
  const addSub = () => { if (!nuevaSub.trim()) return; setForm((f) => ({ ...f, subtareas: [...f.subtareas, { texto: nuevaSub.trim(), hecho: false }] })); setNuevaSub(''); };
  const handleRecalcular = async () => { await recalcularGantt(proyectoId); cargar(); onRefresh(); };

  const aplanar = (acts, result = []) => { for (const a of acts) { result.push(a); if (a.hijos?.length) aplanar(a.hijos, result); } return result; };
  const lista = aplanar(actividades.filter((a) => !a.padre_id));

  return (
    <div className="pl-page">
      <div className="pl-between">
        <h2 className="pl-h2">Plan de Actividades — Gantt</h2>
        <div className="pl-row">
          <button className={`pl-btn pl-btn-sm ${vistaGantt ? 'pl-btn-blue' : 'pl-btn-outline'}`} onClick={() => setVistaGantt((v) => !v)}>{vistaGantt ? '📊 Gantt ON' : '📊 Gantt OFF'}</button>
          <button className="pl-btn pl-btn-outline pl-btn-sm" onClick={handleRecalcular}>🔄 Recalcular fechas</button>
          <button className="pl-btn pl-btn-primary pl-btn-sm" onClick={() => { setForm(emptyForm(proyectoId)); setEditId(null); setShowForm(true); }}>+ Actividad</button>
        </div>
      </div>

      {showForm && (
        <div className="pl-card pl-card-pad">
          <h3 className="pl-h3">{editId ? 'Editar' : 'Nueva'} Actividad</h3>
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '.75rem' }}>
            <input className="pl-input" required value={form.titulo} onChange={(e) => setForm((f) => ({ ...f, titulo: e.target.value }))} placeholder="Título *" />
            <div className="pl-grid pl-grid-2">
              <div>
                <label className="pl-label">Nivel</label>
                <select className="pl-select" value={form.nivel} onChange={(e) => setForm((f) => ({ ...f, nivel: Number(e.target.value) }))}>
                  <option value={0}>0 — Título</option><option value={1}>1 — Actividad</option>
                  <option value={2}>2 — Subactividad</option><option value={3}>3 — Sub-subactividad</option>
                </select>
              </div>
              <div>
                <label className="pl-label">Prioridad</label>
                <select className="pl-select" value={form.prioridad} onChange={(e) => setForm((f) => ({ ...f, prioridad: e.target.value }))}>
                  {['Alta', 'Media', 'Baja'].map((p) => <option key={p}>{p}</option>)}
                </select>
              </div>
              <div>
                <label className="pl-label">Inicio planificado</label>
                <input className="pl-input" type="date" value={form.fecha_inicio_plan} onChange={(e) => setForm((f) => ({ ...f, fecha_inicio_plan: e.target.value }))} />
              </div>
              <div>
                <label className="pl-label">Duración (días lab.)</label>
                <input className="pl-input" type="number" min="0" value={form.duracion_dias} onChange={(e) => setForm((f) => ({ ...f, duracion_dias: e.target.value }))} />
              </div>
            </div>
            <label className="pl-row" style={{ gap: '.5rem', fontSize: '.85rem' }}>
              <input type="checkbox" checked={form.es_hito} onChange={(e) => setForm((f) => ({ ...f, es_hito: e.target.checked }))} />
              Es hito (duración 0, marca un evento clave)
            </label>

            <div>
              <p className="pl-label">Subtareas</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '.25rem', marginBottom: '.5rem', maxHeight: 96, overflowY: 'auto' }}>
                {form.subtareas.map((s, i) => (
                  <div key={i} className="pl-row" style={{ fontSize: '.78rem', justifyContent: 'space-between' }}>
                    <span>• {s.texto}</span>
                    <button type="button" className="pl-link pl-link-danger" onClick={() => setForm((f) => ({ ...f, subtareas: f.subtareas.filter((_, j) => j !== i) }))}>✕</button>
                  </div>
                ))}
              </div>
              <div className="pl-row" style={{ gap: '.5rem' }}>
                <input className="pl-input" value={nuevaSub} onChange={(e) => setNuevaSub(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addSub())}
                  placeholder="Subtarea (Enter para agregar)" style={{ flex: 1 }} />
                <button type="button" className="pl-btn pl-btn-outline" onClick={addSub}>+</button>
              </div>
            </div>

            <div className="pl-row" style={{ gap: '.5rem' }}>
              <button type="button" className="pl-btn pl-btn-outline" style={{ flex: 1 }} onClick={() => setShowForm(false)}>Cancelar</button>
              <button type="submit" className="pl-btn pl-btn-primary" style={{ flex: 1 }}>{editId ? 'Actualizar' : 'Crear'}</button>
            </div>
          </form>
        </div>
      )}

      {loading ? <p className="pl-empty">Cargando...</p>
        : lista.length === 0 ? (
          <div className="pl-empty"><div className="pl-empty-icon">📋</div><p>Sin actividades. Crea la primera para empezar el Gantt.</p></div>
        ) : (
          <div className="pl-card" style={{ overflow: 'hidden' }}>
            <div style={{ display: 'grid', gridTemplateColumns: vistaGantt ? 'minmax(280px,1fr) minmax(240px,1fr)' : '1fr' }}>
              <div style={{ overflowX: 'auto' }}>
                <table className="pl-table">
                  <thead><tr><th>Actividad</th><th>Inicio Plan</th><th>Días</th><th>Avance</th><th></th></tr></thead>
                  <tbody>
                    {lista.map((a) => (
                      <tr key={a.id}>
                        <td style={{ paddingLeft: 12 + (NIVEL_PAD[a.nivel] || 0) }}>
                          <div className="pl-row" style={{ gap: '.3rem' }}>
                            {a.es_hito && <span style={{ color: '#c084fc' }}>◆</span>}
                            <span style={{ fontWeight: a.nivel === 0 ? 700 : a.nivel === 1 ? 600 : 400 }}>{a.titulo}</span>
                          </div>
                          {a.subtareas?.length > 0 && (
                            <div style={{ marginTop: '.25rem', display: 'flex', flexDirection: 'column', gap: '.15rem' }}>
                              {a.subtareas.map((s, i) => (
                                <label key={i} className="pl-row" style={{ gap: '.3rem', cursor: 'pointer', fontSize: '.72rem' }}>
                                  <input type="checkbox" checked={s.hecho} onChange={() => toggleSubtarea(a, i)} />
                                  <span style={{ textDecoration: s.hecho ? 'line-through' : 'none', color: s.hecho ? 'var(--text-secondary)' : 'var(--text-primary)' }}>{s.texto}</span>
                                </label>
                              ))}
                            </div>
                          )}
                          <div className="pl-row" style={{ gap: '.4rem', marginTop: '.3rem' }}>
                            <span className="pl-badge" style={estadoActividadBadge(a.estado)}>{a.estado}</span>
                            <span style={{ fontSize: '.72rem', fontWeight: 600, color: prioridadColor(a.prioridad) }}>{a.prioridad}</span>
                          </div>
                        </td>
                        <td className="pl-muted" style={{ fontSize: '.72rem' }}>{a.fecha_inicio_plan || '—'}</td>
                        <td className="pl-muted" style={{ fontSize: '.72rem' }}>{a.duracion_dias}d</td>
                        <td>
                          <div style={{ width: 64 }}>
                            <div className="pl-progress" style={{ height: 6 }}><div className="pl-progress-real" style={{ width: `${a.avance}%`, opacity: 1 }} /></div>
                            <p className="pl-muted" style={{ fontSize: '.7rem', marginTop: '.2rem' }}>{a.avance}%</p>
                          </div>
                        </td>
                        <td>
                          <div className="pl-row" style={{ gap: '.4rem' }}>
                            <button className="pl-link" onClick={() => handleEdit(a)}>✏️</button>
                            <button className="pl-link pl-link-danger" onClick={() => handleDelete(a.id)}>🗑️</button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {vistaGantt && (
                <div style={{ borderLeft: '1px solid var(--border-color)', overflowX: 'auto' }}>
                  <div style={{ height: 33, background: 'var(--bg-color)', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', padding: '0 .5rem' }}>
                    <span className="pl-muted" style={{ fontSize: '.7rem' }}>{proyecto?.fecha_inicio} → {proyecto?.fecha_fin}</span>
                  </div>
                  {lista.map((a) => (
                    <div key={a.id} style={{ borderBottom: '1px solid var(--border-color)', padding: '.5rem', minHeight: 41, display: 'flex', alignItems: 'center' }}>
                      <div style={{ width: '100%' }}><GanttBar act={a} proyectoInicio={proyecto?.fecha_inicio} totalDias={totalDias} /></div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
    </div>
  );
}
