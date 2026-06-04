import { useState } from 'react';
import { useQuoteStore } from '../store/quoteStore';
import { quoteApi } from '../api/quoteApi';
import ProductPartitionModal from './ProductPartitionModal';

export default function ProductSearch({ cotizacionId }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  
  const { addItem } = useQuoteStore();

  const handleSearch = async (e) => {
    const val = e.target.value;
    setQuery(val);
    if (val.length < 3) {
      setResults([]);
      return;
    }
    
    setSearching(true);
    try {
      const data = await quoteApi.getProducts(val);
      setResults(data);
    } catch (err) {
      console.error(err);
    } finally {
      setSearching(false);
    }
  };

  const handleSelect = (product) => {
    setSelectedProduct(product);
  };

  const handleConfirmAdd = (particion, subparticion) => {
    addItem(cotizacionId, selectedProduct, 1, particion, subparticion);
    setQuery('');
    setResults([]);
    setSelectedProduct(null);
  };

  return (
    <div style={{ position: 'relative' }}>
      <input 
        type="text" 
        value={query}
        onChange={handleSearch}
        placeholder="Buscar producto por nombre, marca o categoría..."
        className="input-field"
        style={{ paddingLeft: '2rem' }}
      />
      <span style={{ position: 'absolute', left: '0.75rem', top: '0.5rem', color: 'var(--text-secondary)' }}>
        🔍
      </span>

      {searching && <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Buscando...</div>}

      {results.length > 0 && (
        <div style={{ 
          position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 10,
          backgroundColor: 'var(--surface-color)', border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius)', marginTop: '0.25rem', maxHeight: '300px', overflowY: 'auto',
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)'
        }}>
          {results.map(p => (
            <div 
              key={p.id}
              style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '0.75rem 1rem', borderBottom: '1px solid var(--border-color)'
              }}
            >
              <div>
                <div style={{ fontWeight: '500', fontSize: '0.9rem' }}>{p.nombre}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  {p.categoria} | {p.marca} | Precio Base: {p.moneda} {p.precio}
                </div>
              </div>
              <button 
                onClick={() => handleSelect(p)}
                className="btn btn-secondary"
                style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}
              >
                + Seleccionar
              </button>
            </div>
          ))}
        </div>
      )}

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
