import { useState } from 'react';
import { useQuoteStore } from '../store/quoteStore';

export default function QuoteTable({ cotizacionId, readOnly = false }) {
  const { items, cotizacion, updateItem, removeItem, reorderItems } = useQuoteStore();
  const [draggedIndex, setDraggedIndex] = useState(null);

  // Símbolo de la moneda de la cotización (el subtotal viene convertido del backend)
  const monedaSimbolo = cotizacion?.moneda?.includes('USD') ? '$' : 'S/';

  const handleUpdate = (id, field, value) => {
    updateItem(cotizacionId, id, { [field]: value });
  };

  // Cantidad: solo enteros, mínimo 1 (no permite 0 ni negativos)
  const handleQtyChange = (id, raw) => {
    let n = parseInt(raw, 10);
    if (isNaN(n) || n < 1) n = 1;
    handleUpdate(id, 'cantidad', n);
  };

  const handleDragStart = (e, index) => {
    setDraggedIndex(index);
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", index);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = async (e, dropIndex) => {
    e.preventDefault();
    if (draggedIndex === null || draggedIndex === dropIndex) return;
    
    const newItems = [...items];
    const draggedItem = newItems[draggedIndex];
    newItems.splice(draggedIndex, 1);
    newItems.splice(dropIndex, 0, draggedItem);

    const newOrderIds = newItems.map(i => i.id);
    await reorderItems(cotizacionId, newOrderIds);
    setDraggedIndex(null);
  };

  return (
    <div className="table-container">
      <table>
        <thead>
          <tr>
            <th style={{ width: '40px' }}></th>
            <th style={{ width: '80px' }}>Cant.</th>
            <th style={{ width: '80px' }}>Und.</th>
            <th>Descripción</th>
            <th style={{ width: '130px' }}>Precio Unit.</th>
            <th style={{ width: '120px' }}>Subtotal</th>
            <th style={{ width: '150px' }}>Partida</th>
            <th style={{ width: '150px' }}>Sub-Partida</th>
            <th style={{ width: '60px' }}></th>
          </tr>
        </thead>
        <tbody>
          {items.length === 0 ? (
            <tr>
              <td colSpan="9" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                No hay ítems en esta cotización
              </td>
            </tr>
          ) : (
            items.map((item, index) => (
              <tr
                key={item.id}
                draggable={!readOnly}
                onDragStart={(e) => handleDragStart(e, index)}
                onDragOver={handleDragOver}
                onDrop={(e) => handleDrop(e, index)}
                style={{
                  opacity: draggedIndex === index ? 0.5 : 1,
                  backgroundColor: draggedIndex === index ? 'var(--surface-hover)' : 'transparent',
                  transition: 'background-color 0.2s'
                }}
              >
                <td style={{ cursor: 'grab', color: 'var(--text-secondary)', textAlign: 'center', fontSize: '1.2rem' }}>
                  ⋮⋮
                </td>
                <td>
                  <input
                    type="number"
                    min="1"
                    step="1"
                    value={parseInt(item.cantidad, 10) || 1}
                    onChange={e => handleQtyChange(item.id, e.target.value)}
                    onKeyDown={e => { if (['.', ',', 'e', 'E', '-', '+'].includes(e.key)) e.preventDefault(); }}
                    disabled={readOnly}
                    className="input-field"
                    style={{ padding: '0.25rem' }}
                  />
                </td>
                <td>{item.unidad}</td>
                <td>
                  <input 
                    type="text" 
                    value={item.nombre}
                    onChange={e => handleUpdate(item.id, 'nombre', e.target.value)}
                    disabled={readOnly}
                    className="input-field"
                    style={{ padding: '0.25rem', marginBottom: '4px' }}
                  />
                  <textarea 
                    value={item.descripcion || ''}
                    onChange={e => handleUpdate(item.id, 'descripcion', e.target.value)}
                    disabled={readOnly}
                    className="input-field"
                    style={{ padding: '0.25rem', fontSize: '0.8rem', minHeight: '40px' }}
                    placeholder="Descripción (opcional)"
                  />
                </td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{item.moneda}</span>
                    <span>
                      {Number(item.precio_unit).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                  </div>
                </td>
                <td style={{ fontWeight: '600', color: 'var(--primary-color)' }}>
                  {monedaSimbolo} {Number(item.subtotal || 0).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                </td>
                <td>
                  <input 
                    type="text" 
                    value={item.particion}
                    onChange={e => handleUpdate(item.id, 'particion', e.target.value)}
                    disabled={readOnly}
                    className="input-field"
                    style={{ padding: '0.25rem' }}
                  />
                </td>
                <td>
                  <input 
                    type="text" 
                    value={item.subparticion || ''}
                    onChange={e => handleUpdate(item.id, 'subparticion', e.target.value)}
                    disabled={readOnly}
                    className="input-field"
                    style={{ padding: '0.25rem' }}
                  />
                </td>
                <td style={{ textAlign: 'center' }}>
                  {!readOnly && (
                    <button
                      onClick={() => removeItem(cotizacionId, item.id)}
                      className="btn btn-danger"
                      style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}
                      title="Eliminar"
                    >
                      X
                    </button>
                  )}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
