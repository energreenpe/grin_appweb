import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { usePlannerStore } from '../store/plannerStore';
import { getProyecto, snapshotCurvaS } from '../api/plannerApi';
import { estadoBadge } from '../utils/estilos';
import ReporteModal from '../components/ReporteModal';
import GanttTab from '../components/GanttTab';
import CuadrillaTab from '../components/CuadrillaTab';
import AsistenciaTab from '../components/AsistenciaTab';
import EvidenciaTab from '../components/EvidenciaTab';
import CurvaSTab from '../components/CurvaSTab';
import '../planner.css';

const TABS = [
  { id: 'gantt', label: '📊 Gantt' },
  { id: 'cuadrilla', label: '👷 Cuadrillas' },
  { id: 'asistencia', label: '📅 Asistencia' },
  { id: 'evidencia', label: '📷 Evidencia' },
  { id: 'curva_s', label: '📈 Curva S' },
];

export default function PlannerDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { proyectoActivo, setProyectoActivo } = usePlannerStore();
  const [tab, setTab] = useState('gantt');
  const [loading, setLoading] = useState(true);
  const [showReporte, setShowReporte] = useState(false);

  const cargar = async () => {
    setLoading(true);
    try {
      const res = await getProyecto(id);
      setProyectoActivo(res.data);
    } catch { navigate('/planner'); }
    finally { setLoading(false); }
  };

  useEffect(() => { cargar(); /* eslint-disable-next-line */ }, [id]);

  const registrarSnapshot = async () => {
    await snapshotCurvaS(id);
    window.alert('Snapshot de Curva S registrado ✅');
  };

  if (loading) return <div className="pl-empty">Cargando proyecto...</div>;
  if (!proyectoActivo) return null;
  const p = proyectoActivo;

  return (
    <div className="pl-page animate-fade-in">
      {/* Encabezado */}
      <div className="pl-card pl-card-pad">
        <div className="pl-row" style={{ fontSize: '.8rem', color: 'var(--text-secondary)', marginBottom: '.5rem' }}>
          <button className="pl-link" style={{ color: 'var(--text-secondary)' }} onClick={() => navigate('/planner')}>← Proyectos</button>
          <span>/</span>
          <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{p.nombre}</span>
        </div>

        <div className="pl-between" style={{ alignItems: 'flex-start' }}>
          <div>
            <h1 className="pl-title" style={{ fontSize: '1.3rem' }}>{p.nombre}</h1>
            <div className="pl-row" style={{ fontSize: '.75rem', color: 'var(--text-secondary)', marginTop: '.35rem', gap: '.85rem' }}>
              <span>🏢 {p.cliente || '—'}</span>
              <span>📍 {p.ubicacion || '—'}</span>
              {p.region && <span>🗺️ {p.region}</span>}
              <span>☀️ {p.paneles} paneles</span>
              {p.fecha_inicio && <span>📆 {p.fecha_inicio} → {p.fecha_fin || '?'}</span>}
            </div>
          </div>

          <div className="pl-row" style={{ gap: '1rem' }}>
            <div style={{ textAlign: 'center' }}>
              <p className="pl-muted" style={{ fontSize: '.7rem' }}>Planificado</p>
              <p style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-secondary)' }}>{p.avance_planificado ?? 0}%</p>
            </div>
            <div style={{ textAlign: 'center' }}>
              <p className="pl-muted" style={{ fontSize: '.7rem' }}>Real</p>
              <p style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--primary-color)' }}>{p.avance_real ?? 0}%</p>
            </div>
            <span className="pl-badge" style={estadoBadge(p.estado)}>{p.estado}</span>
            <button className="pl-btn pl-btn-outline pl-btn-sm" onClick={registrarSnapshot} title="Registrar snapshot Curva S">📸 Snapshot</button>
            <button className="pl-btn pl-btn-primary pl-btn-sm" onClick={() => setShowReporte(true)}>📄 Exportar PDF</button>
          </div>
        </div>

        <div className="pl-progress" style={{ marginTop: '.75rem' }}>
          <div className="pl-progress-plan" style={{ width: `${p.avance_planificado ?? 0}%` }} />
          <div className="pl-progress-real" style={{ width: `${p.avance_real ?? 0}%` }} />
        </div>
        <div className="pl-legend">
          <span><span className="pl-dot" style={{ background: '#555' }} />Planificado</span>
          <span><span className="pl-dot" style={{ background: 'var(--primary-color)' }} />Real</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="pl-tabbar">
        {TABS.map((t) => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`pl-tab ${tab === t.id ? 'pl-tab-active' : ''}`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Contenido */}
      <div>
        {tab === 'gantt' && <GanttTab proyectoId={Number(id)} proyecto={p} onRefresh={cargar} />}
        {tab === 'cuadrilla' && <CuadrillaTab proyectoId={Number(id)} />}
        {tab === 'asistencia' && <AsistenciaTab proyectoId={Number(id)} />}
        {tab === 'evidencia' && <EvidenciaTab proyectoId={Number(id)} proyecto={p} />}
        {tab === 'curva_s' && <CurvaSTab proyectoId={Number(id)} />}
      </div>

      {showReporte && (
        <ReporteModal proyectoId={Number(id)} proyectoNombre={p.nombre} onClose={() => setShowReporte(false)} />
      )}
    </div>
  );
}
