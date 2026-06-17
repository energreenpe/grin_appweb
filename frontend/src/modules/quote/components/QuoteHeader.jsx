import { useState, useEffect, useCallback } from 'react';
import { useQuoteStore } from '../store/quoteStore';
import { quoteApi } from '../api/quoteApi';
import { notify } from '../../../lib/notify';

export default function QuoteHeader({ readOnly = false }) {
  const { cotizacion, updateHeader } = useQuoteStore();
  const [clientes, setClientes] = useState([]);
  const [tipoCambio, setTipoCambio] = useState('');

  const loadClientes = useCallback(async () => {
    try {
      const data = await quoteApi.getClientes();
      setClientes(data);
    } catch (err) {
      console.error(err);
      notify('No se pudo cargar la lista de clientes.');
    }
  }, []);

  useEffect(() => {
    loadClientes();
  }, [loadClientes]);

  // Sincronizar el tipo de cambio desde la base de datos (con 2 decimales)
  useEffect(() => {
    if (cotizacion && cotizacion.tipo_cambio !== undefined && cotizacion.tipo_cambio !== null) {
      if (parseFloat(tipoCambio) !== parseFloat(cotizacion.tipo_cambio)) {
        setTipoCambio(Number(cotizacion.tipo_cambio).toFixed(2));
      }
    }
  }, [cotizacion?.id, cotizacion?.tipo_cambio]);

  if (!cotizacion) return null;

  // Autocompleta todos los campos del cliente desde un registro existente
  const fillFromCliente = (updates, c) => {
    updates.cliente_nombre     = c.nombre || '';
    updates.cliente_doc        = c.documento || '';
    updates.cliente_dir        = c.direccion || '';
    updates.cliente_atencion   = c.atencion || '';
    updates.cliente_referencia = c.referencia || '';
    updates.cliente_correo     = c.correo || '';
    updates.cliente_tel        = c.telefono || '';
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;

    const updates = { [name]: type === 'checkbox' ? checked : value };

    // Autocompletar al reconocer al cliente por nombre o por RUC/DNI.
    // NOTA: el cliente NO se guarda aquí; se persiste recién al "Generar PDF".
    if (name === 'cliente_nombre') {
      const match = clientes.find(c => c.nombre === value);
      if (match) fillFromCliente(updates, match);
    }
    if (name === 'cliente_doc') {
      const match = clientes.find(c => c.documento && c.documento === value);
      if (match) fillFromCliente(updates, match);
    }

    updateHeader(cotizacion.id, updates);
  };

  // Margen de utilidad: el usuario edita el % (entero, mínimo 0), se guarda como
  // multiplicador (18% -> 1.18). Va de 1 en 1% con los botones del input.
  const handleMargenChange = (e) => {
    let pct = parseInt(e.target.value, 10);
    if (isNaN(pct) || pct < 0) pct = 0;
    const utilidad = (1 + pct / 100).toFixed(2);
    updateHeader(cotizacion.id, { utilidad });
  };

  return (
    <fieldset disabled={readOnly} style={{ border: 'none', padding: 0, margin: 0, minInlineSize: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <h3 style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
        Datos de Cliente
      </h3>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Cliente</label>
          <input 
            type="text" 
            name="cliente_nombre"
            list="clientes-list"
            value={cotizacion.cliente_nombre || ''} 
            onChange={handleChange}
            className="input-field"
            placeholder="Nombre del cliente"
          />
          <datalist id="clientes-list">
            {clientes.map(c => (
              <option key={c.id} value={c.nombre} />
            ))}
          </datalist>
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>RUC / DNI</label>
          <input
            type="text"
            name="cliente_doc"
            list="clientes-doc-list"
            value={cotizacion.cliente_doc || ''}
            onChange={handleChange}
            className="input-field"
            placeholder="Documento"
          />
          <datalist id="clientes-doc-list">
            {clientes.filter(c => c.documento).map(c => (
              <option key={c.id} value={c.documento}>{c.nombre}</option>
            ))}
          </datalist>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1rem' }}>
        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Dirección</label>
          <input 
            type="text" 
            name="cliente_dir"
            value={cotizacion.cliente_dir || ''} 
            onChange={handleChange}
            className="input-field"
            placeholder="Dirección del cliente"
          />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Atención</label>
          <input 
            type="text" 
            name="cliente_atencion"
            value={cotizacion.cliente_atencion || ''} 
            onChange={handleChange}
            className="input-field"
            placeholder="Atención a..."
          />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Referencia</label>
          <input 
            type="text" 
            name="cliente_referencia"
            value={cotizacion.cliente_referencia || ''} 
            onChange={handleChange}
            className="input-field"
            placeholder="Referencia de ubicación"
          />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Correo Electrónico</label>
          <input 
            type="text" 
            name="cliente_correo"
            value={cotizacion.cliente_correo || ''} 
            onChange={handleChange}
            className="input-field"
            placeholder="correo@cliente.com"
          />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Teléfono</label>
          <input 
            type="text" 
            name="cliente_tel"
            value={cotizacion.cliente_tel || ''} 
            onChange={handleChange}
            className="input-field"
            placeholder="Teléfono del cliente"
          />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Moneda</label>
          <select 
            name="moneda"
            value={cotizacion.moneda} 
            onChange={handleChange}
            className="input-field"
          >
            <option value="Soles (PEN)">Soles (PEN)</option>
            <option value="Dólares (USD)">Dólares (USD)</option>
          </select>
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Tipo de Cambio</label>
          <input 
            type="text" 
            name="tipo_cambio"
            value={tipoCambio} 
            onChange={(e) => {
              // Permitir solo números y un punto
              const val = e.target.value.replace(/[^0-9.]/g, '');
              // Prevenir más de un punto decimal
              if ((val.match(/\./g) || []).length > 1) return;
              setTipoCambio(val);
            }}
            onBlur={() => {
              const val = parseFloat(tipoCambio);
              if (!isNaN(val)) {
                const formatted = val.toFixed(2);
                setTipoCambio(formatted);
                updateHeader(cotizacion.id, { tipo_cambio: formatted });
              } else {
                setTipoCambio(Number(cotizacion.tipo_cambio || 0).toFixed(2));
              }
            }}
            className="input-field"
          />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
         <div>
          <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Margen (Utilidad)</label>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <input
              type="number"
              name="utilidad"
              min="0"
              step="1"
              value={Math.round((Number(cotizacion.utilidad) - 1) * 100)}
              onChange={handleMargenChange}
              onKeyDown={e => { if (['.', ',', 'e', 'E', '-', '+'].includes(e.key)) e.preventDefault(); }}
              className="input-field"
              style={{ flex: 1 }}
            />
            <span style={{ color: 'var(--text-secondary)' }}>%</span>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'flex-end', paddingBottom: '0.5rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
            <input 
              type="checkbox" 
              name="mostrar_precios"
              checked={cotizacion.mostrar_precios} 
              onChange={handleChange}
              style={{ width: '16px', height: '16px' }}
            />
            <span style={{ fontSize: '0.9rem' }}>Mostrar precios en PDF</span>
          </label>
        </div>
      </div>
    </fieldset>
  );
}
