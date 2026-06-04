import { useState } from 'react';
import { useQuoteStore } from '../store/quoteStore';

export default function ProductPartitionModal({ product, onConfirm, onCancel }) {
  const [particion, setParticion] = useState("");
  const [subparticion, setSubparticion] = useState("");
  
  const { items } = useQuoteStore();
  
  // Extraer historial único de las particiones ya usadas en esta cotización
  const historyPartitions = Array.from(new Set(items.map(i => i.particion).filter(Boolean)));
  const historySubpartitions = Array.from(new Set(items.map(i => i.subparticion).filter(Boolean)));

  const handleSubmit = (e) => {
    e.preventDefault();
    onConfirm(particion, subparticion);
  };

  if (!product) return null;

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, 
      backgroundColor: 'rgba(0,0,0,0.7)', zIndex: 1000,
      display: 'flex', alignItems: 'center', justifyContent: 'center'
    }}>
      <div className="glass-panel" style={{ padding: '2rem', width: '400px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <h3 style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem', marginBottom: '0.5rem' }}>
          Agregar Ítem
        </h3>
        
        <div style={{ marginBottom: '1rem', padding: '0.75rem', backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 'var(--radius)' }}>
          <div style={{ fontWeight: '600', color: 'var(--primary-color)' }}>{product.nombre}</div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{product.marca} - {product.modelo}</div>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Partición (Partida)</label>
            <input 
              type="text" 
              value={particion} 
              onChange={e => setParticion(e.target.value)}
              list="partitions-list"
              className="input-field"
              placeholder="Escribe nombre de partición"
              required
              autoFocus
            />
            <datalist id="partitions-list">
              {historyPartitions.map(p => <option key={p} value={p} />)}
            </datalist>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Sub-Partición (Sub-Partida)</label>
            <input 
              type="text" 
              value={subparticion} 
              onChange={e => setSubparticion(e.target.value)}
              list="subpartitions-list"
              className="input-field"
              placeholder="Escribe nombre de subpartición"
            />
            <datalist id="subpartitions-list">
              {historySubpartitions.map(sp => <option key={sp} value={sp} />)}
            </datalist>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1rem' }}>
            <button type="button" onClick={onCancel} className="btn btn-secondary">Cancelar</button>
            <button type="submit" className="btn btn-primary">Añadir a Cotización</button>
          </div>
        </form>
      </div>
    </div>
  );
}
