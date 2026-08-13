import { Trash2, Sliders } from 'lucide-react';
import { rgbToHex, hexToRgb, getMinFieldSize } from '../utils/coords.js';

const SYMBOL_TYPE_OPTIONS = [
  { value: 'check', label: '✔', title: 'Check' },
  { value: 'cross', label: '✘', title: 'Aspa' },
  { value: 'bullet', label: '•', title: 'Punto' },
];

export default function RightPanel({ open = true, selected, isField, isOverlay, updateField, updateOverlay, onDelete }) {
  if (!selected) {
    return (
      <aside className={`list-right-panel ${open ? '' : 'closed'}`}>
        <div className="panel-header">
          <div className="title-row"><Sliders size={14} className="panel-icon" /><span>Propiedades</span></div>
        </div>
        <div className="panel-body empty">
          <div className="empty-inspector">
            <Sliders size={28} className="inspector-decor-icon" />
            <p>Ningún elemento seleccionado</p>
            <span>Haz clic en un campo o cobertura para configurar sus propiedades.</span>
          </div>
        </div>
      </aside>
    );
  }

  // Cuadro mínimo para que el texto actual no desaparezca al exportar (ver
  // getMinFieldSize): por debajo de esto, pdf_stamp.py recorta el texto sin avisar.
  const minSize = isField ? getMinFieldSize(selected.text, selected.font_family, selected.font_size) : null;
  const isSymbol = isField && !!selected.symbol;

  const handleProp = (key, val) => {
    const n = parseFloat(val);
    if (Number.isNaN(n)) return;
    if (isField) {
      if (key === 'width') updateField({ width: Math.max(minSize.minWidth, n) });
      else if (key === 'height') updateField({ height: Math.max(minSize.minHeight, n) });
      else updateField({ [key]: n });
    } else if (isOverlay) {
      updateOverlay({ [key]: n });
    }
  };

  const handleFontSize = (val) => {
    const fontSize = Math.max(6, parseInt(val, 10) || 12);
    const { minWidth, minHeight } = getMinFieldSize(selected.text, selected.font_family, fontSize);
    const updates = { font_size: fontSize };
    if (selected.width < minWidth) updates.width = minWidth;
    if (selected.height < minHeight) updates.height = minHeight;
    updateField(updates);
  };

  const overlayColor = selected.color || [1, 1, 1];

  return (
    <aside className={`list-right-panel ${open ? '' : 'closed'}`}>
      <div className="panel-header">
        <div className="title-row"><Sliders size={14} className="panel-icon" /><span>Propiedades</span></div>
        <span className={`badge-type ${isField ? 'field' : 'overlay'}`}>{isSymbol ? 'Símbolo' : isField ? 'Texto' : 'Máscara'}</span>
      </div>

      <div className="panel-body">
        <div className="property-group">
          <h4 className="group-title">Posición (PDF points)</h4>
          <div className="grid-2x2">
            <div className="input-field-wrapper"><label>Eje X</label><input type="number" value={Math.round(selected.x)} onChange={(e) => handleProp('x', e.target.value)} min="0" /></div>
            <div className="input-field-wrapper"><label>Eje Y</label><input type="number" value={Math.round(selected.y)} onChange={(e) => handleProp('y', e.target.value)} min="0" /></div>
            <div className="input-field-wrapper"><label>Ancho</label><input type="number" value={Math.round(selected.width)} onChange={(e) => handleProp('width', e.target.value)} min={isField ? minSize.minWidth : 10} /></div>
            <div className="input-field-wrapper"><label>Alto</label><input type="number" value={Math.round(selected.height)} onChange={(e) => handleProp('height', e.target.value)} min={isField ? minSize.minHeight : 10} /></div>
          </div>
        </div>

        {isField && isSymbol && (
          <div className="property-group">
            <h4 className="group-title">Símbolo</h4>
            <div className="toggle-bg-options">
              {SYMBOL_TYPE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  className={`toggle-bg-opt ${selected.symbol === opt.value ? 'active-opt' : ''}`}
                  onClick={() => updateField({ symbol: opt.value })}
                  title={opt.title}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            <div className="input-field-wrapper" style={{ marginTop: '12px' }}>
              <label>Tamaño</label>
              <input type="number" value={selected.font_size} onChange={(e) => handleFontSize(e.target.value)} min="6" max="72" />
            </div>
          </div>
        )}

        {isField && !isSymbol && (
          <>
            <div className="property-group">
              <h4 className="group-title">Contenido</h4>
              <div className="input-field-wrapper col">
                <textarea value={selected.text} onChange={(e) => updateField({ text: e.target.value })} placeholder="Texto que se estampará..." rows={4} />
              </div>
            </div>
            <div className="property-group">
              <h4 className="group-title">Tipografía</h4>
              <div className="input-field-wrapper">
                <label>Fuente</label>
                <select value={selected.font_family} onChange={(e) => updateField({ font_family: e.target.value })}>
                  <option value="Helvetica">Helvetica (Sans-serif)</option>
                  <option value="Times-Roman">Times New Roman (Serif)</option>
                  <option value="Courier">Courier (Monospace)</option>
                </select>
              </div>
              <div className="input-field-wrapper" style={{ marginTop: '12px' }}>
                <label>Tamaño</label>
                <input type="number" value={selected.font_size} onChange={(e) => handleFontSize(e.target.value)} min="6" max="72" />
              </div>
            </div>
          </>
        )}

        {isField && (
          <div className="property-group">
            <h4 className="group-title">Colores</h4>
            <div className="color-row">
              <label>{isSymbol ? 'Símbolo' : 'Texto'}</label>
              <div className="color-picker-wrap">
                <input type="color" value={rgbToHex(selected.font_color)} onChange={(e) => updateField({ font_color: hexToRgb(e.target.value) })} />
                <span className="hex-label">{rgbToHex(selected.font_color).toUpperCase()}</span>
              </div>
            </div>
            <div className="color-row" style={{ marginTop: '12px' }}>
              <label>Fondo</label>
              <div className="toggle-bg-options">
                <button className={`toggle-bg-opt ${!selected.bg_color ? 'active-opt' : ''}`} onClick={() => updateField({ bg_color: null })}>Transparente</button>
                <button className={`toggle-bg-opt ${selected.bg_color ? 'active-opt' : ''}`} onClick={() => updateField({ bg_color: [1, 1, 1] })}>Sólido</button>
              </div>
            </div>
            {selected.bg_color && (
              <div className="color-row" style={{ marginTop: '12px' }}>
                <label>Color fondo</label>
                <div className="color-picker-wrap">
                  <input type="color" value={rgbToHex(selected.bg_color)} onChange={(e) => updateField({ bg_color: hexToRgb(e.target.value) })} />
                  <span className="hex-label">{rgbToHex(selected.bg_color).toUpperCase()}</span>
                </div>
              </div>
            )}
          </div>
        )}

        {isOverlay && (
          <div className="property-group">
            <h4 className="group-title">Máscara</h4>
            <div className="color-row">
              <label>Relleno</label>
              <div className="color-picker-wrap">
                <input type="color" value={rgbToHex(overlayColor)} onChange={(e) => updateOverlay({ color: hexToRgb(e.target.value) })} />
                <span className="hex-label">{rgbToHex(overlayColor).toUpperCase()}</span>
              </div>
            </div>
            <div className="quick-colors" style={{ marginTop: '12px' }}>
              <button className="quick-color-btn white" onClick={() => updateOverlay({ color: [1, 1, 1] })} title="Blanco" />
              <button className="quick-color-btn black" onClick={() => updateOverlay({ color: [0, 0, 0] })} title="Negro" />
              <button className="quick-color-btn gray" onClick={() => updateOverlay({ color: [0.5, 0.5, 0.5] })} title="Gris" />
            </div>
          </div>
        )}

        <div className="panel-actions">
          <button className="delete-element-btn" onClick={onDelete}><Trash2 size={14} /><span>Eliminar elemento</span></button>
        </div>
      </div>
    </aside>
  );
}
