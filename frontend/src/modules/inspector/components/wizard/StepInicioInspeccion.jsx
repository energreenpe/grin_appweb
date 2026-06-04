import React, { useState, useEffect, useRef } from 'react';
import { useWizardStore } from '../../store/wizardStore';
import { inspectorApi } from '../../api/inspectorApi';

const TIPO_CLIENTE_OPTIONS = ['Persona', 'Empresa'];

export default function StepInicioInspeccion({ onNext }) {
  const { data, setData } = useWizardStore();

  // ─── Estado local ───────────────────────────────────────────────
  const [tipoCliente, setTipoCliente] = useState(data.tipo_cliente || '');

  // Cliente
  const [clienteSearch, setClienteSearch] = useState(data.cliente_info?.nombre || '');
  const [clienteResults, setClienteResults] = useState([]);
  const [clienteSeleccionado, setClienteSeleccionado] = useState(data.cliente_info || null);
  const [showClienteDropdown, setShowClienteDropdown] = useState(false);
  const [showNuevoCliente, setShowNuevoCliente] = useState(false);
  const [loadingCliente, setLoadingCliente] = useState(false);
  const [nuevoCliente, setNuevoCliente] = useState({
    nombre: '', documento: '', direccion: '', atencion: '',
    referencia: '', correo: '', telefono: ''
  });

  // Técnico
  const [tecnicoSearch, setTecnicoSearch] = useState(data.tecnico_info?.nombre || '');
  const [tecnicoResults, setTecnicoResults] = useState([]);
  const [tecnicoSeleccionado, setTecnicoSeleccionado] = useState(data.tecnico_info || null);
  const [allTecnicos, setAllTecnicos] = useState([]);
  const [showTecnicoDropdown, setShowTecnicoDropdown] = useState(false);
  const [loadingTecnico, setLoadingTecnico] = useState(false);

  const [loadingGuardar, setLoadingGuardar] = useState(false);
  const [error, setError] = useState('');

  const clienteRef = useRef(null);
  const tecnicoRef = useRef(null);

  // ─── Cargar técnicos al montar ────────────────────────────────────
  useEffect(() => {
    const fetchTecnicos = async () => {
      try {
        setLoadingTecnico(true);
        const res = await inspectorApi.getTecnicos();
        setAllTecnicos(res);
      } catch (e) {
        console.error('Error cargando técnicos', e);
      } finally {
        setLoadingTecnico(false);
      }
    };
    fetchTecnicos();
  }, []);

  // ─── Cerrar dropdowns al hacer clic fuera ─────────────────────────
  useEffect(() => {
    const handler = (e) => {
      if (clienteRef.current && !clienteRef.current.contains(e.target))
        setShowClienteDropdown(false);
      if (tecnicoRef.current && !tecnicoRef.current.contains(e.target))
        setShowTecnicoDropdown(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // ─── Búsqueda de clientes con debounce ────────────────────────────
  useEffect(() => {
    if (clienteSearch.length < 2) { setClienteResults([]); return; }
    const t = setTimeout(async () => {
      setLoadingCliente(true);
      try {
        const res = await inspectorApi.searchClientes(clienteSearch);
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

  // ─── Filtro de técnicos en tiempo real ───────────────────────────
  useEffect(() => {
    if (!tecnicoSearch) {
      setTecnicoResults(allTecnicos);
    } else {
      setTecnicoResults(
        allTecnicos.filter(t =>
          t.nombre.toLowerCase().includes(tecnicoSearch.toLowerCase())
        )
      );
    }
  }, [tecnicoSearch, allTecnicos]);

  // ─── Handlers clientes ───────────────────────────────────────────
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
      const created = await inspectorApi.createCliente(nuevoCliente);
      handleSelectCliente(created);
      setShowNuevoCliente(false);
    } catch (err) {
      setError('Error al crear el cliente. Intenta nuevamente.');
    } finally {
      setLoadingGuardar(false);
    }
  };

  // ─── Handlers técnicos ───────────────────────────────────────────
  const handleSelectTecnico = (t) => {
    setTecnicoSeleccionado(t);
    setTecnicoSearch(t.nombre);
    setShowTecnicoDropdown(false);
    setData({ tecnico_id: t.id, tecnico_info: t });
  };

  // ─── Avanzar ─────────────────────────────────────────────────────
  const handleContinuar = () => {
    setError('');
    if (!tipoCliente) { setError('Selecciona el tipo de cliente.'); return; }
    if (!clienteSeleccionado) { setError('Debes seleccionar o crear un cliente.'); return; }
    if (!tecnicoSeleccionado) { setError('Debes seleccionar el técnico responsable.'); return; }
    const newData = {
      ...data,
      tipo_cliente: tipoCliente,
      cliente_id: clienteSeleccionado.id,
      cliente_info: clienteSeleccionado,
      tecnico_id: tecnicoSeleccionado.id,
      tecnico_info: tecnicoSeleccionado,
    };
    setData(newData);
    onNext(newData);
  };

  // ─── Estilos compartidos ─────────────────────────────────────────
  const inputStyle = {
    width: '100%',
    padding: '0.65rem 0.9rem',
    background: 'var(--input-bg, rgba(255,255,255,0.07))',
    border: '1px solid var(--border-color)',
    borderRadius: '8px',
    color: 'var(--text-primary)',
    fontSize: '0.95rem',
    boxSizing: 'border-box',
    outline: 'none',
  };

  const labelStyle = {
    display: 'block',
    fontSize: '0.8rem',
    fontWeight: 600,
    color: 'var(--text-secondary)',
    marginBottom: '0.4rem',
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
  };

  const dropdownStyle = {
    position: 'absolute',
    top: '100%',
    left: 0,
    right: 0,
    background: 'var(--card-bg, #1e1e2e)',
    border: '1px solid var(--border-color)',
    borderRadius: '8px',
    boxShadow: '0 8px 24px rgba(0,0,0,0.35)',
    zIndex: 100,
    maxHeight: '220px',
    overflowY: 'auto',
    marginTop: '4px',
  };

  const dropdownItemStyle = {
    padding: '0.7rem 1rem',
    cursor: 'pointer',
    borderBottom: '1px solid var(--border-color)',
    fontSize: '0.9rem',
    transition: 'background 0.15s',
  };

  const sectionHeaderStyle = {
    fontSize: '1rem',
    fontWeight: 700,
    color: 'var(--primary-color, #62B989)',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    marginBottom: '1rem',
    paddingBottom: '0.5rem',
    borderBottom: '1px solid var(--border-color)',
  };

  const chipStyle = (selected) => ({
    padding: '0.55rem 1.1rem',
    borderRadius: '30px',
    border: selected ? '2px solid var(--primary-color, #62B989)' : '1px solid var(--border-color)',
    background: selected ? 'rgba(98,185,137,0.18)' : 'transparent',
    color: selected ? 'var(--primary-color, #62B989)' : 'var(--text-secondary)',
    cursor: 'pointer',
    fontWeight: selected ? 700 : 400,
    fontSize: '0.9rem',
    transition: 'all 0.2s',
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <div style={{ textAlign: 'center' }}>
        <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '0.3rem' }}>
          Nueva Inspección Técnica
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          Completa los datos del cliente y el técnico asignado
        </p>
      </div>

      {/* ── 1. TIPO DE CLIENTE ───────────────────────────────────── */}
      <div>
        <div style={sectionHeaderStyle}>
          <span>👤</span> Tipo de Cliente
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
          {TIPO_CLIENTE_OPTIONS.map(tipo => (
            <button
              key={tipo}
              type="button"
              style={chipStyle(tipoCliente === tipo)}
              onClick={() => setTipoCliente(tipo)}
            >
              {tipo}
            </button>
          ))}
        </div>
      </div>

      {/* ── 2. CLIENTE ──────────────────────────────────────────── */}
      <div>
        <div style={sectionHeaderStyle}>
          <span>🏢</span> Datos del Cliente
        </div>

        {/* Buscador con autocomplete */}
        {!showNuevoCliente ? (
          <div>
            <div ref={clienteRef} style={{ position: 'relative', marginBottom: '0.75rem' }}>
              <label style={labelStyle}>Buscar cliente (nombre o RUC/DNI)</label>
              <div style={{ position: 'relative' }}>
                <input
                  id="cliente-search-input"
                  type="text"
                  style={inputStyle}
                  placeholder="Escribe mínimo 2 caracteres..."
                  value={clienteSearch}
                  onChange={(e) => {
                    setClienteSearch(e.target.value);
                    if (clienteSeleccionado && e.target.value !== clienteSeleccionado.nombre) {
                      setClienteSeleccionado(null);
                    }
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
                  {clienteResults.map(c => (
                    <div
                      key={c.id}
                      style={dropdownItemStyle}
                      onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.06)'}
                      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                      onClick={() => handleSelectCliente(c)}
                    >
                      <strong>{c.nombre}</strong>
                      {c.documento && <span style={{ color: 'var(--text-secondary)', marginLeft: '0.5rem', fontSize: '0.85rem' }}>{c.documento}</span>}
                      {c.direccion && <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '2px' }}>{c.direccion}</div>}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Card del cliente seleccionado */}
            {clienteSeleccionado && (
              <div style={{
                background: 'rgba(98,185,137,0.08)',
                border: '1px solid rgba(98,185,137,0.3)',
                borderRadius: '10px',
                padding: '0.9rem 1rem',
                display: 'flex',
                alignItems: 'flex-start',
                justifyContent: 'space-between',
                gap: '0.5rem',
                marginBottom: '0.75rem',
              }}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--primary-color, #62B989)' }}>
                    ✓ {clienteSeleccionado.nombre}
                  </div>
                  {clienteSeleccionado.documento && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      {clienteSeleccionado.documento}
                    </div>
                  )}
                  {clienteSeleccionado.direccion && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      📍 {clienteSeleccionado.direccion}
                    </div>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => { setClienteSeleccionado(null); setClienteSearch(''); }}
                  style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '1.1rem', padding: '0' }}
                >
                  ✕
                </button>
              </div>
            )}

            <button
              type="button"
              onClick={() => setShowNuevoCliente(true)}
              style={{ background: 'none', border: '1px dashed var(--border-color)', borderRadius: '8px', color: 'var(--text-secondary)', cursor: 'pointer', padding: '0.5rem 1rem', fontSize: '0.85rem', width: '100%' }}
            >
              + No encontré al cliente — Crear nuevo
            </button>
          </div>
        ) : (
          /* ── Formulario Nuevo Cliente ── */
          <form onSubmit={handleCrearCliente} style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.85rem' }}>
              <div style={{ gridColumn: '1 / -1' }}>
                <label style={labelStyle}>Nombre / Razón Social *</label>
                <input
                  required
                  type="text"
                  style={inputStyle}
                  placeholder="Nombre completo o razón social"
                  value={nuevoCliente.nombre}
                  onChange={e => setNuevoCliente({ ...nuevoCliente, nombre: e.target.value })}
                />
              </div>
              <div>
                <label style={labelStyle}>RUC / DNI</label>
                <input
                  type="text"
                  style={inputStyle}
                  placeholder="Número de documento"
                  value={nuevoCliente.documento}
                  onChange={e => setNuevoCliente({ ...nuevoCliente, documento: e.target.value })}
                />
              </div>
              <div>
                <label style={labelStyle}>Atención a</label>
                <input
                  type="text"
                  style={inputStyle}
                  placeholder="Persona de contacto"
                  value={nuevoCliente.atencion}
                  onChange={e => setNuevoCliente({ ...nuevoCliente, atencion: e.target.value })}
                />
              </div>
              <div style={{ gridColumn: '1 / -1' }}>
                <label style={labelStyle}>Dirección</label>
                <input
                  type="text"
                  style={inputStyle}
                  placeholder="Dirección completa"
                  value={nuevoCliente.direccion}
                  onChange={e => setNuevoCliente({ ...nuevoCliente, direccion: e.target.value })}
                />
              </div>
              <div style={{ gridColumn: '1 / -1' }}>
                <label style={labelStyle}>Referencia</label>
                <input
                  type="text"
                  style={inputStyle}
                  placeholder="Referencia de ubicación (ej: frente al parque)"
                  value={nuevoCliente.referencia}
                  onChange={e => setNuevoCliente({ ...nuevoCliente, referencia: e.target.value })}
                />
              </div>
              <div>
                <label style={labelStyle}>Teléfono</label>
                <input
                  type="tel"
                  style={inputStyle}
                  placeholder="Teléfono de contacto"
                  value={nuevoCliente.telefono}
                  onChange={e => setNuevoCliente({ ...nuevoCliente, telefono: e.target.value })}
                />
              </div>
              <div>
                <label style={labelStyle}>Correo</label>
                <input
                  type="email"
                  style={inputStyle}
                  placeholder="correo@email.com"
                  value={nuevoCliente.correo}
                  onChange={e => setNuevoCliente({ ...nuevoCliente, correo: e.target.value })}
                />
              </div>
            </div>
            <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.25rem' }}>
              <button
                type="button"
                onClick={() => setShowNuevoCliente(false)}
                style={{ flex: 1, padding: '0.65rem', background: 'transparent', border: '1px solid var(--border-color)', borderRadius: '8px', color: 'var(--text-secondary)', cursor: 'pointer', fontWeight: 500 }}
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={loadingGuardar}
                style={{ flex: 2, padding: '0.65rem', background: 'var(--primary-color, #62B989)', border: 'none', borderRadius: '8px', color: '#fff', cursor: 'pointer', fontWeight: 700, fontSize: '0.95rem' }}
              >
                {loadingGuardar ? 'Guardando...' : '✓ Guardar Cliente'}
              </button>
            </div>
          </form>
        )}
      </div>

      {/* ── 3. TÉCNICO ──────────────────────────────────────────── */}
      <div>
        <div style={sectionHeaderStyle}>
          <span>🔧</span> Técnico Responsable
        </div>

        <div ref={tecnicoRef} style={{ position: 'relative' }}>
          <label style={labelStyle}>Seleccionar técnico</label>
          <input
            id="tecnico-search-input"
            type="text"
            style={inputStyle}
            placeholder={loadingTecnico ? 'Cargando técnicos...' : 'Buscar técnico por nombre...'}
            value={tecnicoSearch}
            disabled={loadingTecnico}
            onChange={(e) => {
              setTecnicoSearch(e.target.value);
              if (tecnicoSeleccionado && e.target.value !== tecnicoSeleccionado.nombre)
                setTecnicoSeleccionado(null);
              setShowTecnicoDropdown(true);
            }}
            onFocus={() => setShowTecnicoDropdown(true)}
            autoComplete="off"
          />

          {showTecnicoDropdown && tecnicoResults.length > 0 && (
            <div style={dropdownStyle}>
              {tecnicoResults.map(t => (
                <div
                  key={t.id}
                  style={dropdownItemStyle}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.06)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                  onClick={() => handleSelectTecnico(t)}
                >
                  <strong>{t.nombre}</strong>
                  {t.telefono && <span style={{ color: 'var(--text-secondary)', marginLeft: '0.5rem', fontSize: '0.85rem' }}>📞 {t.telefono}</span>}
                  {t.correo && <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '2px' }}>✉ {t.correo}</div>}
                </div>
              ))}
            </div>
          )}

          {showTecnicoDropdown && !loadingTecnico && tecnicoResults.length === 0 && (
            <div style={{ ...dropdownStyle, padding: '0.75rem 1rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              No se encontraron técnicos
            </div>
          )}
        </div>

        {/* Card del técnico seleccionado */}
        {tecnicoSeleccionado && (
          <div style={{
            background: 'rgba(98,185,137,0.08)',
            border: '1px solid rgba(98,185,137,0.3)',
            borderRadius: '10px',
            padding: '0.9rem 1rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginTop: '0.75rem',
          }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--primary-color, #62B989)' }}>
                ✓ {tecnicoSeleccionado.nombre}
              </div>
              {tecnicoSeleccionado.telefono && (
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  📞 {tecnicoSeleccionado.telefono}
                </div>
              )}
            </div>
            <button
              type="button"
              onClick={() => { setTecnicoSeleccionado(null); setTecnicoSearch(''); }}
              style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '1.1rem', padding: '0' }}
            >
              ✕
            </button>
          </div>
        )}
      </div>

      {/* ── ERROR ── */}
      {error && (
        <div style={{ background: 'rgba(220,50,50,0.12)', border: '1px solid rgba(220,50,50,0.4)', borderRadius: '8px', padding: '0.75rem 1rem', color: '#ff6b6b', fontSize: '0.9rem' }}>
          ⚠️ {error}
        </div>
      )}

      {/* ── BOTÓN CONTINUAR ── */}
      <button
        id="btn-continuar-inicio"
        type="button"
        onClick={handleContinuar}
        style={{
          width: '100%',
          padding: '0.9rem',
          background: 'var(--primary-color, #62B989)',
          border: 'none',
          borderRadius: '10px',
          color: '#fff',
          fontSize: '1rem',
          fontWeight: 700,
          cursor: 'pointer',
          transition: 'opacity 0.2s',
          marginTop: '0.5rem',
        }}
        onMouseEnter={e => e.currentTarget.style.opacity = '0.88'}
        onMouseLeave={e => e.currentTarget.style.opacity = '1'}
      >
        Continuar → Tipo de Sistema
      </button>
    </div>
  );
}
