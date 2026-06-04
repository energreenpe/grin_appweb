import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { quoteApi } from '../api/quoteApi';

export default function QuoteList() {
  const [quotes, setQuotes] = useState([]);
  const [loading, setLoading] = useState(true);
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
        version: ''
      });
      navigate(`/quote/${newQuote.id}`);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="animate-fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.8rem' }}>Cotizaciones</h1>
        <button onClick={handleCreate} className="btn btn-primary">
          + Nueva Cotización
        </button>
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
              {quotes.length === 0 ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: '2rem' }}>
                    No hay cotizaciones registradas
                  </td>
                </tr>
              ) : (
                quotes.map(q => (
                  <tr key={q.id}>
                    <td style={{ fontWeight: '600' }}>{q.correlativo}</td>
                    <td>{q.cliente_nombre}</td>
                    <td>{new Date(q.created_at).toLocaleDateString()}</td>
                    <td>{q.moneda}</td>
                    <td>
                      <span style={{ 
                        padding: '4px 8px', 
                        borderRadius: '12px', 
                        fontSize: '0.8rem',
                        backgroundColor: q.estado === 'borrador' ? 'rgba(255,255,255,0.1)' : 'rgba(98, 185, 137, 0.2)',
                        color: q.estado === 'borrador' ? 'var(--text-secondary)' : 'var(--primary-color)'
                      }}>
                        {q.estado}
                      </span>
                    </td>
                    <td>
                      <button 
                        onClick={() => navigate(`/quote/${q.id}`)}
                        className="btn btn-secondary"
                        style={{ padding: '0.25rem 0.75rem', fontSize: '0.9rem' }}
                      >
                        Editar
                      </button>
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
