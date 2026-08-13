import { Layers, FileText, Square } from 'lucide-react';

const SYMBOL_LABELS = { check: '✔ Símbolo (check)', cross: '✘ Símbolo (aspa)', bullet: '• Símbolo (punto)' };

export default function LeftPanel({ open = true, fields, overlays, selected, setSelected, currentPage }) {
  const pageFields = fields.filter((f) => f.page === currentPage - 1);
  const pageOverlays = overlays.filter((o) => o.page === currentPage - 1);
  const items = [
    ...pageFields.map((f) => ({ ...f, kind: 'field' })),
    ...pageOverlays.map((o) => ({ ...o, kind: 'overlay' })),
  ];

  return (
    <aside className={`list-left-panel ${open ? '' : 'closed'}`}>
      <div className="panel-header">
        <div className="title-row"><Layers size={14} className="panel-icon" /><span>Capas de página</span></div>
        <span className="count-badge">{items.length}</span>
      </div>

      <div className="panel-body">
        {items.length === 0 ? (
          <div className="panel-empty-state">
            <p className="primary-text">Sin elementos aún</p>
            <p className="secondary-text">Usa las herramientas de arriba para insertar campos o coberturas en esta página.</p>
          </div>
        ) : (
          <ul className="layers-list">
            {items.map((item) => {
              const isField = item.kind === 'field';
              return (
                <li
                  key={item.id}
                  className={`layer-item ${selected === item.id ? 'layer-selected' : ''}`}
                  onClick={() => setSelected(item.id)}
                >
                  <div className="layer-left">
                    <span className={`layer-badge ${item.kind}`}>{isField ? <FileText size={10} /> : <Square size={10} />}</span>
                    <span className="layer-label">
                      {isField
                        ? (item.symbol
                            ? (SYMBOL_LABELS[item.symbol] || 'Símbolo')
                            : (item.text.trim() || <span className="empty-text">Texto vacío...</span>))
                        : 'Cobertura / Máscara'}
                    </span>
                  </div>
                  <span className="layer-coords">{Math.round(item.x)},{Math.round(item.y)}</span>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <div className="panel-footer">
        <div className="stat-item"><span className="label">Campos</span><span className="value">{fields.length}</span></div>
        <div className="stat-item"><span className="label">Coberturas</span><span className="value">{overlays.length}</span></div>
      </div>
    </aside>
  );
}
