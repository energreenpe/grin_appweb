import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuoteStore } from '../store/quoteStore';
import { quoteApi } from '../api/quoteApi';
import CompanyHeader from '../components/CompanyHeader';
import QuoteHeader from '../components/QuoteHeader';
import ProductSearch from '../components/ProductSearch';
import QuoteTable from '../components/QuoteTable';
import QuoteSummary from '../components/QuoteSummary';
import QuoteConditions from '../components/QuoteConditions';
import ServiceFormModal from '../components/ServiceFormModal';
import { notify } from '../../../lib/notify';
import { useIsMobile } from '../../../lib/useIsMobile';

const ESTADO_COLORS = {
  borrador:  { bg: 'rgba(255,255,255,0.1)',  fg: 'var(--text-secondary)' },
  enviada:   { bg: 'rgba(59,130,246,0.2)',   fg: '#60a5fa' },
  aprobada:  { bg: 'rgba(74,222,128,0.2)',   fg: '#4ade80' },
  rechazada: { bg: 'rgba(248,113,113,0.2)',  fg: '#f87171' },
};

export default function QuoteEditor() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { cotizacion, loadCotizacion, loading, error, addItem, changeEstado, flushPending, logoUploads } = useQuoteStore();
  const [showServiceModal, setShowServiceModal] = useState(false);

  useEffect(() => {
    if (id) loadCotizacion(id);
  }, [id, loadCotizacion]);

  // Al salir del editor, persistir cualquier cambio pendiente del debounce.
  useEffect(() => {
    return () => { useQuoteStore.getState().flushPending(); };
  }, []);

  const estado = cotizacion?.estado;
  const readOnly = !!cotizacion && !['borrador', 'enviada'].includes(estado);
  const isMobile = useIsMobile();

  const handleDownloadPdf = async () => {
    if (!id || !cotizacion) return;
    if (logoUploads > 0) {
      notify('Espera a que termine de cargar el logo antes de generar el PDF.');
      return;
    }
    try {
      // Guardar lo último que se tecleó (debounce) antes de generar el PDF.
      await flushPending();
      const base = cotizacion.correlativo || `COTIZACION-${cotizacion.id}`;
      const defaultName = `${base}_${(cotizacion.cliente_nombre || 'cliente').replace(/ /g, '_')}.pdf`;
      const fileName = prompt("Confirma o edita el nombre del archivo PDF:", defaultName);
      if (!fileName) return; // User cancelled

      await quoteApi.downloadPdf(id, fileName);
      // Generar el PDF de un borrador lo pasa a "Enviada" y le asigna correlativo: recargar.
      await loadCotizacion(id);
    } catch (err) {
      console.error("Error downloading PDF", err);
      notify('No se pudo generar el PDF. Revisa tu conexión.');
    }
  };

  const handleEstado = async (nuevo) => {
    const verbo = { enviada: 'marcar como Enviada', aprobada: 'Aprobar', rechazada: 'Rechazar' };
    if (!window.confirm(`¿Seguro que deseas ${verbo[nuevo] || 'cambiar el estado de'} esta cotización?`)) return;
    const res = await changeEstado(cotizacion.id, nuevo);
    if (!res.ok) notify(res.error);
  };

  const handleDuplicate = async () => {
    try {
      const nueva = await quoteApi.duplicar(cotizacion.id);
      navigate(`/quote/${nueva.id}`);
    } catch (err) {
      console.error(err);
      notify('No se pudo duplicar la cotización. Revisa tu conexión.');
    }
  };

  const handleAddService = (serviceProduct, qty, particion, subparticion) => {
    addItem(cotizacion.id, serviceProduct, qty, particion, subparticion);
    setShowServiceModal(false);
  };

  if (loading && !cotizacion) return <div style={{ padding: '2rem' }}>Cargando cotización...</div>;
  if (error) return <div style={{ padding: '2rem', color: 'red' }}>Error: {error}</div>;
  if (!cotizacion) return null;

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header y Acciones */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <button
            onClick={() => navigate('/quote')}
            className="btn"
            style={{ padding: '0', background: 'none', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}
          >
            ← Volver a lista
          </button>
          <h1 style={{ fontSize: '1.8rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
            {cotizacion.correlativo || 'Borrador (sin número)'}
            <span style={{
              fontSize: '0.9rem', padding: '4px 12px', borderRadius: '20px',
              textTransform: 'capitalize',
              background: ESTADO_COLORS[estado]?.bg || 'rgba(255,255,255,0.1)',
              color: ESTADO_COLORS[estado]?.fg || 'var(--text-secondary)',
            }}>
              {estado}
            </span>
          </h1>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>Guardado automático</span>

          {estado === 'borrador' && (
            <button onClick={() => handleEstado('enviada')} className="btn btn-secondary">Marcar Enviada</button>
          )}
          {(estado === 'borrador' || estado === 'enviada') && (
            <button onClick={() => handleEstado('aprobada')} className="btn btn-secondary"
              style={{ borderColor: '#4ade80', color: '#4ade80' }}>✓ Aprobar</button>
          )}
          {(estado === 'enviada' || estado === 'aprobada') && (
            <button onClick={() => handleEstado('rechazada')} className="btn btn-danger">✗ Rechazar</button>
          )}

          <button onClick={handleDuplicate} className="btn btn-secondary">⧉ Duplicar</button>
          <button onClick={handleDownloadPdf} disabled={logoUploads > 0}
            title={logoUploads > 0 ? 'Espera a que termine de cargar el logo' : 'Generar PDF'}
            className="btn btn-primary"
            style={{ display: 'flex', gap: '8px', alignItems: 'center', opacity: logoUploads > 0 ? 0.6 : 1 }}>
            <span>📄</span> {logoUploads > 0 ? 'Cargando logo…' : 'Generar PDF'}
          </button>
        </div>
      </div>

      {readOnly && (
        <div style={{
          padding: '0.75rem 1rem', borderRadius: 'var(--radius)',
          background: 'rgba(255, 196, 0, 0.12)', border: '1px solid rgba(255, 196, 0, 0.4)',
          color: '#ffca28', fontSize: '0.9rem',
        }}>
          🔒 Esta cotización está <strong>{estado}</strong> y es de <strong>solo lectura</strong>.
          Usa <strong>Duplicar</strong> para crear una nueva versión editable.
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        
        {/* Cabecera Superior: en escritorio Empresa/Cliente (izq.) + Resumen (der., 350px);
            en móvil una sola columna -> Empresa, Cliente y luego Resumen apilados. */}
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 350px', gap: '1.5rem', alignItems: 'stretch' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {/* Datos de Empresa */}
            <div className="glass-panel" style={{ padding: '1.5rem' }}>
              <CompanyHeader readOnly={readOnly} />
            </div>

            {/* Datos del Cliente y Configuración */}
            <div className="glass-panel" style={{ padding: '1.5rem' }}>
              <QuoteHeader readOnly={readOnly} />
            </div>
          </div>

          {/* Panel lateral derecho: Totales y Resumen */}
          <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <QuoteSummary />
          </div>
        </div>

        {/* Buscador de Productos (Ancho completo) — oculto en solo lectura */}
        {!readOnly && (
          <div className="glass-panel" style={{ padding: '1.5rem', position: 'relative', zIndex: 50 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
              <h3 style={{ margin: 0 }}>Agregar Ítems</h3>
              <button onClick={() => setShowServiceModal(true)} className="btn btn-primary" style={{ padding: '4px 12px', fontSize: '0.85rem' }}>
                + Agregar Servicio
              </button>
            </div>
            <ProductSearch cotizacionId={cotizacion.id} />
          </div>
        )}

        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <h3 style={{ marginBottom: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
            Detalle de Cotización
          </h3>
          <QuoteTable cotizacionId={cotizacion.id} readOnly={readOnly} />
        </div>

        {/* Condiciones de Cotización */}
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <QuoteConditions cotizacionId={cotizacion.id} readOnly={readOnly} />
        </div>
      </div>

      {showServiceModal && (
        <ServiceFormModal 
          cotizacionId={cotizacion.id} 
          onConfirm={handleAddService} 
          onCancel={() => setShowServiceModal(false)} 
        />
      )}
    </div>
  );
}
