import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { mathApi } from '../api/mathApi';
import CalculoCard from '../components/CalculoCard';
import SearchableSelect from '../components/SearchableSelect';
import { useCalculoStore } from '../store/calculoStore';

export default function MathList() {
  const navigate = useNavigate();
  const { reset } = useCalculoStore();
  const [calculos, setCalculos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [filtroSistema, setFiltroSistema] = useState('');
  const [filtroEstado, setFiltroEstado] = useState('');

  const fetchCalculos = async () => {
    try {
      setLoading(true);
      const data = await mathApi.getCalculos({
        tipo_sistema: filtroSistema || undefined,
        estado: filtroEstado || undefined,
      });
      setCalculos(data);
      setError(null);
    } catch (err) {
      console.error('Error fetching calculos', err);
      setError('No se pudieron cargar los cálculos. Intenta nuevamente.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCalculos();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtroSistema, filtroEstado]);

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ margin: '0 0 0.5rem 0', fontSize: '1.8rem' }}>Cálculos Solares</h1>
          <p style={{ margin: 0, color: 'var(--text-secondary)' }}>
            Dimensionamiento de sistemas fotovoltaicos
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => { reset(); navigate('/math/new'); }}
          style={{ padding: '0.75rem 1.5rem', fontSize: '1rem', fontWeight: 'bold' }}>
          + Nuevo Cálculo
        </button>
      </div>

      <div className="glass-panel" style={{ padding: '1rem', display: 'flex', gap: '1rem', flexWrap: 'wrap', position: 'relative', zIndex: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <label style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Sistema:</label>
          <SearchableSelect
            style={{ minWidth: '190px' }}
            value={filtroSistema}
            onChange={setFiltroSistema}
            placeholder="Todos"
            options={[
              { value: '', label: 'Todos' },
              { value: 'SFV Aislado', label: 'SFV Aislado' },
              { value: 'SFV Autoconsumo', label: 'SFV Autoconsumo' },
              { value: 'SFV Híbrido', label: 'SFV Híbrido' },
              { value: 'Bombeo Solar', label: 'Bombeo Solar' },
            ]}
          />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <label style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Estado:</label>
          <SearchableSelect
            style={{ minWidth: '160px' }}
            value={filtroEstado}
            onChange={setFiltroEstado}
            placeholder="Todos"
            options={[
              { value: '', label: 'Todos' },
              { value: 'completado', label: 'Completados' },
              { value: 'borrador', label: 'Borradores' },
            ]}
          />
        </div>
        <button className="btn btn-secondary" onClick={fetchCalculos} style={{ marginLeft: 'auto' }}>↻ Actualizar</button>
      </div>

      {loading ? (
        <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>Cargando cálculos...</div>
      ) : error ? (
        <div style={{ padding: '2rem', textAlign: 'center', color: 'red', background: 'rgba(255,0,0,0.1)', borderRadius: '8px' }}>{error}</div>
      ) : calculos.length === 0 ? (
        <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--text-secondary)', border: '2px dashed var(--border-color)', borderRadius: '12px' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📐</div>
          <h3>No hay cálculos registrados</h3>
          <p>Haz clic en "Nuevo Cálculo" para dimensionar el primer sistema.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.5rem' }}>
          {calculos.map((calculo) => (
            <CalculoCard key={calculo.id} calculo={calculo} onChange={fetchCalculos} />
          ))}
        </div>
      )}
    </div>
  );
}
