import { useState, useCallback } from 'react';
import { UploadCloud, FileText, AlertCircle } from 'lucide-react';
import { listApi } from '../api/listApi';

const ALLOWED = ['.pdf', '.docx', '.xlsx'];
const MAX_MB = 25;

export default function UploadScreen({ onUpload, onBack }) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const [error, setError] = useState(null);

  const processFile = useCallback(async (file) => {
    if (!file) return;
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALLOWED.includes(ext)) {
      setError(`Formato no soportado. Válidos: ${ALLOWED.join(', ')}`);
      return;
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      setError(`El archivo supera el máximo de ${MAX_MB} MB.`);
      return;
    }

    setError(null);
    setUploading(true);
    setStatusMsg('Subiendo documento...');

    try {
      const res = await listApi.upload(file);
      let pdfName = res.pdf_name;
      let pdfUrl = res.pdf_url;

      if (res.status !== 'finished') {
        setStatusMsg('Convirtiendo a PDF...');
        const job = await listApi.pollJob(res.job_id);
        pdfName = job.result?.pdf_name || job.pdf_name;
        pdfUrl = job.result?.pdf_url || job.pdf_url;
      }

      onUpload({ pdf_name: pdfName, pdf_url: pdfUrl, original_name: file.name });
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Error al procesar el documento.');
    } finally {
      setUploading(false);
      setStatusMsg('');
    }
  }, [onUpload]);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files?.[0]) processFile(e.dataTransfer.files[0]);
  }, [processFile]);

  const handleFileChange = (e) => {
    if (e.target.files?.[0]) processFile(e.target.files[0]);
  };

  return (
    <div className="list-upload-screen">
      {onBack && (
        <button className="btn btn-secondary list-upload-back" onClick={onBack}>
          ← Volver a la lista
        </button>
      )}
      <div className="upload-container">
        <div className="upload-header">
          <h1 className="logo-text">LIST</h1>
          <p className="subtitle">Editor visual y estampado de documentos</p>
        </div>

        <div
          className={`dropzone ${dragging ? 'drag-active' : ''} ${uploading ? 'upload-processing' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => !uploading && document.getElementById('list-file-input').click()}
        >
          <input
            id="list-file-input"
            type="file"
            accept=".pdf,.docx,.xlsx"
            style={{ display: 'none' }}
            onChange={handleFileChange}
            disabled={uploading}
          />

          {uploading ? (
            <div className="processing-wrapper">
              <div className="spinner-large" />
              <h3>{statusMsg || 'Procesando...'}</h3>
              <p>Esto puede tardar unos segundos si requiere conversión.</p>
            </div>
          ) : (
            <div className="dropzone-content">
              <div className="icon-glow"><UploadCloud className="upload-icon-svg" /></div>
              <h3>Arrastra tu archivo aquí</h3>
              <p className="highlight">o haz clic para explorar en tu equipo</p>
              <div className="supported-formats">
                <span className="badge docx"><FileText size={12} /> Word (.docx)</span>
                <span className="badge xlsx"><FileText size={12} /> Excel (.xlsx)</span>
                <span className="badge pdf"><FileText size={12} /> PDF (.pdf)</span>
              </div>
            </div>
          )}
        </div>

        {error && (
          <div className="error-banner">
            <AlertCircle className="error-icon" size={18} />
            <span>{error}</span>
          </div>
        )}

        <div className="upload-footer">
          <p>Máximo {MAX_MB} MB por archivo • Los temporales se eliminan automáticamente.</p>
        </div>
      </div>
    </div>
  );
}
