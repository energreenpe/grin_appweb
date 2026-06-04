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

export default function QuoteEditor() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { cotizacion, loadCotizacion, loading, error, addItem } = useQuoteStore();
  const [showServiceModal, setShowServiceModal] = useState(false);

  useEffect(() => {
    if (id) loadCotizacion(id);
  }, [id, loadCotizacion]);

  const handleDownloadPdf = async () => {
    if (!id || !cotizacion) return;
    try {
      const defaultName = `COT2026-${cotizacion.correlativo}-${cotizacion.version || '1.0'}_${cotizacion.cliente_nombre.replace(/ /g, '_')}.pdf`;
      const fileName = prompt("Confirma o edita el nombre del archivo PDF:", defaultName);
      if (!fileName) return; // User cancelled

      await quoteApi.downloadPdf(id, fileName);
    } catch (err) {
      console.error("Error downloading PDF", err);
      alert("Error al generar el PDF");
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <button
            onClick={() => navigate('/quote')}
            className="btn"
            style={{ padding: '0', background: 'none', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}
          >
            ← Volver a lista
          </button>
          <h1 style={{ fontSize: '1.8rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
            {cotizacion.correlativo}
            <span style={{ fontSize: '1rem', padding: '4px 10px', background: 'rgba(255,255,255,0.1)', borderRadius: '20px' }}>
              {cotizacion.estado}
            </span>
          </h1>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn btn-secondary">Guardar Borrador</button>
          <button onClick={handleDownloadPdf} className="btn btn-primary" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <span>📄</span> Generar PDF
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        
        {/* Cabecera Superior: Empresa/Cliente (Izquierda) y Resumen (Derecha) */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 350px', gap: '1.5rem', alignItems: 'stretch' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {/* Datos de Empresa */}
            <div className="glass-panel" style={{ padding: '1.5rem' }}>
              <CompanyHeader />
            </div>

            {/* Datos del Cliente y Configuración */}
            <div className="glass-panel" style={{ padding: '1.5rem' }}>
              <QuoteHeader />
            </div>
          </div>

          {/* Panel lateral derecho: Totales y Resumen */}
          <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <QuoteSummary />
          </div>
        </div>

        {/* Buscador de Productos (Ancho completo) */}
        <div className="glass-panel" style={{ padding: '1.5rem', position: 'relative', zIndex: 50 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
            <h3 style={{ margin: 0 }}>Agregar Ítems</h3>
            <button onClick={() => setShowServiceModal(true)} className="btn btn-primary" style={{ padding: '4px 12px', fontSize: '0.85rem' }}>
              + Agregar Servicio
            </button>
          </div>
          <ProductSearch cotizacionId={cotizacion.id} />
        </div>

        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <h3 style={{ marginBottom: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
            Detalle de Cotización
          </h3>
          <QuoteTable cotizacionId={cotizacion.id} />
        </div>

        {/* Condiciones de Cotización */}
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <QuoteConditions cotizacionId={cotizacion.id} />
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
