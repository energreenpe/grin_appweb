import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { inspectorApi } from '../api/inspectorApi';
import VisitaCard from '../components/VisitaCard';
import SearchableSelect from '../../../components/SearchableSelect';
import { useWizardStore } from '../store/wizardStore';

export default function InspectorList() {
  const navigate = useNavigate();
  const { reset } = useWizardStore();
  const [visitas, setVisitas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filtros
  const [filtroTipo, setFiltroTipo] = useState('');
  const [filtroSistema, setFiltroSistema] = useState('');
  const [filtroEstado, setFiltroEstado] = useState('');

  const fetchVisitas = async () => {
    try {
      setLoading(true);
      const data = await inspectorApi.getVisitas({
        tipo_cliente: filtroTipo || undefined,
        tipo_sistema: filtroSistema || undefined,
        estado: filtroEstado || undefined
      });
      setVisitas(data);
      setError(null);
    } catch (err) {
      console.error("Error fetching visitas", err);
      setError("No se pudieron cargar las visitas. Intenta nuevamente.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVisitas();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtroTipo, filtroSistema, filtroEstado]);

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', height: '100%' }}>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ margin: '0 0 0.5rem 0', fontSize: '1.8rem' }}>Inspecciones Técnicas</h1>
          <p style={{ margin: 0, color: 'var(--text-secondary)' }}>
            Registro y reportes fotográficos de visitas a campo
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => { reset(); navigate('/inspector/new'); }}
          style={{ padding: '0.75rem 1.5rem', fontSize: '1rem', fontWeight: 'bold' }}
        >
          + Nueva Inspección
        </button>
      </div>

      <div className="glass-panel" style={{ padding: '1rem', display: 'flex', gap: '1rem', flexWrap: 'wrap', position: 'relative', zIndex: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <label style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Tipo Cliente:</label>
          <SearchableSelect
            style={{ minWidth: '150px' }}
            value={filtroTipo}
            onChange={setFiltroTipo}
            placeholder="Todos"
            options={[
              { value: '', label: 'Todos' },
              { value: 'Persona', label: 'Persona' },
              { value: 'Empresa', label: 'Empresa' },
            ]}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <label style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Sistema:</label>
          <SearchableSelect
            style={{ minWidth: '180px' }}
            value={filtroSistema}
            onChange={setFiltroSistema}
            placeholder="Todos"
            options={[
              { value: '', label: 'Todos' },
              { value: 'SFV Autoconsumo', label: 'SFV Autoconsumo' },
              { value: 'SFV Híbrido', label: 'SFV Híbrido' },
              { value: 'SFV Aislado', label: 'SFV Aislado' },
              { value: 'Terma Solar', label: 'Terma Solar' },
              { value: 'BESS', label: 'BESS' },
            ]}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <label style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Estado:</label>
          <SearchableSelect
            style={{ minWidth: '150px' }}
            value={filtroEstado}
            onChange={setFiltroEstado}
            placeholder="Todos"
            options={[
              { value: '', label: 'Todos' },
              { value: 'completada', label: 'Completadas' },
              { value: 'borrador', label: 'Borradores' },
            ]}
          />
        </div>
        
        <button className="btn btn-secondary" onClick={fetchVisitas} style={{ marginLeft: 'auto' }}>
          ↻ Actualizar
        </button>
      </div>

      {loading ? (
        <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
          Cargando visitas...
        </div>
      ) : error ? (
        <div style={{ padding: '2rem', textAlign: 'center', color: 'red', background: 'rgba(255,0,0,0.1)', borderRadius: '8px' }}>
          {error}
        </div>
      ) : visitas.length === 0 ? (
        <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--text-secondary)', border: '2px dashed var(--border-color)', borderRadius: '12px' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📋</div>
          <h3>No hay inspecciones registradas</h3>
          <p>Haz clic en "Nueva Inspección" para registrar la primera visita.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.5rem' }}>
          {visitas.map(visita => (
            <VisitaCard key={visita.id} visita={visita} />
          ))}
        </div>
      )}

    </div>
  );
}
