import { useRef, useState } from 'react';
import { GripHorizontal, Plus, Minus, Type, Trash2 } from 'lucide-react';
import { rgbToHex, hexToRgb } from '../utils/coords.js';

export default function DraggableField({
  field, left, top, width, height, selected, onSelect, onUpdate, pageScale, zoom = 1.0, onDelete,
}) {
  const [dragging, setDragging] = useState(false);
  const dragStart = useRef(null);

  const formatRGB = (rgb) => {
    if (!rgb) return 'transparent';
    const [r, g, b] = rgb;
    return `rgb(${Math.round(r * 255)}, ${Math.round(g * 255)}, ${Math.round(b * 255)})`;
  };

  const handleMouseDown = (e, forceDrag = false) => {
    if (e.target.classList.contains('resize-handle')) return;
    if (!forceDrag && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) return;
    e.stopPropagation();
    onSelect();
    setDragging(true);
    dragStart.current = { mx: e.clientX, my: e.clientY, pdfX: field.x, pdfY: field.y };

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
    const startW = field.width, startH = field.height, sx = e.clientX, sy = e.clientY;
    const onMove = (ev) => {
      const dxPoints = ((ev.clientX - sx) / zoom) * pageScale.scaleX;
      const dyPoints = ((ev.clientY - sy) / zoom) * pageScale.scaleY;
      onUpdate({ width: Math.max(30, startW + dxPoints), height: Math.max(16, startH + dyPoints) }, false);
    };
    const onUp = () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
      onUpdate({}, true);
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  };

  const below = top < 50;

  return (
    <div
      className={`draggable-element field-element ${selected ? 'selected' : ''} ${dragging ? 'dragging' : ''}`}
      style={{ left, top, width, height, backgroundColor: formatRGB(field.bg_color) }}
      onMouseDown={handleMouseDown}
    >
      {selected && (
        <div className={`element-toolbar glass ${below ? 'below' : ''}`} onMouseDown={(e) => e.stopPropagation()}>
          <div className="drag-handle" title="Arrastrar" onMouseDown={(e) => { e.stopPropagation(); e.preventDefault(); handleMouseDown(e, true); }}>
            <GripHorizontal size={14} />
          </div>
          <div className="toolbar-divider" />
          <button className="toolbar-btn" onClick={() => onUpdate({ font_size: Math.max(6, field.font_size - 1) }, true)} title="Reducir"><Minus size={12} /></button>
          <span className="toolbar-val">{field.font_size}</span>
          <button className="toolbar-btn" onClick={() => onUpdate({ font_size: Math.min(72, field.font_size + 1) }, true)} title="Aumentar"><Plus size={12} /></button>
          <div className="toolbar-divider" />
          <div className="toolbar-color-picker" title="Color de letra">
            <input type="color" value={rgbToHex(field.font_color)} onChange={(e) => onUpdate({ font_color: hexToRgb(e.target.value) }, true)} />
            <Type size={12} style={{ color: formatRGB(field.font_color) }} />
          </div>
          <button className={`toolbar-btn ${field.bg_color ? 'active' : ''}`} onClick={() => onUpdate({ bg_color: field.bg_color ? null : [1, 1, 1] }, true)} title="Fondo">
            <div className="bg-toggle-icon" style={{ backgroundColor: field.bg_color ? formatRGB(field.bg_color) : 'transparent' }} />
          </button>
          {field.bg_color && (
            <div className="toolbar-color-picker" title="Color de fondo">
              <input type="color" value={rgbToHex(field.bg_color)} onChange={(e) => onUpdate({ bg_color: hexToRgb(e.target.value) }, true)} />
              <div className="color-indicator" style={{ backgroundColor: formatRGB(field.bg_color) }} />
            </div>
          )}
          <div className="toolbar-divider" />
          <button className="toolbar-btn delete" onClick={onDelete} title="Eliminar"><Trash2 size={12} /></button>
        </div>
      )}

      <textarea
        className="field-input"
        style={{
          fontSize: `${field.font_size}px`,
          color: formatRGB(field.font_color),
          fontFamily: field.font_family === 'Courier' ? 'monospace' : 'var(--font-family)',
        }}
        value={field.text}
        placeholder="Escribe aquí..."
        onChange={(e) => onUpdate({ text: e.target.value }, true)}
        onClick={(e) => { e.stopPropagation(); onSelect(); }}
      />

      {selected && <div className="resize-handle" onMouseDown={handleResize} />}
    </div>
  );
}
