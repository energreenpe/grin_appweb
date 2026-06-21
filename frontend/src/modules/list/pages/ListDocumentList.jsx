import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { listApi } from '../api/listApi';
import { useListStore } from '../store/listStore';
import { notify } from '../../../lib/notify';

export default function ListDocumentList() {
  const navigate = useNavigate();
  const reset = useListStore((s) => s.reset);
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDocs = async () => {
    try {
      setLoading(true);
      setDocs(await listApi.listDocumentos());
      setError(null);
    } catch (err) {
      setError('No se pudieron cargar los documentos. Intenta nuevamente.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDocs(); }, []);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm('¿Eliminar este documento? Esta acción no se puede deshacer.')) return;
    try {
      await listApi.deleteDocumento(id);
      setDocs((d) => d.filter((x) => x.id !== id));
      notify('Documento eliminado.', 'success');
    } catch (err) {
      notify('No se pudo eliminar el documento.', 'error');
    }
  };

  const fmtDate = (s) =>
    s ? new Date(s).toLocaleString('es-PE', { dateStyle: 'medium', timeStyle: 'short' }) : '';

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ margin: '0 0 0.5rem 0', fontSize: '1.8rem' }}>Editor de Documentos</h1>
          <p style={{ margin: 0, color: 'var(--text-secondary)' }}>
            Sube, edita y exporta documentos PDF (LIST)
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => { reset(); navigate('/list/new'); }}
          style={{ padding: '0.75rem 1.5rem', fontSize: '1rem', fontWeight: 'bold' }}
        >
          + Nuevo Documento
        </button>
      </div>

      {loading ? (
        <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>Cargando documentos...</div>
      ) : error ? (
        <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--danger-color)', background: 'rgba(239,68,68,0.1)', borderRadius: '8px' }}>{error}</div>
      ) : docs.length === 0 ? (
        <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--text-secondary)', border: '2px dashed var(--border-color)', borderRadius: '12px' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📝</div>
          <h3>No hay documentos aún</h3>
          <p>Haz clic en "Nuevo Documento" para subir tu primer archivo.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1.5rem' }}>
          {docs.map((d) => (
            <div
              key={d.id}
              className="glass-panel"
              onClick={() => navigate(`/list/${d.id}`)}
              style={{ padding: '1.25rem', cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: '0.75rem', transition: 'transform 0.15s, box-shadow 0.15s' }}
              onMouseOver={(e) => { e.currentTarget.style.transform = 'translateY(-3px)'; e.currentTarget.style.boxShadow = '0 10px 20px rgba(0,0,0,0.3)'; }}
              onMouseOut={(e) => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = 'none'; }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', minWidth: 0 }}>
                <span style={{ fontSize: '1.6rem' }}>📄</span>
                <span style={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={d.nombre}>{d.nombre}</span>
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                Editado: {fmtDate(d.updated_at)}
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', marginTop: 'auto' }}>
                <button className="btn btn-primary" style={{ flex: 1 }} onClick={(e) => { e.stopPropagation(); navigate(`/list/${d.id}`); }}>Abrir</button>
                <button className="btn btn-danger" onClick={(e) => handleDelete(d.id, e)}>Eliminar</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
