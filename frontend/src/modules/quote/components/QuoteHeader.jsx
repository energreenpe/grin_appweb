import { useState, useEffect, useCallback, useRef } from 'react';
import { useQuoteStore } from '../store/quoteStore';
import { quoteApi } from '../api/quoteApi';
import { notify } from '../../../lib/notify';
import SearchableSelect from '../../../components/SearchableSelect';

export default function QuoteHeader({ readOnly = false }) {
  const { cotizacion, updateHeader } = useQuoteStore();
  const [clientes, setClientes] = useState([]);
  const [tipoCambio, setTipoCambio] = useState('');
  const [showNombreDrop, setShowNombreDrop] = useState(false);
  const [showDocDrop, setShowDocDrop] = useState(false);
  const nombreRef = useRef(null);
  const docRef = useRef(null);

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

  // Cierra los dropdowns de cliente al tocar fuera (también funciona en móvil).
  useEffect(() => {
    const handler = (e) => {
      if (nombreRef.current && !nombreRef.current.contains(e.target)) setShowNombreDrop(false);
      if (docRef.current && !docRef.current.contains(e.target)) setShowDocDrop(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

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

  // Selecciona un cliente del dropdown y autocompleta todos sus campos.
  const seleccionarCliente = (c) => {
    const updates = {};
    fillFromCliente(updates, c);
    updateHeader(cotizacion.id, updates);
    setShowNombreDrop(false);
    setShowDocDrop(false);
  };

  // Listas filtradas y estilos del dropdown de cliente.
  const qNombre = (cotizacion.cliente_nombre || '').trim().toLowerCase();
  const clientesNombre = qNombre ? clientes.filter(c => c.nombre.toLowerCase().includes(qNombre)) : clientes;
  const qDoc = (cotizacion.cliente_doc || '').trim().toLowerCase();
  const clientesDoc = clientes.filter(c => c.documento && (qDoc ? c.documento.toLowerCase().includes(qDoc) : true));
  const dropStyle = {
    position: 'absolute', top: '100%', left: 0, right: 0, background: 'var(--surface-color)',
    border: '1px solid var(--border-color)', borderRadius: 'var(--radius)', boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
    zIndex: 100, maxHeight: '240px', overflowX: 'hidden', overflowY: 'auto', marginTop: '4px',
  };
  const dropItem = {
    padding: '0.6rem 0.8rem', cursor: 'pointer', borderBottom: '1px solid var(--border-color)', fontSize: '0.9rem',
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
          <div ref={nombreRef} style={{ position: 'relative' }}>
            <input
              type="text"
              name="cliente_nombre"
              autoComplete="off"
              value={cotizacion.cliente_nombre || ''}
              onChange={(e) => { handleChange(e); setShowNombreDrop(true); }}
              onFocus={() => setShowNombreDrop(true)}
              className="input-field"
              placeholder="Nombre del cliente"
            />
            {showNombreDrop && clientesNombre.length > 0 && (
              <div style={dropStyle}>
                {clientesNombre.map(c => (
                  <div key={c.id} style={dropItem}
                    onMouseEnter={ev => (ev.currentTarget.style.background = 'rgba(255,255,255,0.06)')}
                    onMouseLeave={ev => (ev.currentTarget.style.background = 'transparent')}
                    onClick={() => seleccionarCliente(c)}>
                    <strong>{c.nombre}</strong>
                    {c.documento && <span style={{ color: 'var(--text-secondary)', marginLeft: '0.5rem', fontSize: '0.85rem' }}>{c.documento}</span>}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>RUC / DNI</label>
          <div ref={docRef} style={{ position: 'relative' }}>
            <input
              type="text"
              name="cliente_doc"
              autoComplete="off"
              value={cotizacion.cliente_doc || ''}
              onChange={(e) => { handleChange(e); setShowDocDrop(true); }}
              onFocus={() => setShowDocDrop(true)}
              className="input-field"
              placeholder="Documento"
            />
            {showDocDrop && clientesDoc.length > 0 && (
              <div style={dropStyle}>
                {clientesDoc.map(c => (
                  <div key={c.id} style={dropItem}
                    onMouseEnter={ev => (ev.currentTarget.style.background = 'rgba(255,255,255,0.06)')}
                    onMouseLeave={ev => (ev.currentTarget.style.background = 'transparent')}
                    onClick={() => seleccionarCliente(c)}>
                    <strong>{c.documento}</strong>
                    <span style={{ color: 'var(--text-secondary)', marginLeft: '0.5rem', fontSize: '0.85rem' }}>{c.nombre}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
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
          <SearchableSelect
            value={cotizacion.moneda}
            onChange={(v) => handleChange({ target: { name: 'moneda', value: v } })}
            options={[
              { value: 'Soles (PEN)', label: 'Soles (PEN)' },
              { value: 'Dólares (USD)', label: 'Dólares (USD)' },
            ]}
          />
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
