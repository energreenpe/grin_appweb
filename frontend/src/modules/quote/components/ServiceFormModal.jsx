import { useState } from 'react';
import { useQuoteStore } from '../store/quoteStore';

export default function ServiceFormModal({ onConfirm, onCancel }) {
  const [descripcion, setDescripcion] = useState("");
  const [unidad, setUnidad] = useState("Und");
  const [cantidad, setCantidad] = useState("1");
  const [precio, setPrecio] = useState("");
  const [moneda, setMoneda] = useState("PEN");
  const [particion, setParticion] = useState("");
  const [subparticion, setSubparticion] = useState("");
  
  const { items } = useQuoteStore();
  
  const historyPartitions = Array.from(new Set(items.map(i => i.particion).filter(Boolean)));
  const historySubpartitions = Array.from(new Set(items.map(i => i.subparticion).filter(Boolean)));

  const handleSubmit = (e) => {
    e.preventDefault();
    
    const qty = parseFloat(cantidad);
    const prc = parseFloat(precio);
    
    if (isNaN(qty) || isNaN(prc)) {
      alert("La cantidad y el precio deben ser valores numéricos.");
      return;
    }

    const serviceProduct = {
      id: null,
      nombre: "Servicio Manual", // El PDF ignorará esto, solo se usa para validar BD
      descripcion: descripcion,
      marca: "",
      unidad: unidad,
      precio: prc,
      moneda: moneda
    };

    onConfirm(serviceProduct, qty, particion, subparticion);
  };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, 
      backgroundColor: 'rgba(0,0,0,0.7)', zIndex: 1000,
      display: 'flex', alignItems: 'center', justifyContent: 'center'
    }}>
      <div className="glass-panel animate-fade-in" style={{ padding: '2rem', width: '500px', maxHeight: '90vh', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <h3 style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem', marginBottom: '0.5rem' }}>
          Agregar Servicio
        </h3>
        
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Descripción de servicio</label>
            <textarea 
              value={descripcion} 
              onChange={e => setDescripcion(e.target.value)}
              className="input-field"
              rows="3"
              required
              autoFocus
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Unidad</label>
              <select value={unidad} onChange={e => setUnidad(e.target.value)} className="input-field">
                <option value="Und">Und</option>
                <option value="Kg">Kg</option>
                <option value="Lt">Lt</option>
                <option value="Mts">Mts</option>
                <option value="Glb">Glb</option>
                <option value="Kit">Kit</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Cantidad</label>
              <input 
                type="number" 
                min="1" step="1"
                value={cantidad} 
                onChange={e => setCantidad(e.target.value)}
                className="input-field"
                required
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Precio Base</label>
              <input 
                type="number" 
                min="0" step="0.01"
                value={precio} 
                onChange={e => setPrecio(e.target.value)}
                className="input-field"
                placeholder="0.00"
                required
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Moneda</label>
              <select value={moneda} onChange={e => setMoneda(e.target.value)} className="input-field">
                <option value="PEN">Soles (PEN)</option>
                <option value="USD">Dólares (USD)</option>
              </select>
            </div>
          </div>

          <hr style={{ border: 'none', borderTop: '1px solid var(--border-color)', margin: '0.5rem 0' }} />

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
            <button type="submit" className="btn btn-primary">Guardar Servicio</button>
          </div>
        </form>
      </div>
    </div>
  );
}
