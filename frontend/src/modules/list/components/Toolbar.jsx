import { useState } from 'react';
import {
  MousePointer, Type, Square, ChevronLeft, ChevronRight,
  ZoomIn, ZoomOut, Undo2, Redo2, Save, FolderOpen, Download, Layers, Sliders,
} from 'lucide-react';

export default function Toolbar({
  docName, saveStatus, leftOpen, rightOpen, onToggleLeft, onToggleRight,
  activeTool, setActiveTool, zoom, setZoom,
  currentPage, numPages, setCurrentPage, onExport, exporting,
  onSaveTemplate, onLoadTemplate, onNew,
  canUndo, canRedo, onUndo, onRedo,
}) {
  const saveLabel = {
    saving: 'Guardando…',
    saved: 'Guardado ✓',
    error: 'Error al guardar',
  }[saveStatus];
  const [showModal, setShowModal] = useState(false);
  const [action, setAction] = useState('save');
  const [templateName, setTemplateName] = useState('');
  const [templateId, setTemplateId] = useState('');

  const openDialog = (a) => { setAction(a); setTemplateName(''); setTemplateId(''); setShowModal(true); };
  const submit = () => {
    if (action === 'save') onSaveTemplate(templateName);
    else onLoadTemplate(templateId);
    setShowModal(false);
  };

  return (
    <header className="list-toolbar glass">
      <div className="toolbar-section left">
        <button className="logo-badge" onClick={onNew} title="Volver a la lista de documentos">← LIST</button>
        <span className="divider" />
        <span className="doc-title" title={docName}>{docName}</span>
        {saveLabel && <span className={`save-status ${saveStatus}`}>{saveLabel}</span>}
      </div>

      <div className="toolbar-section center">
        <button className={`tool-btn ${activeTool === 'select' ? 'active' : ''}`} onClick={() => setActiveTool('select')} title="Seleccionar (V)">
          <MousePointer className="tool-icon" /><span>Seleccionar</span>
        </button>
        <button className={`tool-btn ${activeTool === 'text' ? 'active' : ''}`} onClick={() => setActiveTool('text')} title="Campo de texto (T)">
          <Type className="tool-icon" /><span>Texto</span>
        </button>
        <button className={`tool-btn ${activeTool === 'overlay' ? 'active' : ''}`} onClick={() => setActiveTool('overlay')} title="Cobertura (O)">
          <Square className="tool-icon" /><span>Cobertura</span>
        </button>
      </div>

      <div className="toolbar-section right">
        <button
          className={`action-btn-sm ${leftOpen ? 'active' : ''}`}
          onClick={onToggleLeft}
          title="Mostrar/ocultar Capas"
        >
          <Layers className="tool-icon" />
        </button>
        <button
          className={`action-btn-sm ${rightOpen ? 'active' : ''}`}
          onClick={onToggleRight}
          title="Mostrar/ocultar Propiedades"
        >
          <Sliders className="tool-icon" />
        </button>
        <span className="divider-sm" />
        <div className="btn-group">
          <button className="action-btn-sm" onClick={onUndo} disabled={!canUndo} title="Deshacer (Ctrl+Z)"><Undo2 className="tool-icon" /></button>
          <button className="action-btn-sm" onClick={onRedo} disabled={!canRedo} title="Rehacer (Ctrl+Y)"><Redo2 className="tool-icon" /></button>
        </div>
        <span className="divider-sm" />

        {numPages > 0 && (
          <div className="page-navigator">
            <button className="nav-arrow" onClick={() => setCurrentPage((p) => Math.max(1, p - 1))} disabled={currentPage <= 1}><ChevronLeft size={16} /></button>
            <span className="page-display"><span className="current">{currentPage}</span><span className="separator">/</span><span className="total">{numPages}</span></span>
            <button className="nav-arrow" onClick={() => setCurrentPage((p) => Math.min(numPages, p + 1))} disabled={currentPage >= numPages}><ChevronRight size={16} /></button>
          </div>
        )}
        <span className="divider-sm" />

        <div className="zoom-widget">
          <button className="zoom-action" onClick={() => setZoom((z) => Math.max(0.5, +(z - 0.1).toFixed(1)))} disabled={zoom <= 0.5}><ZoomOut size={14} /></button>
          <span className="zoom-text">{Math.round(zoom * 100)}%</span>
          <button className="zoom-action" onClick={() => setZoom((z) => Math.min(2.0, +(z + 0.1).toFixed(1)))} disabled={zoom >= 2.0}><ZoomIn size={14} /></button>
        </div>
        <span className="divider-sm" />

        <div className="btn-group">
          <button className="action-btn" onClick={() => openDialog('save')} title="Guardar como plantilla"><Save size={16} /><span>Plantilla</span></button>
          <button className="action-btn" onClick={() => openDialog('load')} title="Cargar plantilla"><FolderOpen size={16} /></button>
        </div>
        <span className="divider" />

        <button className={`export-btn-primary ${exporting ? 'loading-state' : ''}`} onClick={onExport} disabled={exporting}>
          {exporting ? (<><div className="spinner" /><span>Exportando...</span></>) : (<><Download size={16} /><span>Exportar PDF</span></>)}
        </button>
      </div>

      {showModal && (
        <div className="template-modal-backdrop" onClick={() => setShowModal(false)}>
          <div className="template-modal-content glass" onClick={(e) => e.stopPropagation()}>
            <h2>{action === 'save' ? 'Guardar Plantilla' : 'Cargar Plantilla'}</h2>
            <p>{action === 'save'
              ? 'Asigna un nombre para identificar la distribución de campos.'
              : 'Pega el identificador (id) de la plantilla a importar.'}</p>
            {action === 'save' ? (
              <input className="input-field" type="text" placeholder="Ej. Formulario A4" value={templateName} onChange={(e) => setTemplateName(e.target.value)} autoFocus />
            ) : (
              <input className="input-field" type="text" placeholder="Ej. 12" value={templateId} onChange={(e) => setTemplateId(e.target.value)} autoFocus />
            )}
            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancelar</button>
              <button className="btn btn-primary" onClick={submit} disabled={action === 'save' ? !templateName.trim() : !templateId.trim()}>Confirmar</button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
