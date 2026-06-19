import React, { useState, useEffect, useRef } from 'react';
import { useCalculoStore } from '../../store/calculoStore';
import { mathApi } from '../../api/mathApi';

const TIPO_CLIENTE_OPTIONS = ['Persona', 'Empresa'];

export default function StepInicioCalculo({ onNext }) {
  const { data, setData } = useCalculoStore();

  const [nombreProyecto, setNombreProyecto] = useState(data.nombre_proyecto || '');
  const [tipoCliente, setTipoCliente] = useState(data.tipo_cliente || '');
  const [region, setRegion] = useState(data.region || '');
  const [regiones, setRegiones] = useState([]);
  const [regionSearch, setRegionSearch] = useState(data.region || '');
  const [showRegionDropdown, setShowRegionDropdown] = useState(false);

  // Cliente
  const [clienteSearch, setClienteSearch] = useState(data.cliente_info?.nombre || '');
  const [clienteResults, setClienteResults] = useState([]);
  const [clienteSeleccionado, setClienteSeleccionado] = useState(data.cliente_info || null);
  const [showClienteDropdown, setShowClienteDropdown] = useState(false);
  const [showNuevoCliente, setShowNuevoCliente] = useState(false);
  const [loadingCliente, setLoadingCliente] = useState(false);
  const [nuevoCliente, setNuevoCliente] = useState({
    nombre: '', documento: '', direccion: '', atencion: '', referencia: '', correo: '', telefono: '',
  });

  // Ingeniero
  const [ingenieroSearch, setIngenieroSearch] = useState(data.ingeniero_info?.nombre || '');
  const [ingenieroResults, setIngenieroResults] = useState([]);
  const [ingenieroSeleccionado, setIngenieroSeleccionado] = useState(data.ingeniero_info || null);
  const [allIngenieros, setAllIngenieros] = useState([]);
  const [showIngenieroDropdown, setShowIngenieroDropdown] = useState(false);
  const [loadingIngeniero, setLoadingIngeniero] = useState(false);

  const [loadingGuardar, setLoadingGuardar] = useState(false);
  const [error, setError] = useState('');

  const clienteRef = useRef(null);
  const ingenieroRef = useRef(null);
  const regionRef = useRef(null);

  // ── Cargar ingenieros y regiones al montar ──
  useEffect(() => {
    (async () => {
      try {
        setLoadingIngeniero(true);
        const [ings, regs] = await Promise.all([mathApi.getIngenieros(), mathApi.getRegiones()]);
        setAllIngenieros(ings);
        setRegiones(regs);
      } catch (e) {
        console.error('Error cargando ingenieros/regiones', e);
      } finally {
        setLoadingIngeniero(false);
      }
    })();
  }, []);

  // ── Cerrar dropdowns al clic fuera ──
  useEffect(() => {
    const handler = (e) => {
      if (clienteRef.current && !clienteRef.current.contains(e.target)) setShowClienteDropdown(false);
      if (ingenieroRef.current && !ingenieroRef.current.contains(e.target)) setShowIngenieroDropdown(false);
      if (regionRef.current && !regionRef.current.contains(e.target)) setShowRegionDropdown(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // ── Búsqueda de clientes con debounce ──
  useEffect(() => {
    if (clienteSearch.length < 2) { setClienteResults([]); return; }
    const t = setTimeout(async () => {
      setLoadingCliente(true);
      try {
        const res = await mathApi.searchClientes(clienteSearch);
        setClienteResults(res);
        setShowClienteDropdown(true);
      } catch (e) {
        console.error(e);
      } finally {
        setLoadingCliente(false);
      }
    }, 400);
    return () => clearTimeout(t);
  }, [clienteSearch]);

  // ── Filtro de ingenieros en tiempo real ──
  useEffect(() => {
    if (!ingenieroSearch) {
      setIngenieroResults(allIngenieros);
    } else {
      setIngenieroResults(
        allIngenieros.filter((i) => i.nombre.toLowerCase().includes(ingenieroSearch.toLowerCase()))
      );
    }
  }, [ingenieroSearch, allIngenieros]);

  const handleSelectCliente = (c) => {
    setClienteSeleccionado(c);
    setClienteSearch(c.nombre);
    setShowClienteDropdown(false);
    setShowNuevoCliente(false);
    setData({ cliente_id: c.id, cliente_info: c });
  };

  const handleCrearCliente = async (e) => {
    e.preventDefault();
    if (!nuevoCliente.nombre.trim()) return;
    setLoadingGuardar(true);
    try {
      const created = await mathApi.createCliente(nuevoCliente);
      handleSelectCliente(created);
      setShowNuevoCliente(false);
    } catch {
      setError('Error al crear el cliente. Intenta nuevamente.');
    } finally {
      setLoadingGuardar(false);
    }
  };

  const handleSelectIngeniero = (i) => {
    setIngenieroSeleccionado(i);
    setIngenieroSearch(i.nombre);
    setShowIngenieroDropdown(false);
    setData({ ingeniero_id: i.id, ingeniero_info: i });
  };

  const handleContinuar = () => {
    setError('');
    if (!nombreProyecto.trim()) { setError('Indica el nombre del proyecto.'); return; }
    if (!tipoCliente) { setError('Selecciona el tipo de cliente.'); return; }
    if (!clienteSeleccionado) { setError('Debes seleccionar o crear un cliente.'); return; }
    if (!ingenieroSeleccionado) { setError('Debes seleccionar el ingeniero responsable.'); return; }
    if (!region) { setError('Selecciona la región del proyecto.'); return; }
    const newData = {
      ...data,
      nombre_proyecto: nombreProyecto.trim(),
      tipo_cliente: tipoCliente,
      cliente_id: clienteSeleccionado.id,
      cliente_info: clienteSeleccionado,
      ingeniero_id: ingenieroSeleccionado.id,
      ingeniero_info: ingenieroSeleccionado,
      region,
    };
    setData(newData);
    onNext(newData);
  };

  // ── Estilos compartidos ──
  const inputStyle = {
    width: '100%', padding: '0.65rem 0.9rem', background: 'var(--surface-color)',
    border: '1px solid var(--border-color)', borderRadius: '8px', color: 'var(--text-primary)',
    fontSize: '0.95rem', boxSizing: 'border-box', outline: 'none',
  };
  const labelStyle = {
    display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)',
    marginBottom: '0.4rem', textTransform: 'uppercase', letterSpacing: '0.04em',
  };
  const dropdownStyle = {
    position: 'absolute', top: '100%', left: 0, right: 0, background: 'var(--surface-color)',
    border: '1px solid var(--border-color)', borderRadius: '8px', boxShadow: '0 8px 24px rgba(0,0,0,0.35)',
    zIndex: 100, maxHeight: '220px', overflowX: 'hidden', overflowY: 'auto', marginTop: '4px',
  };

  // Regiones filtradas para el dropdown buscable (todas si no hay búsqueda activa).
  const regionesFiltradas = (regionSearch.trim() && regionSearch !== region)
    ? regiones.filter((r) => r.nombre.toLowerCase().includes(regionSearch.trim().toLowerCase()))
    : regiones;
  const dropdownItemStyle = {
    padding: '0.7rem 1rem', cursor: 'pointer', borderBottom: '1px solid var(--border-color)',
    fontSize: '0.9rem', transition: 'background 0.15s',
  };
  const sectionHeaderStyle = {
    fontSize: '1rem', fontWeight: 700, color: 'var(--primary-color)', display: 'flex',
    alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', paddingBottom: '0.5rem',
    borderBottom: '1px solid var(--border-color)',
  };
  const chipStyle = (selected) => ({
    padding: '0.55rem 1.1rem', borderRadius: '30px',
    border: selected ? '2px solid var(--primary-color)' : '1px solid var(--border-color)',
    background: selected ? 'rgba(98,185,137,0.18)' : 'transparent',
    color: selected ? 'var(--primary-color)' : 'var(--text-secondary)',
    cursor: 'pointer', fontWeight: selected ? 700 : 400, fontSize: '0.9rem', transition: 'all 0.2s',
  });
  const cardSeleccion = {
    background: 'rgba(98,185,137,0.08)', border: '1px solid rgba(98,185,137,0.3)', borderRadius: '10px',
    padding: '0.9rem 1rem', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between',
    gap: '0.5rem', marginTop: '0.75rem',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <div style={{ textAlign: 'center' }}>
        <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '0.3rem' }}>Nuevo Cálculo Solar</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          Datos del proyecto, cliente e ingeniero responsable
        </p>
      </div>

      {/* ── Proyecto + Región ── */}
      <div>
        <div style={sectionHeaderStyle}><span>📐</span> Proyecto</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.85rem' }}>
          <div style={{ gridColumn: '1 / -1' }}>
            <label style={labelStyle}>Nombre del proyecto / cálculo *</label>
            <input
              type="text" style={inputStyle} placeholder="Ej. Vivienda Sr. Pérez - Aislado"
              value={nombreProyecto} onChange={(e) => setNombreProyecto(e.target.value)}
            />
          </div>
          <div style={{ gridColumn: '1 / -1' }} ref={regionRef}>
            <label style={labelStyle}>Región *</label>
            <div style={{ position: 'relative' }}>
              <input
                type="text" style={inputStyle} placeholder="Busca tu región…" autoComplete="off"
                value={regionSearch}
                onChange={(e) => {
                  setRegionSearch(e.target.value);
                  if (region && e.target.value !== region) { setRegion(''); setData({ region: null }); }
                  setShowRegionDropdown(true);
                }}
                onFocus={() => setShowRegionDropdown(true)}
              />
              {showRegionDropdown && regionesFiltradas.length > 0 && (
                <div style={dropdownStyle}>
                  {regionesFiltradas.map((r) => (
                    <div
                      key={r.id}
                      style={{ ...dropdownItemStyle, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}
                      onMouseEnter={(ev) => (ev.currentTarget.style.background = 'rgba(255,255,255,0.06)')}
                      onMouseLeave={(ev) => (ev.currentTarget.style.background = 'transparent')}
                      onClick={() => {
                        setRegion(r.nombre);
                        setRegionSearch(r.nombre);
                        setData({ region: r.nombre });
                        setShowRegionDropdown(false);
                      }}
                    >
                      {r.nombre}
                    </div>
                  ))}
                </div>
              )}
              {showRegionDropdown && regionesFiltradas.length === 0 && (
                <div style={{ ...dropdownStyle, padding: '0.75rem 1rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                  No se encontraron regiones
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ── Tipo de cliente ── */}
      <div>
        <div style={sectionHeaderStyle}><span>👤</span> Tipo de Cliente</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
          {TIPO_CLIENTE_OPTIONS.map((tipo) => (
            <button key={tipo} type="button" style={chipStyle(tipoCliente === tipo)} onClick={() => setTipoCliente(tipo)}>
              {tipo}
            </button>
          ))}
        </div>
      </div>

      {/* ── Cliente ── */}
      <div>
        <div style={sectionHeaderStyle}><span>🏢</span> Datos del Cliente</div>
        {!showNuevoCliente ? (
          <div>
            <div ref={clienteRef} style={{ position: 'relative', marginBottom: '0.75rem' }}>
              <label style={labelStyle}>Buscar cliente (nombre o RUC/DNI)</label>
              <div style={{ position: 'relative' }}>
                <input
                  type="text" style={inputStyle} placeholder="Escribe mínimo 2 caracteres..."
                  value={clienteSearch}
                  onChange={(e) => {
                    setClienteSearch(e.target.value);
                    if (clienteSeleccionado && e.target.value !== clienteSeleccionado.nombre) setClienteSeleccionado(null);
                    setShowClienteDropdown(true);
                  }}
                  onFocus={() => clienteSearch.length >= 2 && setShowClienteDropdown(true)}
                  autoComplete="off"
                />
                {loadingCliente && (
                  <span style={{ position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Buscando...
                  </span>
                )}
              </div>
              {showClienteDropdown && clienteResults.length > 0 && (
                <div style={dropdownStyle}>
                  {clienteResults.map((c) => (
                    <div key={c.id} style={dropdownItemStyle}
                      onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(255,255,255,0.06)')}
                      onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                      onClick={() => handleSelectCliente(c)}>
                      <strong>{c.nombre}</strong>
                      {c.documento && <span style={{ color: 'var(--text-secondary)', marginLeft: '0.5rem', fontSize: '0.85rem' }}>{c.documento}</span>}
                      {c.direccion && <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '2px' }}>{c.direccion}</div>}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {clienteSeleccionado && (
              <div style={cardSeleccion}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--primary-color)' }}>✓ {clienteSeleccionado.nombre}</div>
                  {clienteSeleccionado.documento && <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{clienteSeleccionado.documento}</div>}
                  {clienteSeleccionado.direccion && <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>📍 {clienteSeleccionado.direccion}</div>}
                </div>
                <button type="button" onClick={() => { setClienteSeleccionado(null); setClienteSearch(''); }}
                  style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '1.1rem' }}>✕</button>
              </div>
            )}

            <button type="button" onClick={() => setShowNuevoCliente(true)}
              style={{ marginTop: '0.75rem', background: 'none', border: '1px dashed var(--border-color)', borderRadius: '8px', color: 'var(--text-secondary)', cursor: 'pointer', padding: '0.5rem 1rem', fontSize: '0.85rem', width: '100%' }}>
              + No encontré al cliente — Crear nuevo
            </button>
          </div>
        ) : (
          <form onSubmit={handleCrearCliente} style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.85rem' }}>
              <div style={{ gridColumn: '1 / -1' }}>
                <label style={labelStyle}>Nombre / Razón Social *</label>
                <input required type="text" style={inputStyle} value={nuevoCliente.nombre} onChange={(e) => setNuevoCliente({ ...nuevoCliente, nombre: e.target.value })} />
              </div>
              <div>
                <label style={labelStyle}>RUC / DNI</label>
                <input type="text" style={inputStyle} value={nuevoCliente.documento} onChange={(e) => setNuevoCliente({ ...nuevoCliente, documento: e.target.value })} />
              </div>
              <div>
                <label style={labelStyle}>Atención a</label>
                <input type="text" style={inputStyle} value={nuevoCliente.atencion} onChange={(e) => setNuevoCliente({ ...nuevoCliente, atencion: e.target.value })} />
              </div>
              <div style={{ gridColumn: '1 / -1' }}>
                <label style={labelStyle}>Dirección</label>
                <input type="text" style={inputStyle} value={nuevoCliente.direccion} onChange={(e) => setNuevoCliente({ ...nuevoCliente, direccion: e.target.value })} />
              </div>
              <div style={{ gridColumn: '1 / -1' }}>
                <label style={labelStyle}>Referencia</label>
                <input type="text" style={inputStyle} value={nuevoCliente.referencia} onChange={(e) => setNuevoCliente({ ...nuevoCliente, referencia: e.target.value })} />
              </div>
              <div>
                <label style={labelStyle}>Teléfono</label>
                <input type="tel" style={inputStyle} value={nuevoCliente.telefono} onChange={(e) => setNuevoCliente({ ...nuevoCliente, telefono: e.target.value })} />
              </div>
              <div>
                <label style={labelStyle}>Correo</label>
                <input type="email" style={inputStyle} value={nuevoCliente.correo} onChange={(e) => setNuevoCliente({ ...nuevoCliente, correo: e.target.value })} />
              </div>
            </div>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button type="button" onClick={() => setShowNuevoCliente(false)}
                style={{ flex: 1, padding: '0.65rem', background: 'transparent', border: '1px solid var(--border-color)', borderRadius: '8px', color: 'var(--text-secondary)', cursor: 'pointer', fontWeight: 500 }}>
                Cancelar
              </button>
              <button type="submit" disabled={loadingGuardar}
                style={{ flex: 2, padding: '0.65rem', background: 'var(--primary-color)', border: 'none', borderRadius: '8px', color: '#000', cursor: 'pointer', fontWeight: 700 }}>
                {loadingGuardar ? 'Guardando...' : '✓ Crear Cliente'}
              </button>
            </div>
          </form>
        )}
      </div>

      {/* ── Ingeniero ── */}
      <div>
        <div style={sectionHeaderStyle}><span>👷</span> Ingeniero Responsable</div>
        <div ref={ingenieroRef} style={{ position: 'relative' }}>
          <label style={labelStyle}>Seleccionar ingeniero</label>
          <input
            type="text" style={inputStyle}
            placeholder={loadingIngeniero ? 'Cargando ingenieros...' : 'Buscar ingeniero por nombre...'}
            value={ingenieroSearch} disabled={loadingIngeniero}
            onChange={(e) => {
              setIngenieroSearch(e.target.value);
              if (ingenieroSeleccionado && e.target.value !== ingenieroSeleccionado.nombre) setIngenieroSeleccionado(null);
              setShowIngenieroDropdown(true);
            }}
            onFocus={() => setShowIngenieroDropdown(true)} autoComplete="off"
          />
          {showIngenieroDropdown && ingenieroResults.length > 0 && (
            <div style={dropdownStyle}>
              {ingenieroResults.map((i) => (
                <div key={i.id} style={dropdownItemStyle}
                  onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(255,255,255,0.06)')}
                  onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                  onClick={() => handleSelectIngeniero(i)}>
                  <strong>{i.nombre}</strong>
                  {i.telefono && <span style={{ color: 'var(--text-secondary)', marginLeft: '0.5rem', fontSize: '0.85rem' }}>📞 {i.telefono}</span>}
                  {i.correo && <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '2px' }}>✉ {i.correo}</div>}
                </div>
              ))}
            </div>
          )}
          {showIngenieroDropdown && !loadingIngeniero && ingenieroResults.length === 0 && (
            <div style={{ ...dropdownStyle, padding: '0.75rem 1rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              No se encontraron ingenieros
            </div>
          )}
        </div>
        {ingenieroSeleccionado && (
          <div style={cardSeleccion}>
            <div>
              <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--primary-color)' }}>✓ {ingenieroSeleccionado.nombre}</div>
              {ingenieroSeleccionado.telefono && <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>📞 {ingenieroSeleccionado.telefono}</div>}
            </div>
            <button type="button" onClick={() => { setIngenieroSeleccionado(null); setIngenieroSearch(''); }}
              style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '1.1rem' }}>✕</button>
          </div>
        )}
      </div>

      {error && (
        <div style={{ background: 'rgba(220,50,50,0.12)', border: '1px solid rgba(220,50,50,0.4)', borderRadius: '8px', padding: '0.75rem 1rem', color: '#ff6b6b', fontSize: '0.9rem' }}>
          ⚠️ {error}
        </div>
      )}

      <button type="button" onClick={handleContinuar}
        style={{ width: '100%', padding: '0.9rem', background: 'var(--primary-color)', border: 'none', borderRadius: '10px', color: '#000', fontSize: '1rem', fontWeight: 700, cursor: 'pointer', marginTop: '0.5rem' }}>
        Continuar → Tipo de Sistema
      </button>
    </div>
  );
}
