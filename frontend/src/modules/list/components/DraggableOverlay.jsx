import { useRef, useState } from 'react';
import { GripHorizontal, Trash2 } from 'lucide-react';
import { rgbToHex, hexToRgb } from '../utils/coords.js';

export default function DraggableOverlay({
  overlay, bounds, selected, onSelect, onUpdate, pageScale, zoom = 1.0, onDelete,
}) {
  const [dragging, setDragging] = useState(false);
  const dragStart = useRef(null);

  const formatRGB = (rgb) => {
    if (!rgb) return 'rgb(255, 255, 255)';
    const [r, g, b] = rgb;
    return `rgb(${Math.round(r * 255)}, ${Math.round(g * 255)}, ${Math.round(b * 255)})`;
  };

  const handleMouseDown = (e, forceDrag = false) => {
    if (e.target.classList.contains('resize-handle')) return;
    e.stopPropagation();
    onSelect();
    setDragging(true);
    dragStart.current = { mx: e.clientX, my: e.clientY, pdfX: overlay.x, pdfY: overlay.y };

    const onMove = (ev) => {
      if (!dragStart.current) return;
      const dxPoints = ((ev.clientX - dragStart.current.mx) / zoom) * pageScale.scaleX;
      const dyPoints = ((ev.clientY - dragStart.current.my) / zoom) * pageScale.scaleY;
      onUpdate({ x: Math.max(0, dragStart.current.pdfX + dxPoints), y: Math.max(0, dragStart.current.pdfY + dyPoints) }, false);
    };
    const onUp = () => {
      setDragging(false);
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
      onUpdate({}, true);
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  };

  const handleResize = (e) => {
    e.stopPropagation();
    e.preventDefault();
    const startW = overlay.width, startH = overlay.height, sx = e.clientX, sy = e.clientY;
    const onMove = (ev) => {
      const dxPoints = ((ev.clientX - sx) / zoom) * pageScale.scaleX;
      const dyPoints = ((ev.clientY - sy) / zoom) * pageScale.scaleY;
      onUpdate({ width: Math.max(20, startW + dxPoints), height: Math.max(16, startH + dyPoints) }, false);
    };
    const onUp = () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
      onUpdate({}, true);
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  };

  const below = bounds.top < 50;

  return (
    <div
      className={`draggable-element overlay-element ${selected ? 'selected' : ''} ${dragging ? 'dragging' : ''}`}
      style={{ left: bounds.left, top: bounds.top, width: bounds.width, height: bounds.height, backgroundColor: formatRGB(overlay.color) }}
      onMouseDown={handleMouseDown}
    >
      {selected && (
        <>
          <div className={`element-toolbar glass ${below ? 'below' : ''}`} onMouseDown={(e) => e.stopPropagation()}>
            <div className="drag-handle" title="Arrastrar" onMouseDown={(e) => { e.stopPropagation(); e.preventDefault(); handleMouseDown(e, true); }}>
              <GripHorizontal size={14} />
            </div>
            <div className="toolbar-divider" />
            <div className="toolbar-color-picker" title="Color de máscara">
              <input type="color" value={rgbToHex(overlay.color)} onChange={(e) => onUpdate({ color: hexToRgb(e.target.value) }, true)} />
              <div className="color-indicator" style={{ backgroundColor: formatRGB(overlay.color) }} />
            </div>
            <div className="preset-colors-row">
              <div className="preset-color-dot" style={{ backgroundColor: '#ffffff' }} onClick={() => onUpdate({ color: [1, 1, 1] }, true)} title="Blanco" />
              <div className="preset-color-dot" style={{ backgroundColor: '#000000' }} onClick={() => onUpdate({ color: [0, 0, 0] }, true)} title="Negro" />
              <div className="preset-color-dot" style={{ backgroundColor: '#808080' }} onClick={() => onUpdate({ color: [0.5, 0.5, 0.5] }, true)} title="Gris" />
            </div>
            <div className="toolbar-divider" />
            <button className="toolbar-btn delete" onClick={onDelete} title="Eliminar"><Trash2 size={12} /></button>
          </div>
          <span className="overlay-label">Cobertura</span>
          <div className="resize-handle" onMouseDown={handleResize} />
        </>
      )}
    </div>
  );
}
