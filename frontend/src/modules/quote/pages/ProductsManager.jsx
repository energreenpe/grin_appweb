import { useState, useEffect, useCallback } from 'react';
import { quoteApi } from '../api/quoteApi';
import ProductFormModal from '../components/ProductFormModal';
import { notify } from '../../../lib/notify';

export default function ProductsManager() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  
  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);

  const loadProducts = useCallback(async (query = '') => {
    setLoading(true);
    try {
      const data = await quoteApi.getProducts(query);
      setProducts(data);
    } catch (err) {
      console.error(err);
      notify('No se pudieron cargar los productos. Revisa tu conexión.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProducts();
  }, [loadProducts]);

  const handleSearch = (e) => {
    e.preventDefault();
    loadProducts(search);
  };

  const handleCreate = () => {
    setEditingProduct(null);
    setIsModalOpen(true);
  };

  const handleEdit = (product) => {
    setEditingProduct(product);
    setIsModalOpen(true);
  };

  const handleDelete = async (id, nombre) => {
    if (!window.confirm(`¿Estás seguro de eliminar el producto: ${nombre}?`)) return;
    try {
      await quoteApi.deleteProduct(id);
      loadProducts(search);
    } catch (err) {
      console.error(err);
      notify(err?.response?.data?.detail || "No se pudo eliminar el producto.");
    }
  };

  const handleSaveModal = async (formData) => {
    try {
      if (editingProduct) {
        await quoteApi.updateProduct(editingProduct.id, formData);
      } else {
        await quoteApi.createProduct(formData);
      }
      setIsModalOpen(false);
      loadProducts(search);
    } catch (err) {
      console.error(err);
      notify(err?.response?.data?.detail || "No se pudo guardar el producto.");
    }
  };

  return (
    <div className="animate-fade-in" style={{ padding: '1rem 0' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>Catálogo de Productos</h1>
          <p style={{ color: 'var(--text-secondary)' }}>Administra los productos disponibles para cotizar.</p>
        </div>
        <button onClick={handleCreate} className="btn btn-primary" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span>+</span> Nuevo Producto
        </button>
      </div>

      <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '1rem' }}>
          <input 
            type="text" 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por nombre, marca o categoría..."
            className="input-field"
            style={{ flex: 1 }}
          />
          <button type="submit" className="btn btn-secondary">Buscar</button>
          {search && (
            <button type="button" onClick={() => { setSearch(''); loadProducts(''); }} className="btn">
              Limpiar
            </button>
          )}
        </form>
      </div>

      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center' }}>Cargando productos...</div>
        ) : products.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            No se encontraron productos.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', backgroundColor: 'rgba(255,255,255,0.02)' }}>
                  <th style={{ padding: '1rem' }}>Nombre</th>
                  <th style={{ padding: '1rem' }}>Categoría</th>
                  <th style={{ padding: '1rem' }}>Marca</th>
                  <th style={{ padding: '1rem' }}>Precio</th>
                  <th style={{ padding: '1rem', textAlign: 'right' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {products.map(p => (
                  <tr key={p.id} style={{ borderBottom: '1px solid var(--border-color)' }} className="hover-bg">
                    <td style={{ padding: '1rem' }}>
                      <div style={{ fontWeight: '500' }}>{p.nombre}</div>
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <span style={{ padding: '4px 8px', backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: '12px', fontSize: '0.8rem' }}>
                        {p.categoria}
                      </span>
                    </td>
                    <td style={{ padding: '1rem' }}>{p.marca || '-'}</td>
                    <td style={{ padding: '1rem' }}>
                      <div style={{ fontWeight: '600', color: 'var(--primary-color)' }}>{p.moneda} {Number(p.precio).toFixed(2)}</div>
                    </td>
                    <td style={{ padding: '1rem', textAlign: 'right' }}>
                      <button onClick={() => handleEdit(p)} className="btn btn-secondary" style={{ padding: '0.4rem 0.8rem', marginRight: '0.5rem', fontSize: '0.85rem' }}>
                        Editar
                      </button>
                      <button onClick={() => handleDelete(p.id, p.nombre)} className="btn btn-secondary" style={{ padding: '0.4rem 0.8rem', color: '#ff6b6b', borderColor: 'rgba(255,107,107,0.2)', fontSize: '0.85rem' }}>
                        Eliminar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {isModalOpen && (
        <ProductFormModal 
          product={editingProduct}
          onSave={handleSaveModal}
          onCancel={() => setIsModalOpen(false)}
        />
      )}
    </div>
  );
}
