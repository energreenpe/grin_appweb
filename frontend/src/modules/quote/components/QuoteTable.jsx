import { useState } from 'react';
import { useQuoteStore } from '../store/quoteStore';

export default function QuoteTable({ cotizacionId }) {
  const { items, updateItem, removeItem, reorderItems } = useQuoteStore();
  const [draggedIndex, setDraggedIndex] = useState(null);

  const handleUpdate = (id, field, value) => {
    updateItem(cotizacionId, id, { [field]: value });
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
            <th style={{ width: '150px' }}>Partición</th>
            <th style={{ width: '150px' }}>Sub-Partición</th>
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
                draggable
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
                    value={item.cantidad} 
                    onChange={e => handleUpdate(item.id, 'cantidad', e.target.value)}
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
                    className="input-field"
                    style={{ padding: '0.25rem', marginBottom: '4px' }}
                  />
                  <textarea 
                    value={item.descripcion || ''} 
                    onChange={e => handleUpdate(item.id, 'descripcion', e.target.value)}
                    className="input-field"
                    style={{ padding: '0.25rem', fontSize: '0.8rem', minHeight: '40px' }}
                    placeholder="Descripción (opcional)"
                  />
                </td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{item.moneda}</span>
                    <input 
                      type="number" 
                      value={item.precio_unit} 
                      onChange={e => handleUpdate(item.id, 'precio_unit', e.target.value)}
                      className="input-field"
                      style={{ padding: '0.25rem' }}
                    />
                  </div>
                </td>
                <td style={{ fontWeight: '600', color: 'var(--primary-color)' }}>
                  {item.moneda} {Number(item.subtotal || (item.cantidad * item.precio_unit)).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                </td>
                <td>
                  <input 
                    type="text" 
                    value={item.particion} 
                    onChange={e => handleUpdate(item.id, 'particion', e.target.value)}
                    className="input-field"
                    style={{ padding: '0.25rem' }}
                  />
                </td>
                <td>
                  <input 
                    type="text" 
                    value={item.subparticion || ''} 
                    onChange={e => handleUpdate(item.id, 'subparticion', e.target.value)}
                    className="input-field"
                    style={{ padding: '0.25rem' }}
                  />
                </td>
                <td style={{ textAlign: 'center' }}>
                  <button 
                    onClick={() => removeItem(cotizacionId, item.id)}
                    className="btn btn-danger"
                    style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}
                    title="Eliminar"
                  >
                    X
                  </button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
