import { useState } from 'react';
import { createPortal } from 'react-dom';
import { quoteApi } from '../api/quoteApi';
import { notify } from '../../../lib/notify';

export default function ProductImportModal({ onImported, onCancel }) {
  const [file, setFile] = useState(null);
  const [importing, setImporting] = useState(false);
  const [rowErrors, setRowErrors] = useState(null);
  const [structError, setStructError] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0] || null);
    setRowErrors(null);
    setStructError(null);
  };

  const handleDownloadTemplate = async () => {
    try {
      await quoteApi.downloadProductsTemplate();
    } catch (err) {
      console.error(err);
      notify('No se pudo descargar la plantilla.');
    }
  };

  const handleImport = async () => {
    if (!file) return;
    setImporting(true);
    setRowErrors(null);
    setStructError(null);
    try {
      const result = await quoteApi.importProducts(file);
      const omitidosMsg = result.omitidos_duplicados > 0
        ? ` (${result.omitidos_duplicados} ya existían y se omitieron)`
        : '';
      notify(`Se importaron ${result.creados} productos.${omitidosMsg}`, 'success');
      onImported();
    } catch (err) {
      console.error(err);
      const detail = err?.response?.data?.detail;
      if (detail && typeof detail === 'object' && Array.isArray(detail.errores)) {
        setRowErrors(detail.errores);
      } else {
        setStructError(typeof detail === 'string' ? detail : 'No se pudo importar el archivo.');
      }
    } finally {
      setImporting(false);
    }
  };

  return createPortal(
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.7)', zIndex: 9999,
      display: 'flex', alignItems: 'center', justifyContent: 'center'
    }}>
      <div className="glass-panel animate-fade-in" style={{ padding: '2rem', width: '560px', maxHeight: '90vh', overflowY: 'auto' }}>
        <h2 style={{ marginBottom: '0.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
          Importar Productos desde Excel
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
          Sube un archivo .xlsx con tu catálogo de productos (columnas: ID, CATEGORIA, NOMBRE,
          DESCRIPCION, MARCA, PRECIO, UNIDAD, MONEDA). Si un producto ya existe (mismo nombre y
          marca), se omite automáticamente.
        </p>

        <button type="button" onClick={handleDownloadTemplate} className="btn btn-secondary" style={{ marginBottom: '1.5rem' }}>
          ⬇ Descargar Plantilla
        </button>

        <div style={{ marginBottom: '1rem' }}>
          <label className="form-label">Archivo Excel (.xlsx) *</label>
          <input type="file" accept=".xlsx" onChange={handleFileChange} className="input-field" />
        </div>

        {structError && (
          <div style={{ padding: '0.75rem', backgroundColor: 'rgba(255,107,107,0.1)', color: '#ff6b6b', borderRadius: 'var(--radius)', marginBottom: '1rem', fontSize: '0.9rem' }}>
            {structError}
          </div>
        )}

        {rowErrors && (
          <div style={{ marginBottom: '1rem' }}>
            <div style={{ color: '#ff6b6b', fontWeight: '600', marginBottom: '0.5rem', fontSize: '0.9rem' }}>
              El archivo tiene errores y no se importó nada. Corrígelos y vuelve a intentarlo:
            </div>
            <div style={{ maxHeight: '220px', overflowY: 'auto', border: '1px solid var(--border-color)', borderRadius: 'var(--radius)' }}>
              {rowErrors.map((re, i) => (
                <div key={i} style={{ padding: '0.5rem 0.75rem', borderBottom: '1px solid var(--border-color)', fontSize: '0.85rem' }}>
                  <strong>Fila {re.fila}:</strong> {re.errores.join('; ')}
                </div>
              ))}
            </div>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1.5rem' }}>
          <button type="button" onClick={onCancel} className="btn btn-secondary">Cancelar</button>
          <button
            type="button"
            onClick={handleImport}
            className="btn btn-primary"
            disabled={!file || importing}
            style={{ opacity: (!file || importing) ? 0.6 : 1, cursor: (!file || importing) ? 'not-allowed' : 'pointer' }}
          >
            {importing ? 'Importando...' : 'Importar'}
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
