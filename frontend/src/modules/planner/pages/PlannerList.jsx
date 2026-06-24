import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePlannerStore } from '../store/plannerStore';
import { getProyectos, getKpis, deleteProyecto } from '../api/plannerApi';
import ProyectoModal from '../components/ProyectoModal';
import { estadoBadge } from '../utils/estilos';
import '../planner.css';

export default function PlannerList() {
  const navigate = useNavigate();
  const { proyectos, setProyectos, kpis, setKpis, filtroEstado, setFiltroEstado } = usePlannerStore();
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editando, setEditando] = useState(null);

  const cargar = async () => {
    setLoading(true);
    try {
      const [pRes, kRes] = await Promise.all([
        getProyectos(filtroEstado ? { estado: filtroEstado } : {}),
        getKpis(),
      ]);
      setProyectos(pRes.data);
      setKpis(kRes.data);
    } finally { setLoading(false); }
  };

  useEffect(() => { cargar(); /* eslint-disable-next-line */ }, [filtroEstado]);

  const handleDelete = async (id, nombre) => {
    if (!window.confirm(`¿Eliminar "${nombre}"? Se eliminarán todos sus datos.`)) return;
    await deleteProyecto(id); cargar();
  };

  const KPIS = kpis ? [
    { label: 'Proyectos', value: kpis.total_proyectos, color: 'var(--text-primary)' },
    { label: 'En Progreso', value: kpis.proyectos_activos, color: '#7ab7ff' },
    { label: 'Completados', value: kpis.proyectos_completados, color: 'var(--primary-color)' },
    { label: 'Paneles totales', value: kpis.total_paneles, color: '#f0b429' },
    { label: 'Personal activo', value: kpis.personal_activo, color: '#c084fc' },
  ] : [];

  return (
    <div className="pl-page animate-fade-in">
      <div className="pl-between">
        <div>
          <h1 className="pl-title">☀️ Planner Solar</h1>
          <p className="pl-subtitle">Gestión de proyectos fotovoltaicos — Energreen Perú</p>
        </div>
        <button className="pl-btn pl-btn-primary" onClick={() => { setEditando(null); setShowModal(true); }}>
          + Nuevo Proyecto
        </button>
      </div>

      {kpis && (
        <div className="pl-grid pl-grid-kpi">
          {KPIS.map((k) => (
            <div key={k.label} className="pl-kpi">
              <p className="pl-kpi-label">{k.label}</p>
              <p className="pl-kpi-value" style={{ color: k.color }}>{k.value}</p>
            </div>
          ))}
        </div>
      )}

      {kpis && (
        <div className="pl-card pl-card-pad">
          <div className="pl-between" style={{ fontSize: '.82rem', marginBottom: '.5rem' }}>
            <span style={{ fontWeight: 600 }}>Avance promedio global</span>
            <span className="pl-muted">
              Plan: <strong>{kpis.promedio_avance_planificado}%</strong> · Real:{' '}
              <strong style={{ color: 'var(--primary-color)' }}>{kpis.promedio_avance_real}%</strong>
            </span>
          </div>
          <div className="pl-progress" style={{ height: 12 }}>
            <div className="pl-progress-plan" style={{ width: `${kpis.promedio_avance_planificado}%` }} />
            <div className="pl-progress-real" style={{ width: `${kpis.promedio_avance_real}%` }} />
          </div>
          <div className="pl-legend">
            <span><span className="pl-dot" style={{ background: '#555' }} />Planificado</span>
            <span><span className="pl-dot" style={{ background: 'var(--primary-color)' }} />Real</span>
          </div>
        </div>
      )}

      <div className="pl-row">
        {[null, 'Pendiente', 'En Progreso', 'Completado', 'Cancelado'].map((e) => (
          <button key={e ?? 'todos'} onClick={() => setFiltroEstado(e)}
            className={`pl-pill ${filtroEstado === e ? 'pl-pill-active' : ''}`}>
            {e ?? 'Todos'}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="pl-empty">Cargando proyectos...</div>
      ) : proyectos.length === 0 ? (
        <div className="pl-empty">
          <div className="pl-empty-icon">☀️</div>
          <p style={{ fontWeight: 600 }}>Sin proyectos aún</p>
          <p style={{ fontSize: '.85rem' }}>Crea tu primer proyecto fotovoltaico</p>
        </div>
      ) : (
        <div className="pl-grid pl-grid-cards">
          {proyectos.map((p) => {
            const badge = estadoBadge(p.estado);
            return (
              <div key={p.id} className="pl-card pl-card-pad pl-card-hover"
                onClick={() => navigate(`/planner/${p.id}`)}
                style={{ display: 'flex', flexDirection: 'column', gap: '.75rem' }}>
                <div className="pl-between" style={{ alignItems: 'flex-start' }}>
                  <div style={{ minWidth: 0 }}>
                    <h3 style={{ fontWeight: 600, margin: 0, fontSize: '.95rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={p.nombre}>{p.nombre}</h3>
                    <p className="pl-muted" style={{ fontSize: '.75rem', margin: '.25rem 0 0' }}>🏢 {p.cliente || '—'} · 📍 {p.ubicacion || '—'}</p>
                    {p.fecha_inicio && <p className="pl-muted" style={{ fontSize: '.72rem', margin: '.15rem 0 0' }}>📆 {p.fecha_inicio} → {p.fecha_fin || '?'}</p>}
                  </div>
                  <span className="pl-badge" style={badge}>{p.estado}</span>
                </div>

                <div>
                  <div className="pl-between" style={{ fontSize: '.72rem', marginBottom: '.3rem' }}>
                    <span className="pl-muted">Avance</span>
                    <span className="pl-muted">Plan <strong>{p.avance_planificado ?? 0}%</strong> · Real <strong style={{ color: 'var(--primary-color)' }}>{p.avance_real ?? 0}%</strong></span>
                  </div>
                  <div className="pl-progress">
                    <div className="pl-progress-plan" style={{ width: `${p.avance_planificado ?? 0}%` }} />
                    <div className="pl-progress-real" style={{ width: `${p.avance_real ?? 0}%` }} />
                  </div>
                </div>

                <div className="pl-between">
                  <span className="pl-muted" style={{ fontSize: '.75rem' }}>☀️ {p.paneles} paneles</span>
                  <div className="pl-row" onClick={(e) => e.stopPropagation()}>
                    <button className="pl-link" onClick={() => { setEditando(p); setShowModal(true); }}>Editar</button>
                    <button className="pl-link pl-link-danger" onClick={() => handleDelete(p.id, p.nombre)}>Eliminar</button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {showModal && (
        <ProyectoModal proyecto={editando}
          onClose={() => { setShowModal(false); setEditando(null); }}
          onSaved={() => { setShowModal(false); setEditando(null); cargar(); }} />
      )}
    </div>
  );
}
