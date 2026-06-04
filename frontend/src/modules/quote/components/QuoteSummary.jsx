import { useQuoteStore } from '../store/quoteStore';

export default function QuoteSummary() {
  const { totales, cotizacion } = useQuoteStore();

  if (!cotizacion) return null;

  const monedaDisplay = cotizacion.moneda.includes('USD') ? '$' : 'S/';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <h3 style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
        Resumen
      </h3>

      {/* Subtotales por Partición */}
      {Object.keys(totales.por_particion || {}).length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Por Partición</div>
          {Object.entries(totales.por_particion).map(([particion, valor]) => (
            <div key={particion} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
              <span style={{ color: 'var(--text-secondary)' }}>{particion}</span>
              <span>{monedaDisplay} {Number(valor).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
            </div>
          ))}
          <div style={{ height: '1px', backgroundColor: 'var(--border-color)', margin: '0.5rem 0' }} />
        </div>
      )}

      {/* Totales Generales */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: 'var(--text-secondary)' }}>Valor Venta (Subtotal)</span>
          <span>{monedaDisplay} {Number(totales.subtotal || 0).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
        </div>
        
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: 'var(--text-secondary)' }}>I.G.V. (18%)</span>
          <span>{monedaDisplay} {Number(totales.igv || 0).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
        </div>
        
        <div style={{ 
          display: 'flex', justifyContent: 'space-between', 
          marginTop: '0.5rem', paddingTop: '1rem', 
          borderTop: '1px solid var(--border-color)',
          fontSize: '1.2rem', fontWeight: 'bold', color: 'var(--primary-color)'
        }}>
          <span>Total</span>
          <span>{monedaDisplay} {Number(totales.total || 0).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
        </div>
      </div>

      <div style={{ 
        marginTop: '1rem', padding: '1rem', 
        backgroundColor: 'rgba(255,255,255,0.02)', 
        borderRadius: 'var(--radius)',
        fontSize: '0.8rem', color: 'var(--text-secondary)'
      }}>
        <div style={{ marginBottom: '4px' }}><strong>T.C.:</strong> {cotizacion.tipo_cambio}</div>
        <div style={{ marginBottom: '4px' }}><strong>Margen:</strong> {((cotizacion.utilidad - 1) * 100).toFixed(0)}%</div>
      </div>
    </div>
  );
}
