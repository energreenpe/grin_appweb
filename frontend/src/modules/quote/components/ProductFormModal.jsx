import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';

export default function ProductFormModal({ product, onSave, onCancel }) {
  const [formData, setFormData] = useState({
    nombre: '',
    descripcion: '',
    marca: '',
    modelo: '',
    categoria: '',
    unidad: 'Und',
    moneda: 'USD',
    precio: 0,
    costo: 0,
    activo: true
  });

  useEffect(() => {
    if (product) {
      setFormData({
        nombre: product.nombre || '',
        descripcion: product.descripcion || '',
        marca: product.marca || '',
        modelo: product.modelo || '',
        categoria: product.categoria || '',
        unidad: product.unidad || 'Und',
        moneda: product.moneda || 'USD',
        precio: product.precio || 0,
        costo: product.costo || 0,
        activo: product.activo ?? true
      });
    }
  }, [product]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  return createPortal(
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, 
      backgroundColor: 'rgba(0,0,0,0.7)', zIndex: 9999,
      display: 'flex', alignItems: 'center', justifyContent: 'center'
    }}>
      <div className="glass-panel animate-fade-in" style={{ padding: '2rem', width: '500px', maxHeight: '90vh', overflowY: 'auto' }}>
        <h2 style={{ marginBottom: '1.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
          {product ? 'Editar Producto' : 'Nuevo Producto'}
        </h2>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          
          <div>
            <label className="form-label">Nombre del Producto *</label>
            <input type="text" name="nombre" value={formData.nombre} onChange={handleChange} className="input-field" required />
          </div>

          <div>
            <label className="form-label">Descripción</label>
            <textarea name="descripcion" value={formData.descripcion} onChange={handleChange} className="input-field" rows="3" />
          </div>

          <div>
            <label className="form-label">Marca</label>
            <input type="text" name="marca" value={formData.marca} onChange={handleChange} className="input-field" />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <label className="form-label">Categoría *</label>
              <input type="text" name="categoria" value={formData.categoria} onChange={handleChange} className="input-field" required />
            </div>
            <div>
              <label className="form-label">Unidad de Medida</label>
              <input type="text" name="unidad" value={formData.unidad} onChange={handleChange} className="input-field" />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <label className="form-label">Moneda</label>
              <select name="moneda" value={formData.moneda} onChange={handleChange} className="input-field">
                <option value="USD">USD</option>
                <option value="PEN">PEN</option>
              </select>
            </div>
            <div>
              <label className="form-label">Precio Venta *</label>
              <input type="number" step="0.01" name="precio" value={formData.precio} onChange={handleChange} className="input-field" required />
            </div>
          </div>

          <div style={{ marginTop: '0.5rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
              <input type="checkbox" name="activo" checked={formData.activo} onChange={handleChange} style={{ width: '16px', height: '16px' }} />
              <span>Producto Activo (Visible en Búsquedas)</span>
            </label>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1.5rem' }}>
            <button type="button" onClick={onCancel} className="btn btn-secondary">Cancelar</button>
            <button type="submit" className="btn btn-primary">Guardar Producto</button>
          </div>
        </form>
      </div>
    </div>,
    document.body
  );
}
