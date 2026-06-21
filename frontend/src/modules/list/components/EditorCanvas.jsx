import { useRef, useState, useEffect, useCallback } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

import DraggableField from './DraggableField.jsx';
import DraggableOverlay from './DraggableOverlay.jsx';
import { pdfToHtml, htmlToPdf, getScaleFactors } from '../utils/coords.js';

import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url';

pdfjs.GlobalWorkerOptions.workerSrc = workerUrl;

export default function EditorCanvas({
  pdfUrl, fields, overlays, selected, setSelected, activeTool, zoom,
  currentPage, setCurrentPage, setNumPages, pageScale, setPageScale,
  addField, addOverlay, updateField, updateOverlay, onDelete,
}) {
  const [cursorStyle, setCursorStyle] = useState('default');
  const [pdfError, setPdfError] = useState(null);
  const [numPages, setNumPagesLocal] = useState(0);
  const originalSizeRef = useRef({ width: 595.27, height: 841.89 });

  useEffect(() => {
    const map = { select: 'default', text: 'crosshair', overlay: 'crosshair' };
    setCursorStyle(map[activeTool] || 'default');
  }, [activeTool]);

  const handlePageClick = useCallback((e, pageNum) => {
    const targetPage = pageNum !== undefined ? pageNum : currentPage;
    if (pageNum !== undefined && pageNum !== currentPage) setCurrentPage(pageNum);

    // En modo selección la deselección la maneja handleCanvasClick (cubre toda el área).
    if (activeTool === 'select') return;

    const rect = e.currentTarget.getBoundingClientRect();
    const pdfCoords = htmlToPdf(e.clientX - rect.left, e.clientY - rect.top, 1, 1, pageScale.scaleX, pageScale.scaleY, zoom);

    if (activeTool === 'text') {
      addField(targetPage - 1, Math.max(0, pdfCoords.x - 75), Math.max(0, pdfCoords.y - 12));
    } else if (activeTool === 'overlay') {
      addOverlay(targetPage - 1, Math.max(0, pdfCoords.x - 60), Math.max(0, pdfCoords.y - 15));
    }
  }, [activeTool, zoom, currentPage, pageScale, addField, addOverlay, setSelected, setCurrentPage]);

  // Deselecciona al hacer clic en cualquier parte del lienzo que NO sea un elemento
  // (PDF, márgenes, fondo). Los elementos detienen el clic, así que si llega aquí y
  // el target no está dentro de un .draggable-element, fue un clic "afuera".
  const handleCanvasClick = useCallback((e) => {
    if (activeTool === 'select' && !e.target.closest('.draggable-element')) {
      setSelected(null);
    }
  }, [activeTool, setSelected]);

  const onDocLoaded = useCallback(({ numPages: np }) => {
    setNumPagesLocal(np);
    setNumPages(np);
  }, [setNumPages]);

  const onPageLoadSuccess = useCallback((page) => {
    const { originalWidth, originalHeight } = page;
    originalSizeRef.current = { width: originalWidth, height: originalHeight };
    setTimeout(() => {
      const pageEl = document.querySelector('.react-pdf__Page');
      const renderWidth = pageEl ? pageEl.getBoundingClientRect().width / zoom : page.width;
      const renderHeight = pageEl ? pageEl.getBoundingClientRect().height / zoom : page.height;
      setPageScale(getScaleFactors(originalWidth, originalHeight, renderWidth, renderHeight));
    }, 150);
  }, [zoom, setPageScale]);

  return (
    <main className="editor-canvas" style={{ cursor: cursorStyle }} onClick={handleCanvasClick}>
      <div className="scroll-viewport">
        <div className="canvas-container">
          <Document
            file={pdfUrl}
            onLoadSuccess={(pdf) => { setPdfError(null); onDocLoaded(pdf); }}
            onLoadError={(err) => { console.error('react-pdf error:', err); setPdfError(err); }}
            loading={<div className="document-loading"><div className="spinner-large" /><span>Cargando documento...</span></div>}
            error={<div className="document-error"><h3>Error al cargar PDF</h3><p>{pdfError ? `Detalle: ${pdfError.message}` : 'No se pudo cargar el archivo.'}</p></div>}
          >
            {numPages > 0 && Array.from(new Array(numPages), (el, index) => {
              const pageNum = index + 1;
              return (
                <div key={pageNum} className="pdf-page-wrapper" onClick={(e) => handlePageClick(e, pageNum)}>
                  <Page
                    pageNumber={pageNum}
                    scale={zoom}
                    onLoadSuccess={pageNum === 1 ? onPageLoadSuccess : undefined}
                    renderTextLayer
                    renderAnnotationLayer={false}
                    loading=""
                  />
                  <div className="elements-layer">
                    {overlays.filter((o) => o.page === pageNum - 1).map((o) => {
                      const bounds = pdfToHtml(o.x, o.y, o.width, o.height, pageScale.scaleX, pageScale.scaleY, zoom);
                      return (
                        <DraggableOverlay
                          key={o.id} overlay={o} bounds={bounds} selected={selected === o.id}
                          onSelect={() => { setSelected(o.id); setCurrentPage(pageNum); }}
                          onUpdate={(upd, commit) => updateOverlay(o.id, upd, commit)}
                          pageScale={pageScale} zoom={zoom} onDelete={onDelete}
                        />
                      );
                    })}
                    {fields.filter((f) => f.page === pageNum - 1).map((f) => {
                      const bounds = pdfToHtml(f.x, f.y, f.width, f.height, pageScale.scaleX, pageScale.scaleY, zoom);
                      return (
                        <DraggableField
                          key={f.id} field={f} left={bounds.left} top={bounds.top} width={bounds.width} height={bounds.height}
                          selected={selected === f.id}
                          onSelect={() => { setSelected(f.id); setCurrentPage(pageNum); }}
                          onUpdate={(upd, commit) => updateField(f.id, upd, commit)}
                          pageScale={pageScale} zoom={zoom} onDelete={onDelete}
                        />
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </Document>
        </div>
      </div>

      <div className="canvas-footer-hint">
        {activeTool === 'text' && <span>Haz clic en la página para colocar un campo de texto</span>}
        {activeTool === 'overlay' && <span>Haz clic para añadir una cobertura</span>}
        {activeTool === 'select' && selected && <span>Arrastra para mover • Tirador para redimensionar • <kbd>Supr</kbd> para borrar</span>}
        {activeTool === 'select' && !selected && <span>Selección: haz clic en un elemento para editarlo</span>}
      </div>
    </main>
  );
}
