import { useState, useEffect, useCallback } from 'react';
import { useQuoteStore } from '../store/quoteStore';
import { quoteApi } from '../api/quoteApi';
import { notify } from '../../../lib/notify';
import ProductPartitionModal from './ProductPartitionModal';

// Alto que deja ver ~5 filas a la vez; el resto se ve con scroll vertical.
const TABLE_MAX_HEIGHT = '360px';
const stickyTh = { position: 'sticky', top: 0, zIndex: 1 };

export default function ProductSearch({ cotizacionId }) {
  const [query, setQuery] = useState('');
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);

  const { addItem } = useQuoteStore();

  // Carga productos: los primeros si no hay búsqueda, o las coincidencias si la hay.
  const loadProducts = useCallback(async (q = '') => {
    setLoading(true);
    try {
      const data = await quoteApi.getProducts(q);
      setProducts(data);
    } catch (err) {
      console.error(err);
      notify('No se pudieron cargar los productos. Revisa tu conexión.');
    } finally {
      setLoading(false);
    }
  }, []);

  // Carga inicial (primeros 5) y búsqueda con debounce (no consulta en cada tecla).
  useEffect(() => {
    const t = setTimeout(() => loadProducts(query.trim()), 300);
    return () => clearTimeout(t);
  }, [query, loadProducts]);

  const handleConfirmAdd = (particion, subparticion) => {
    addItem(cotizacionId, selectedProduct, 1, particion, subparticion);
    setSelectedProduct(null);
  };

  return (
    <div>
      {/* Barra de búsqueda */}
      <div style={{ position: 'relative', marginBottom: '1rem' }}>
        <span style={{ position: 'absolute', left: '0.75rem', top: '0.5rem', color: 'var(--text-secondary)' }}>
          🔍
        </span>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Buscar producto por nombre, marca o categoría..."
          className="input-field"
          style={{ paddingLeft: '2rem' }}
        />
      </div>

      {/* Tabla de productos: contiene todos, muestra ~5 con scroll vertical */}
      <div className="table-container" style={{ maxHeight: TABLE_MAX_HEIGHT, overflowY: 'auto' }}>
        <table>
          <thead>
            <tr>
              <th style={stickyTh}>Producto</th>
              <th style={{ ...stickyTh, width: '150px' }}>Categoría</th>
              <th style={{ ...stickyTh, width: '120px' }}>Marca</th>
              <th style={{ ...stickyTh, width: '130px' }}>Precio Base</th>
              <th style={{ ...stickyTh, width: '100px' }}></th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="5" style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-secondary)' }}>
                  Cargando...
                </td>
              </tr>
            ) : products.length === 0 ? (
              <tr>
                <td colSpan="5" style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-secondary)' }}>
                  {query.trim() ? 'No se encontraron productos' : 'No hay productos registrados'}
                </td>
              </tr>
            ) : (
              products.map((p) => (
                <tr key={p.id}>
                  <td>
                    <div style={{ fontWeight: 500 }}>{p.nombre}</div>
                    {p.descripcion && (
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{p.descripcion}</div>
                    )}
                  </td>
                  <td style={{ fontSize: '0.85rem' }}>{p.categoria}</td>
                  <td style={{ fontSize: '0.85rem' }}>{p.marca}</td>
                  <td style={{ fontSize: '0.85rem' }}>
                    {p.moneda} {Number(p.precio).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <button
                      onClick={() => setSelectedProduct(p)}
                      className="btn btn-secondary"
                      style={{ padding: '0.25rem 0.6rem', fontSize: '0.8rem' }}
                    >
                      + Agregar
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {selectedProduct && (
        <ProductPartitionModal
          product={selectedProduct}
          onConfirm={handleConfirmAdd}
          onCancel={() => setSelectedProduct(null)}
        />
      )}
    </div>
  );
}
