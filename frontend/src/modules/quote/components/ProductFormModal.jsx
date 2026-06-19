import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import SearchableSelect from '../../../components/SearchableSelect';

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
    if (!formData.nombre.trim()) {
      alert("El Nombre del Producto es obligatorio.");
      return;
    }
    if (!formData.descripcion.trim()) {
      alert("La Descripción es obligatoria.");
      return;
    }
    if (!formData.marca.trim()) {
      alert("La Marca es obligatoria.");
      return;
    }
    if (!formData.categoria.trim()) {
      alert("La Categoría es obligatoria.");
      return;
    }
    if (Number(formData.precio) <= 0) {
      alert("El precio de venta debe ser mayor a 0.");
      return;
    }
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
            <label className="form-label">Descripción *</label>
            <textarea name="descripcion" value={formData.descripcion} onChange={handleChange} className="input-field" rows="3" required />
          </div>

          <div>
            <label className="form-label">Marca *</label>
            <input type="text" name="marca" value={formData.marca} onChange={handleChange} className="input-field" required />
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
              <SearchableSelect
                value={formData.moneda}
                onChange={(v) => handleChange({ target: { name: 'moneda', value: v } })}
                options={[
                  { value: 'USD', label: 'USD' },
                  { value: 'PEN', label: 'PEN' },
                ]}
              />
            </div>
            <div>
              <label className="form-label">Precio Venta *</label>
              <input type="number" step="0.01" min="0.01" name="precio" value={formData.precio} onChange={handleChange} className="input-field" required />
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
