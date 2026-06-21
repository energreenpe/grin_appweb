import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useListStore } from '../store/listStore';
import { listApi } from '../api/listApi';
import { notify } from '../../../lib/notify';
import { useIsMobile } from '../../../lib/useIsMobile';
import UploadScreen from '../components/UploadScreen.jsx';
import Toolbar from '../components/Toolbar.jsx';
import LeftPanel from '../components/LeftPanel.jsx';
import EditorCanvas from '../components/EditorCanvas.jsx';
import RightPanel from '../components/RightPanel.jsx';
import '../list.css';

const stripId = ({ id, ...rest }) => rest;

export default function ListEditor() {
  const { id } = useParams();
  const navigate = useNavigate();
  const s = useListStore();

  const [exporting, setExporting] = useState(false);
  const [saveStatus, setSaveStatus] = useState('idle'); // idle | saving | saved | error
  const skipSave = useRef(true); // evita guardar justo después de abrir/crear

  // Paneles colapsables (responsive): visibles en escritorio, ocultos en móvil.
  const isMobile = useIsMobile();
  const [leftOpen, setLeftOpen] = useState(!isMobile);
  const [rightOpen, setRightOpen] = useState(!isMobile);
  useEffect(() => { setLeftOpen(!isMobile); setRightOpen(!isMobile); }, [isMobile]);

  const docId = id ? Number(id) : null;
  const needsLoad = docId != null && docId !== s.documentId;

  // ── Cargar documento existente (/list/:id) ──────────────────────────────────
  useEffect(() => {
    if (docId == null || docId === s.documentId) return;
    let cancelled = false;
    (async () => {
      try {
        const d = await listApi.getDocumento(docId);
        if (cancelled) return;
        skipSave.current = true;
        s.openDocument({ id: d.id, nombre: d.nombre, pdf_name: d.pdf_name, fields: d.fields, overlays: d.overlays });
      } catch (err) {
        notify('No se pudo abrir el documento.', 'error');
        navigate('/list');
      }
    })();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [docId]);

  // ── Subida nueva (/list/new): subir+convertir → crear documento → /list/:id ──
  const handleUploaded = useCallback(async (docInfo) => {
    try {
      const created = await listApi.createDocumento({
        nombre: docInfo.original_name,
        pdf_name: docInfo.pdf_name,
      });
      skipSave.current = true;
      s.openDocument({ id: created.id, nombre: created.nombre, pdf_name: created.pdf_name, fields: created.fields, overlays: created.overlays });
      navigate(`/list/${created.id}`, { replace: true });
    } catch (err) {
      notify('No se pudo registrar el documento.', 'error');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [navigate]);

  // ── Autoguardado (debounce 1.5s) ────────────────────────────────────────────
  useEffect(() => {
    if (!s.documentId) return;
    if (docId != null && docId !== s.documentId) return; // en transición de carga
    if (skipSave.current) { skipSave.current = false; return; }
    setSaveStatus('saving');
    const t = setTimeout(async () => {
      try {
        await listApi.updateDocumento(s.documentId, {
          fields: s.fields.map(stripId),
          overlays: s.overlays.map(stripId),
        });
        setSaveStatus('saved');
      } catch (err) {
        setSaveStatus('error');
      }
    }, 1500);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [s.fields, s.overlays, s.documentId]);

  // ── Atajos de teclado ───────────────────────────────────────────────────────
  useEffect(() => {
    const onKey = (e) => {
      const el = document.activeElement;
      if (el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.isContentEditable)) return;
      if (e.key === 'Delete' || e.key === 'Backspace') {
        if (s.selected) s.deleteSelected();
      } else if (e.key.toLowerCase() === 'z' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        s.undo();
      } else if (e.key.toLowerCase() === 'y' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        s.redo();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [s]);

  const handleExport = useCallback(async () => {
    if (!s.doc) return;
    setExporting(true);
    try {
      const { job_id } = await listApi.export({
        pdf_name: s.doc.pdf_name,
        fields: s.fields.map(stripId),
        overlays: s.overlays.map(stripId),
      });
      const job = await listApi.pollJob(job_id);
      const outName = job.result?.output_name;
      if (!outName) throw new Error('No se generó el documento.');
      const base = (s.doc.original_name || 'documento').split('.')[0];
      await listApi.downloadOutput(outName, `LIST_${base}_editado.pdf`);
      notify('PDF exportado correctamente.', 'success');
    } catch (err) {
      notify(err.response?.data?.detail || err.message || 'Error al exportar.', 'error');
    } finally {
      setExporting(false);
    }
  }, [s.doc, s.fields, s.overlays]);

  const handleSaveTemplate = useCallback(async (name) => {
    if (!s.doc) return;
    try {
      const res = await listApi.saveTemplate({
        nombre: name || `Plantilla ${s.doc.original_name}`,
        pdf_name: s.doc.pdf_name,
        fields: s.fields.map(stripId),
        overlays: s.overlays.map(stripId),
      });
      notify(`Plantilla guardada (id ${res.id}).`, 'success');
    } catch (err) {
      notify(err.response?.data?.detail || 'Error al guardar la plantilla.', 'error');
    }
  }, [s.doc, s.fields, s.overlays]);

  const handleLoadTemplate = useCallback(async (tid) => {
    if (!tid) return;
    try {
      const t = await listApi.getTemplate(tid);
      s.loadTemplate(t.fields, t.overlays);
      notify(`Plantilla "${t.nombre}" cargada.`, 'success');
    } catch (err) {
      notify(err.response?.data?.detail || 'Error al cargar la plantilla.', 'error');
    }
  }, [s]);

  // ── Render ───────────────────────────────────────────────────────────────────
  if (needsLoad) {
    return (
      <div className="list-app-shell" style={{ alignItems: 'center', justifyContent: 'center' }}>
        <div className="document-loading"><div className="spinner-large" /><span>Abriendo documento...</span></div>
      </div>
    );
  }

  if (!s.doc) {
    return <UploadScreen onUpload={handleUploaded} onBack={() => navigate('/list')} />;
  }

  const selectedItem = s.selected
    ? (s.fields.find((f) => f.id === s.selected) || s.overlays.find((o) => o.id === s.selected))
    : null;
  const isField = s.selected ? s.fields.some((f) => f.id === s.selected) : false;
  const isOverlay = s.selected ? s.overlays.some((o) => o.id === s.selected) : false;

  return (
    <div className="list-app-shell">
      <Toolbar
        docName={s.doc.original_name}
        saveStatus={saveStatus}
        leftOpen={leftOpen}
        rightOpen={rightOpen}
        onToggleLeft={() => setLeftOpen((v) => !v)}
        onToggleRight={() => setRightOpen((v) => !v)}
        activeTool={s.activeTool}
        setActiveTool={s.setActiveTool}
        zoom={s.zoom}
        setZoom={s.setZoom}
        currentPage={s.currentPage}
        numPages={s.numPages}
        setCurrentPage={s.setCurrentPage}
        onExport={handleExport}
        exporting={exporting}
        onSaveTemplate={handleSaveTemplate}
        onLoadTemplate={handleLoadTemplate}
        onNew={() => { s.reset(); navigate('/list'); }}
        canUndo={s.historyIndex > 0}
        canRedo={s.historyIndex < s.history.length - 1}
        onUndo={s.undo}
        onRedo={s.redo}
      />
      <div className="list-app-body">
        {isMobile && (leftOpen || rightOpen) && (
          <div className="list-panel-backdrop" onClick={() => { setLeftOpen(false); setRightOpen(false); }} />
        )}
        <LeftPanel open={leftOpen} fields={s.fields} overlays={s.overlays} selected={s.selected} setSelected={s.setSelected} currentPage={s.currentPage} />
        <EditorCanvas
          pdfUrl={listApi.pdfSrc(s.doc.pdf_name)}
          fields={s.fields}
          overlays={s.overlays}
          selected={s.selected}
          setSelected={s.setSelected}
          activeTool={s.activeTool}
          zoom={s.zoom}
          currentPage={s.currentPage}
          setCurrentPage={s.setCurrentPage}
          setNumPages={s.setNumPages}
          pageScale={s.pageScale}
          setPageScale={s.setPageScale}
          addField={s.addField}
          addOverlay={s.addOverlay}
          updateField={s.updateField}
          updateOverlay={s.updateOverlay}
          onDelete={s.deleteSelected}
        />
        <RightPanel
          open={rightOpen}
          selected={selectedItem}
          isField={isField}
          isOverlay={isOverlay}
          updateField={(upd) => s.selected && s.updateField(s.selected, upd, true)}
          updateOverlay={(upd) => s.selected && s.updateOverlay(s.selected, upd, true)}
          onDelete={s.deleteSelected}
        />
      </div>
    </div>
  );
}
