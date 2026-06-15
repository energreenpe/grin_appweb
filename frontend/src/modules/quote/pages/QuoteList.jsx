import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { quoteApi } from '../api/quoteApi';

const ESTADO_COLORS = {
  borrador:  { bg: 'rgba(255,255,255,0.1)',  fg: 'var(--text-secondary)' },
  enviada:   { bg: 'rgba(59,130,246,0.2)',   fg: '#60a5fa' },
  aprobada:  { bg: 'rgba(74,222,128,0.2)',   fg: '#4ade80' },
  rechazada: { bg: 'rgba(248,113,113,0.2)',  fg: '#f87171' },
};

const ESTADO_FILTROS = ['todos', 'borrador', 'enviada', 'aprobada', 'rechazada'];

export default function QuoteList() {
  const [quotes, setQuotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [estadoFilter, setEstadoFilter] = useState('todos');
  const navigate = useNavigate();

  useEffect(() => {
    loadQuotes();
  }, []);

  const loadQuotes = async () => {
    try {
      const data = await quoteApi.getCotizaciones();
      setQuotes(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      // Default empty quote
      const newQuote = await quoteApi.createCotizacion({
        cliente_nombre: '',
        moneda: 'Soles (PEN)',
      });
      navigate(`/quote/${newQuote.id}`);
    } catch (err) {
      console.error(err);
    }
  };

  const handleDuplicate = async (e, id) => {
    e.stopPropagation();
    try {
      const nueva = await quoteApi.duplicar(id);
      navigate(`/quote/${nueva.id}`);
    } catch (err) {
      console.error(err);
      alert('No se pudo duplicar la cotización');
    }
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (!window.confirm('¿Eliminar este borrador? Esta acción no se puede deshacer.')) return;
    try {
      await quoteApi.deleteCotizacion(id);
      loadQuotes();
    } catch (err) {
      alert(err?.response?.data?.detail || 'No se pudo eliminar la cotización');
    }
  };

  const term = search.trim().toLowerCase();
  const filtered = quotes.filter(q => {
    if (estadoFilter !== 'todos' && q.estado !== estadoFilter) return false;
    if (!term) return true;
    const fecha = new Date(q.created_at).toLocaleDateString();
    return [q.correlativo, q.cliente_nombre, fecha, q.moneda]
      .map(x => (x || '').toString().toLowerCase())
      .join(' ')
      .includes(term);
  });

  const counts = quotes.reduce((acc, q) => {
    acc[q.estado] = (acc[q.estado] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="animate-fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.8rem' }}>Cotizaciones</h1>
        <button onClick={handleCreate} className="btn btn-primary">
          + Nueva Cotización
        </button>
      </div>

      {/* Buscador + filtros por estado */}
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <div style={{ position: 'relative', flex: '1 1 280px', minWidth: '240px' }}>
          <span style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }}>🔍</span>
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Buscar por N° cotización, cliente o fecha..."
            className="input-field"
            style={{ paddingLeft: '2.25rem', width: '100%' }}
          />
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {ESTADO_FILTROS.map(est => {
            const active = estadoFilter === est;
            const total = est === 'todos' ? quotes.length : (counts[est] || 0);
            return (
              <button
                key={est}
                onClick={() => setEstadoFilter(est)}
                className="btn btn-secondary"
                style={{
                  padding: '0.35rem 0.8rem', fontSize: '0.85rem', textTransform: 'capitalize',
                  background: active ? 'var(--primary-color)' : undefined,
                  color: active ? '#fff' : undefined,
                  borderColor: active ? 'var(--primary-color)' : undefined,
                }}
              >
                {est} ({total})
              </button>
            );
          })}
        </div>
      </div>

      <div className="glass-panel table-container">
        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center' }}>Cargando...</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Correlativo</th>
                <th>Cliente</th>
                <th>Fecha</th>
                <th>Moneda</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                    {quotes.length === 0
                      ? 'No hay cotizaciones registradas'
                      : 'No se encontraron cotizaciones con esos criterios'}
                  </td>
                </tr>
              ) : (
                filtered.map(q => (
                  <tr key={q.id}>
                    <td style={{ fontWeight: '600' }}>
                      {q.correlativo || <span style={{ color: 'var(--text-secondary)', fontWeight: 'normal', fontStyle: 'italic' }}>— borrador</span>}
                    </td>
                    <td>{q.cliente_nombre || <span style={{ color: 'var(--text-secondary)' }}>(sin cliente)</span>}</td>
                    <td>{new Date(q.created_at).toLocaleDateString()}</td>
                    <td>{q.moneda}</td>
                    <td>
                      <span style={{
                        padding: '4px 10px',
                        borderRadius: '12px',
                        fontSize: '0.8rem',
                        textTransform: 'capitalize',
                        backgroundColor: (ESTADO_COLORS[q.estado] || ESTADO_COLORS.borrador).bg,
                        color: (ESTADO_COLORS[q.estado] || ESTADO_COLORS.borrador).fg,
                      }}>
                        {q.estado}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button
                          onClick={() => navigate(`/quote/${q.id}`)}
                          className="btn btn-secondary"
                          style={{ padding: '0.25rem 0.75rem', fontSize: '0.9rem' }}
                        >
                          {q.estado === 'borrador' || q.estado === 'enviada' ? 'Editar' : 'Ver'}
                        </button>
                        <button
                          onClick={(e) => handleDuplicate(e, q.id)}
                          className="btn btn-secondary"
                          style={{ padding: '0.25rem 0.75rem', fontSize: '0.9rem' }}
                          title="Duplicar como nuevo borrador"
                        >
                          ⧉
                        </button>
                        {q.estado === 'borrador' && (
                          <button
                            onClick={(e) => handleDelete(e, q.id)}
                            className="btn btn-danger"
                            style={{ padding: '0.25rem 0.75rem', fontSize: '0.9rem' }}
                            title="Eliminar borrador"
                          >
                            🗑
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
