import { useRef, useState } from 'react';
import { GripHorizontal, Plus, Minus, Type, Trash2 } from 'lucide-react';
import { rgbToHex, hexToRgb, getMinFieldSize } from '../utils/coords.js';

// Glifos SOLO para íconos de botones (barra flotante, no la vista previa del
// campo): ahí da igual la fuente que los dibuje, son controles, no el resultado.
const SYMBOL_CHARS = { check: '✔', cross: '✘', bullet: '•' };

// Formas vectoriales de la vista previa — DEBEN coincidir con pdf_stamp.py
// (_CHECK_POINTS / _CROSS_LINES), salvo el eje Y invertido: SVG crece hacia
// abajo, reportlab/PDF crece hacia arriba. Dibujar acá la MISMA forma (en vez
// del glifo Unicode ✔/✘, que ninguna fuente de PDF estándar tiene) es lo que
// garantiza que el editor muestre EXACTAMENTE lo que se exporta — misma forma
// y misma posición dentro del cuadro, no solo un símbolo "parecido".
const CHECK_POINTS_SVG = [[0.12, 0.5], [0.4, 0.82], [0.9, 0.2]];
const CROSS_LINES_SVG = [
  [[0.15, 0.15], [0.85, 0.85]],
  [[0.15, 0.85], [0.85, 0.15]],
];

function SymbolShape({ symbol, color, width, height, strokeWidth }) {
  const w = Math.max(1, width);
  const h = Math.max(1, height);

  if (symbol === 'bullet') {
    const r = Math.min(w, h) * 0.28;
    return (
      <svg width="100%" height="100%" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
        <circle cx={w / 2} cy={h / 2} r={r} fill={color} />
      </svg>
    );
  }

  if (symbol === 'check') {
    const points = CHECK_POINTS_SVG.map(([fx, fy]) => `${fx * w},${fy * h}`).join(' ');
    return (
      <svg width="100%" height="100%" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
        <polyline points={points} fill="none" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }

  if (symbol === 'cross') {
    return (
      <svg width="100%" height="100%" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
        {CROSS_LINES_SVG.map(([[x1, y1], [x2, y2]], i) => (
          <line key={i} x1={x1 * w} y1={y1 * h} x2={x2 * w} y2={y2 * h} stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" />
        ))}
      </svg>
    );
  }

  return null;
}

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
    // Nunca dejar que el cuadro quede más chico de lo que el texto actual
    // necesita: por debajo de eso, pdf_stamp.py lo recorta y el texto
    // desaparece del PDF exportado sin ningún aviso.
    const { minWidth, minHeight } = getMinFieldSize(field.text, field.font_family, field.font_size);
    const onMove = (ev) => {
      const dxPoints = ((ev.clientX - sx) / zoom) * pageScale.scaleX;
      const dyPoints = ((ev.clientY - sy) / zoom) * pageScale.scaleY;
      onUpdate({ width: Math.max(minWidth, startW + dxPoints), height: Math.max(minHeight, startH + dyPoints) }, false);
    };
    const onUp = () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
      onUpdate({}, true);
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  };

  // Cambia font_size y, si el cuadro quedó más chico de lo que ese tamaño
  // necesita, lo agranda para que el texto nunca desaparezca al exportar.
  const changeFontSize = (newSize) => {
    const { minWidth, minHeight } = getMinFieldSize(field.text, field.font_family, newSize);
    const updates = { font_size: newSize };
    if (field.width < minWidth) updates.width = minWidth;
    if (field.height < minHeight) updates.height = minHeight;
    onUpdate(updates, true);
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
          {field.symbol && (
            <>
              {Object.entries(SYMBOL_CHARS).map(([value, char]) => (
                <button
                  key={value}
                  className={`toolbar-btn ${field.symbol === value ? 'active' : ''}`}
                  onClick={() => onUpdate({ symbol: value }, true)}
                  title={value}
                >
                  {char}
                </button>
              ))}
              <div className="toolbar-divider" />
            </>
          )}
          <button className="toolbar-btn" onClick={() => changeFontSize(Math.max(6, field.font_size - 1))} title="Reducir"><Minus size={12} /></button>
          <span className="toolbar-val">{field.font_size}</span>
          <button className="toolbar-btn" onClick={() => changeFontSize(Math.min(72, field.font_size + 1))} title="Aumentar"><Plus size={12} /></button>
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

      {field.symbol ? (
        <div className="field-symbol-display">
          <SymbolShape
            symbol={field.symbol}
            color={formatRGB(field.font_color)}
            width={width}
            height={height}
            // Mismo cálculo que line_width en pdf_stamp.py, con los equivalentes
            // en pantalla (font_size ya escalado a px, width/height ya en px).
            strokeWidth={Math.max(
              1.2,
              Math.min(((field.font_size / (pageScale.scaleY || 1)) * zoom) * 0.14, Math.min(width, height) * 0.22)
            )}
          />
        </div>
      ) : (
        <textarea
          className="field-input"
          style={{
            // field.font_size está en puntos PDF (independiente del zoom); se
            // multiplica por zoom (igual que left/top/width/height vía pdfToHtml)
            // para que el tamaño visual del texto coincida con el de la caja en
            // cualquier nivel de zoom del editor.
            fontSize: `${(field.font_size / (pageScale.scaleY || 1)) * zoom}px`,
            color: formatRGB(field.font_color),
            fontFamily: field.font_family === 'Courier' ? 'monospace' : 'var(--font-family)',
          }}
          value={field.text}
          placeholder="Escribe aquí..."
          onChange={(e) => onUpdate({ text: e.target.value }, true)}
          onClick={(e) => { e.stopPropagation(); onSelect(); }}
        />
      )}

      {selected && <div className="resize-handle" onMouseDown={handleResize} />}
    </div>
  );
}
