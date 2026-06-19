import React, { useState, useRef, useEffect } from 'react';

/**
 * Select buscable reutilizable (capa compartida del frontend).
 * Mismo diseño que los dropdowns del módulo MATH: input + lista filtrable, solo
 * scroll vertical, se cierra al tocar fuera. Funciona en escritorio y móvil
 * (no usa el <select> nativo). Usado por quote e inspector desde aquí.
 *
 * props:
 *  - options: [{ value, label }]   (label es lo que se muestra/filtra; conserva todos los datos)
 *  - value: valor actual
 *  - onChange: (value) => void
 *  - placeholder, disabled, style (estilo del contenedor)
 */
export default function SearchableSelect({ options = [], value, onChange, placeholder = 'Selecciona…', disabled = false, style }) {
  const [search, setSearch] = useState('');
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  const selected = options.find((o) => String(o.value) === String(value)) || null;

  // Sincroniza el texto mostrado con la opción seleccionada, pero NUNCA mientras el
  // dropdown está abierto (para no pisar lo que el usuario está escribiendo).
  useEffect(() => {
    if (!open) setSearch(selected ? selected.label : '');
  }, [value, options, open, selected]);

  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const filtered = (search.trim() && (!selected || search !== selected.label))
    ? options.filter((o) => o.label.toLowerCase().includes(search.trim().toLowerCase()))
    : options;

  const inputStyle = {
    width: '100%', padding: '0.5rem 0.75rem', background: 'var(--surface-color)',
    border: '1px solid var(--border-color)', borderRadius: 'var(--radius)', color: 'var(--text-primary)',
    fontFamily: 'inherit', fontSize: '0.95rem', boxSizing: 'border-box', outline: 'none',
    cursor: disabled ? 'not-allowed' : 'text', opacity: disabled ? 0.6 : 1,
  };
  const dropdownStyle = {
    position: 'absolute', top: '100%', left: 0, right: 0, background: 'var(--surface-color)',
    border: '1px solid var(--border-color)', borderRadius: 'var(--radius)', boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
    zIndex: 100, maxHeight: '240px', overflowX: 'hidden', overflowY: 'auto', marginTop: '4px',
  };
  const itemStyle = {
    padding: '0.6rem 0.8rem', cursor: 'pointer', borderBottom: '1px solid var(--border-color)',
    fontSize: '0.9rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
  };

  return (
    <div ref={ref} style={{ position: 'relative', zIndex: open ? 20 : 'auto', ...style }}>
      <input
        type="text" style={inputStyle} placeholder={placeholder} autoComplete="off" disabled={disabled}
        value={search}
        onChange={(e) => { setSearch(e.target.value); setOpen(true); }}
        onFocus={(e) => { if (!disabled) { setOpen(true); e.target.select(); } }}
      />
      {open && !disabled && filtered.length > 0 && (
        <div style={dropdownStyle}>
          {filtered.map((o) => (
            <div
              key={String(o.value)} style={itemStyle} title={o.label}
              onMouseEnter={(ev) => (ev.currentTarget.style.background = 'rgba(255,255,255,0.06)')}
              onMouseLeave={(ev) => (ev.currentTarget.style.background = 'transparent')}
              onClick={() => { onChange(o.value); setOpen(false); }}
            >
              {o.label}
            </div>
          ))}
        </div>
      )}
      {open && !disabled && filtered.length === 0 && (
        <div style={{ ...dropdownStyle, padding: '0.75rem 1rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          Sin resultados
        </div>
      )}
    </div>
  );
}
